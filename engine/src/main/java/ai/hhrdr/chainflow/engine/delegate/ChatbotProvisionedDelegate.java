package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.engine.impl.persistence.entity.ExecutionEntity;
import org.springframework.stereotype.Component;

@Component("chatbotProvisionedDelegate")
public class ChatbotProvisionedDelegate implements JavaDelegate {

    @Override
    public void execute(DelegateExecution execution) throws Exception {

        // Get reference to the runtime service:
        RuntimeService runtimeService = execution.getProcessEngineServices().getRuntimeService();

        // Retrieve relevant process variables:

        ExecutionEntity executionEntity = (ExecutionEntity) execution;
        String rootProcessInstanceId = executionEntity.getRootProcessInstanceId();

        // Perform the message correlation with variables:
        runtimeService
                .createMessageCorrelation("CHATBOT_PROVISIONED")
                .processInstanceId(rootProcessInstanceId)   // <-- correlate by root process instance ID with agent
                .correlate();
    }
}
