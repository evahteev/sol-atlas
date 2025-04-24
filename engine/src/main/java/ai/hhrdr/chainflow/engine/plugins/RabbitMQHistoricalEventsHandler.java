package ai.hhrdr.chainflow.engine.plugins;

import ai.hhrdr.chainflow.engine.service.RabbitMQSender;
import org.camunda.bpm.engine.HistoryService;
import org.camunda.bpm.engine.history.HistoricProcessInstance;
import org.camunda.bpm.engine.history.HistoricVariableInstance;
import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.camunda.bpm.engine.impl.history.handler.HistoryEventHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class RabbitMQHistoricalEventsHandler implements HistoryEventHandler {

    private static final Logger LOG = LoggerFactory.getLogger(RabbitMQHistoricalEventsHandler.class);

    @Autowired
    private RabbitMQSender rabbitMQSender;

    @Autowired
    @Lazy
    private HistoryService historyService;
    // Needs lazy; otherwise circular dependency is triggered

    @Override
    public void handleEvent(HistoryEvent historyEvent) {
        if (historyEvent == null) {
            LOG.warn("Received null history event");
            return;
        }

        String processInstanceId = historyEvent.getProcessInstanceId();
        String startUserId = null;
        if (processInstanceId != null) {
            HistoricProcessInstance processInstance = historyService.createHistoricProcessInstanceQuery()
                    .processInstanceId(processInstanceId)
                    .singleResult();
            if (processInstance != null) {
                startUserId = processInstance.getStartUserId();
            } else {
                LOG.warn("No historic process instance found for id: {}", processInstanceId);
            }
        } else {
            LOG.warn("History event has a null processInstanceId.");
        }

        // Attempt to retrieve the 'callingProcessInstanceId' if processInstanceId is available
        String callingProcessInstanceId = null;
        if (processInstanceId != null) {
            HistoricVariableInstance callingVar = historyService.createHistoricVariableInstanceQuery()
                    .processInstanceId(processInstanceId)
                    .variableName("callingProcessInstanceId")
                    .singleResult();
            if (callingVar != null && callingVar.getValue() != null) {
                callingProcessInstanceId = callingVar.getValue().toString();
            }
        }

        // If we still haven't resolved it, fall back to using the event's rootProcessInstanceId
        if (callingProcessInstanceId == null && historyEvent.getRootProcessInstanceId() != null) {
            callingProcessInstanceId = historyEvent.getRootProcessInstanceId();
        }

        // Log what we were able to resolve
        LOG.debug("Resolved startUserId: {} and callingProcessInstanceId: {}", startUserId, callingProcessInstanceId);

        // Send the history event along with the user id and the resolved calling process instance id (which may be null)
        rabbitMQSender.send(historyEvent, historyEvent.getClass().getSimpleName(), startUserId, callingProcessInstanceId);
    }

    @Override
    public void handleEvents(List<HistoryEvent> historyEvents) {
        for (HistoryEvent historyEvent : historyEvents) {
            handleEvent(historyEvent);
        }
    }
}
