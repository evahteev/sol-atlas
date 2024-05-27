package ai.hhrdr.chainflow.engine.config;

import org.camunda.bpm.engine.impl.history.event.HistoryEvent;
import org.camunda.bpm.engine.impl.history.handler.HistoryEventHandler;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@Primary
public class CompositeHistoryEventHandler implements HistoryEventHandler {

    private final List<HistoryEventHandler> handlers;

    @Autowired
    public CompositeHistoryEventHandler(List<HistoryEventHandler> handlers) {
        this.handlers = handlers;
    }

    @Override
    public void handleEvent(HistoryEvent historyEvent) {
        for (HistoryEventHandler handler : handlers) {
            handler.handleEvent(historyEvent);
        }
    }

    @Override
    public void handleEvents(List<HistoryEvent> historyEvents) {
        for (HistoryEventHandler handler : handlers) {
            handler.handleEvents(historyEvents);
        }
    }
}

