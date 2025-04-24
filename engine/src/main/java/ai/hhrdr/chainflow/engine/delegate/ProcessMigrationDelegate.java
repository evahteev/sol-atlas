package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.migration.MigrationPlan;
import org.camunda.bpm.engine.runtime.ProcessInstanceQuery;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class ProcessMigrationDelegate implements JavaDelegate {

    @Autowired
    private RuntimeService runtimeService;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // 1. Retrieve the source and target process definition IDs (e.g., from process variables)
        String sourceDefinitionId = (String) execution.getVariable("form_sourceProcessDefinitionID");
        String targetDefinitionId = (String) execution.getVariable("form_targetProcessDefinitionID");

        if (sourceDefinitionId == null || sourceDefinitionId.isEmpty()) {
            throw new IllegalArgumentException("No source process definition ID provided in variable 'source_process_definition_id'.");
        }
        if (targetDefinitionId == null || targetDefinitionId.isEmpty()) {
            throw new IllegalArgumentException("No target process definition ID provided in variable 'target_process_definition_id'.");
        }

        // 2. Create a migration plan
        //    For a simple approach, you can use .mapEqualActivities() to automatically map user tasks or
        //    other activities that have identical IDs in source & target definitions.
        //    Or add custom instructions for each activity mapping.
        MigrationPlan migrationPlan = runtimeService
                .createMigrationPlan(sourceDefinitionId, targetDefinitionId)
                .mapEqualActivities()  // Or create custom mappings
                .build();

        // 3. Create a process instance query for all instances with the source definition ID
        ProcessInstanceQuery processInstanceQuery = runtimeService
                .createProcessInstanceQuery()
                .processDefinitionId(sourceDefinitionId);

        // 4. Execute the migration asynchronously (recommended for large volumes)
        runtimeService.newMigration(migrationPlan)
                .processInstanceQuery(processInstanceQuery)
                // Optionally skip custom listeners or IoMappings if you want:
                // .skipCustomListeners(true)
                // .skipIoMappings(true)
                .executeAsync();

        // (Optional) set a result variable or log output
        System.out.println("[INFO] Migration started from "
                + sourceDefinitionId + " to " + targetDefinitionId);
    }
}
