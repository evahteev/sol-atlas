package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;

public class ProcessInstanceDeduplicationFlagDelegate implements JavaDelegate {

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve RuntimeService from the process engine
        RuntimeService runtimeService = execution.getProcessEngineServices().getRuntimeService();

        // Typically the processDefinitionId looks like "<processDefKey>:<version>:<dbId>".
        // We just want the process definition key itself, so we split on ":".
        String processDefinitionKey = execution.getProcessDefinitionId().split(":")[0];
        String businessKey = execution.getBusinessKey();

        // Count how many active instances share the same definition key & business key.
        long count = runtimeService.createProcessInstanceQuery()
                .processDefinitionKey(processDefinitionKey)
                .processInstanceBusinessKey(businessKey)
                .active()
                .count();

        // If more than one active instance exists with the same definition key & business key,
        // it is considered a duplicate.
        boolean isDuplicate = (count > 1);

        // Set the "isDuplicate" variable in the process context
        execution.setVariable("isDuplicate", isDuplicate);
    }
}
