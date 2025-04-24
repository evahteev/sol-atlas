package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.model.bpmn.instance.camunda.CamundaProperties;
import org.camunda.bpm.model.bpmn.instance.camunda.CamundaProperty;

import java.util.HashMap;
import java.util.Map;

public class StartProcessDelegate implements JavaDelegate {

    @Override
    public void execute(DelegateExecution execution) throws Exception {

        // Get the RuntimeService to start a new process instance
        RuntimeService runtimeService = execution.getProcessEngineServices().getRuntimeService();

        // Get extension properties from the BPMN model element
        CamundaProperties extensionProperties = execution.getBpmnModelElementInstance()
                .getExtensionElements()
                .getElementsQuery()
                .filterByType(CamundaProperties.class)
                .singleResult();

        if (extensionProperties == null) {
            throw new IllegalArgumentException("No extension properties found.");
        }

        // Variables for the new process instance
        Map<String, Object> startVariables = new HashMap<>();

        // Additionally pass along existing process variables if desired:
        // e.g., the current user ID
        String camundaUserId = (String) execution.getVariable("camunda_user_id");
        if (camundaUserId != null) {
            startVariables.put("camunda_user_id", camundaUserId);
        }

        String businessKey = (String) execution.getVariable("businessKey");
        if (businessKey != null) {
            startVariables.put("businessKey", businessKey);
        } else {
            // Or the current business key
            businessKey = execution.getBusinessKey();
            if (businessKey != null) {
                String businessKeySuffix = (String) execution.getVariable("businessKeySuffix");
                if (businessKeySuffix != null) {
                    businessKey += "-" + businessKeySuffix;
                }
                startVariables.put("businessKey", businessKey);
            }
        }

        // Check if config_chatID is provided among the delegate inputs
        Long configChatID = (Long) execution.getVariable("config_chatID");
        if (configChatID != null) {
            startVariables.put("config_chatID", configChatID);
        }
        
        String targetProcessDefinitionKey = null;

        // Iterate through each property and handle accordingly
        for (CamundaProperty property : extensionProperties.getCamundaProperties()) {
            String name = property.getCamundaName();
            String value = property.getCamundaValue();

            if ("targetProcessDefinitionKey".equals(name)) {
                // Grab the target process definition key
                targetProcessDefinitionKey = value;
            } else {
                // Put all other properties into the startVariables map
                startVariables.put(name, value);
            }
        }

        if (targetProcessDefinitionKey == null) {
            throw new IllegalArgumentException("targetProcessDefinitionKey is not defined in extension properties.");
        }

        // Now start the new process instance with the accumulated variables
        runtimeService.startProcessInstanceByKey(targetProcessDefinitionKey, businessKey, startVariables);
    }
}
