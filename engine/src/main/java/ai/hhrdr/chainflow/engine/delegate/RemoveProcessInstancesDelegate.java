package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.runtime.ProcessInstance;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class RemoveProcessInstancesDelegate implements JavaDelegate {

    @Autowired
    private RuntimeService runtimeService;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // 1. Retrieve definitionId / definitionKey from variables
        // -------------------------------------------------------------------------
        String definitionId  = (String) execution.getVariable("form_definitionID");
        String definitionKey = (String) execution.getVariable("form_definitionKey");

        // 2. Create a process instance query
        // -------------------------------------------------------------------------
        List<ProcessInstance> instances;

        boolean hasDefinitionId  = definitionId  != null && !definitionId.trim().isEmpty();
        boolean hasDefinitionKey = definitionKey != null && !definitionKey.trim().isEmpty();

        if (!hasDefinitionId && !hasDefinitionKey) {
            // If neither is provided, remove *all* process instances (USE WITH CAUTION!)
            instances = runtimeService.createProcessInstanceQuery().list();
        } else if (hasDefinitionKey) {
            // If definitionKey is provided, remove all that match
            instances = runtimeService
                    .createProcessInstanceQuery()
                    .processDefinitionKey(definitionKey)
                    .list();
        } else {
            // Otherwise, use definitionId
            instances = runtimeService
                    .createProcessInstanceQuery()
                    .processDefinitionId(definitionId)
                    .list();
        }

        if (instances == null || instances.isEmpty()) {
            System.out.println("[INFO] No matching process instances found.");
            return;
        }

        // 4. Delete each process instance
        // -------------------------------------------------------------------------
        for (ProcessInstance instance : instances) {
            // You can also supply a reason string to track why they were deleted
            runtimeService.deleteProcessInstance(
                    instance.getId(),
                    "Removed by RemoveProcessInstancesDelegate"
            );

            System.out.println("[INFO] Deleted process instance: " + instance.getId());
        }
    }
}
