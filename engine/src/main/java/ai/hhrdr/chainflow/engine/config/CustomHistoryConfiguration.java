package ai.hhrdr.chainflow.engine.config;

import org.camunda.bpm.engine.spring.SpringProcessEngineConfiguration;
import org.camunda.bpm.spring.boot.starter.configuration.Ordering;
import org.camunda.bpm.spring.boot.starter.configuration.impl.DefaultHistoryConfiguration;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

//@Component
@Order(Ordering.DEFAULT_ORDER + 1)
public class CustomHistoryConfiguration extends DefaultHistoryConfiguration {

    private final CompositeHistoryEventHandler compositeHistoryEventHandler;

    @Autowired
    public CustomHistoryConfiguration(CompositeHistoryEventHandler compositeHistoryEventHandler) {
        this.compositeHistoryEventHandler = compositeHistoryEventHandler;
    }

    @Override
    public void preInit(SpringProcessEngineConfiguration configuration) {
        super.preInit(configuration);
        configuration.getCustomHistoryEventHandlers().add(compositeHistoryEventHandler);
    }
}