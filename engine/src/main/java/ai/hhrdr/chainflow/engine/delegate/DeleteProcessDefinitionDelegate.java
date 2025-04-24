package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RepositoryService;
import org.camunda.bpm.engine.repository.ProcessDefinition;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class DeleteProcessDefinitionDelegate implements JavaDelegate {

    @Autowired
    private RepositoryService repositoryService;

    @Override
    public void execute(DelegateExecution execution) throws Exception {

        // 1. Read the process definition key from the process variable 'form_definitionKey'
        String definitionKey = (String) execution.getVariable("form_definitionKey");

        if (definitionKey == null || definitionKey.isEmpty()) {
            throw new IllegalArgumentException("No process definition key found in variable 'form_definitionKey'.");
        }

        // 2. Query all process definitions matching the provided key
        List<ProcessDefinition> definitions = repositoryService
                .createProcessDefinitionQuery()
                .processDefinitionKey(definitionKey)
                .list();

        // 3. If no definitions found, optionally log or throw an exception
        if (definitions.isEmpty()) {
            System.out.println("No process definitions found with key: " + definitionKey);
            return;
        }

        // 4. Delete each matching process definition
        //    The second parameter to deleteProcessDefinition() can be `true` for cascade delete
        //    which also removes running process instances of this definition.
        for (ProcessDefinition definition : definitions) {
            repositoryService.deleteProcessDefinition(definition.getId(), true);
            System.out.println("Deleted process definition: " + definition.getId());
        }
    }
}
