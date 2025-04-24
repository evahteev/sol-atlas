package ai.hhrdr.chainflow.engine.service;

import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.core.MessagePostProcessor;
import org.springframework.amqp.core.MessageProperties;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.rabbit.core.RabbitAdmin;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.HashMap;
import java.util.Map;

@Service
public class RabbitMQSender {

    private final RabbitTemplate rabbitTemplate;
    private final RabbitAdmin rabbitAdmin;
    private final String baseExchange;
    private final String routingkey;
    private final Boolean enabled;
    private static final Logger LOG = LoggerFactory.getLogger(RabbitMQSender.class);

    public RabbitMQSender(RabbitTemplate rabbitTemplate,
                          @Value("${engine.rabbitmq.exchange}") String baseExchange,
                          @Value("${engine.rabbitmq.routingkey}") String routingkey,
                          @Value("${spring.rabbitmq.enabled}") Boolean enabled) {
        this.rabbitTemplate = rabbitTemplate;
        this.baseExchange = baseExchange;
        this.routingkey = routingkey;
        this.enabled = enabled;
        this.rabbitAdmin = new RabbitAdmin(rabbitTemplate.getConnectionFactory());
    }

    public void send(HistoryEvent event, String camundaEventType, String startUserId, String callingProcessInstanceId) {
        if (enabled) {
            String exchangeName = baseExchange + "." + camundaEventType;

            TopicExchange exchangeTopic = new TopicExchange(exchangeName);
            rabbitAdmin.declareExchange(exchangeTopic);  // This is idempotent; no issues if it already exists.

            Map<String, Object> messageBody = convertEventToMap(event, startUserId, callingProcessInstanceId);

            MessagePostProcessor messagePostProcessor = message -> {
                MessageProperties props = message.getMessageProperties();
                props.setHeader("startUserId", startUserId);
                props.setHeader("callingProcessInstanceId", callingProcessInstanceId);
                return message;
            };

            rabbitTemplate.convertAndSend(exchangeName, routingkey, messageBody, messagePostProcessor);
            rabbitTemplate.convertAndSend(baseExchange, routingkey, messageBody, messagePostProcessor);
            LOG.debug("Send, eventType = {} camundaUserId = {} msg = {}", camundaEventType, startUserId, event);
        } else {
            LOG.debug("Event skipped, rabbit disabled, eventType = {} msg = {}", camundaEventType, event);
        }
    }

    private Map<String, Object> convertEventToMap(HistoryEvent event, String startUserId, String callingProcessInstanceId) {
        Map<String, Object> result = new HashMap<>();

        // Walk up the class hierarchy so we capture fields from HistoryEvent and its parents
        Class<?> currentClass = event.getClass();
        while (currentClass != null && currentClass != Object.class) {

            Field[] fields = currentClass.getDeclaredFields();
            for (Field field : fields) {
                // Skip static fields
                if (Modifier.isStatic(field.getModifiers())) {
                    continue;
                }
                field.setAccessible(true);
                try {
                    // Field name -> Field value
                    Object value = field.get(event);
                    result.put(field.getName(), value);
                } catch (IllegalAccessException e) {
                    // Decide how you'd like to handle this
                }
            }
            // Move up to the parent class
            currentClass = currentClass.getSuperclass();
        }

        // Add your custom property
        result.put("camundaUserId", startUserId);
        result.put("rootProcessInstanceId", callingProcessInstanceId);

        return result;
    }

}
