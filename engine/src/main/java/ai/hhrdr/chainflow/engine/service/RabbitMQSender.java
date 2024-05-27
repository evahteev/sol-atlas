package ai.hhrdr.chainflow.engine.service;

import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.amqp.core.AmqpTemplate;


@Service
public class RabbitMQSender {

    @Autowired
    private AmqpTemplate rabbitTemplate;

    @Value("${engine.rabbitmq.exchange}")
    private String exchange;

    @Value("${engine.rabbitmq.routingkey}")
    private String routingkey;

    @Value("${spring.rabbitmq.enabled}")
    private Boolean enabled;


    private static final Logger LOG = LoggerFactory.getLogger(RabbitMQSender.class);

    public void send(HistoryEvent event, String camundaEventType) {
        if (enabled) {
            rabbitTemplate.convertAndSend(exchange, routingkey , event);
            LOG.debug("Send, eventType = " + camundaEventType + " msg = " + event);
        } else {
            LOG.info("Event skipped, rabbit disabled, eventType = " + camundaEventType + " msg = " + event);
        }



    }
}
