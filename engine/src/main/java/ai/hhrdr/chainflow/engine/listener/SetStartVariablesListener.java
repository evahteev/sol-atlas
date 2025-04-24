package ai.hhrdr.chainflow.engine.listener;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.ExecutionListener;
import org.camunda.bpm.engine.form.FormField;
import org.camunda.bpm.engine.form.StartFormData;
import org.camunda.bpm.model.bpmn.instance.StartEvent;
import org.camunda.bpm.model.bpmn.instance.camunda.CamundaProperties;
import org.camunda.bpm.model.bpmn.instance.camunda.CamundaProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Random;

@Component("setStartVariablesListener")
public class SetStartVariablesListener implements ExecutionListener {

    @Value("${bot.adminGroupId}")
    private String adminGroupId;

    @Value("${bot.name}")
    private String botName;

    @Value("${application.name}")
    private String applicationName;

    @Value("${application.token}")
    private String applicationToken;

    @Value("${application.url}")
    private String applicationUrl;

    @Override
    public void notify(DelegateExecution execution) throws Exception {
        // Set variable from application properties

        execution.setVariable("adminGroupId", adminGroupId);
        execution.setVariable("applicationName", applicationName);
        execution.setVariable("botName", botName);
        execution.setVariable("applicationUrl", applicationUrl);
        execution.setVariable("applicationToken", applicationToken);


        // Get the process definition ID to retrieve the start form data
        String processDefinitionId = execution.getProcessDefinitionId();
        StartFormData startFormData = execution.getProcessEngineServices()
                .getFormService()
                .getStartFormData(processDefinitionId);

        // Set variables from form fields
        if (startFormData != null) {
            List<FormField> formFields = startFormData.getFormFields();
            for (FormField formField : formFields) {
                String fieldId = formField.getId();
                if (execution.getVariable(fieldId) == null) {
                    execution.setVariable(fieldId, formField.getValue());
                }
            }
        }

        // Directly access the current StartEvent from the execution
        StartEvent startEvent = (StartEvent) execution.getBpmnModelElementInstance();

        // Set variables from extension properties
        if (startEvent != null && startEvent.getExtensionElements() != null) {
            // Retrieve all CamundaProperties elements instead of using singleResult()
            List<CamundaProperties> camundaPropertiesList = startEvent.getExtensionElements()
                    .getElementsQuery()
                    .filterByType(CamundaProperties.class)
                    .list();

            // Only proceed if we actually have CamundaProperties
            if (camundaPropertiesList != null && !camundaPropertiesList.isEmpty()) {
                CamundaProperties camundaProperties = camundaPropertiesList.get(0);
                for (CamundaProperty property : camundaProperties.getCamundaProperties()) {
                    String name = property.getCamundaName();
                    String value = property.getCamundaValue();
                    if (execution.getVariable(name) == null) {
                        execution.setVariable(name, value);
                    }
                }
            }

            // Check if we have "camunda_user_id" and convert it into a UUID with hyphens
            Object rawCamundaUserId = execution.getVariable("camunda_user_id");
            if (rawCamundaUserId != null) {
                String camundaUserId = rawCamundaUserId.toString();
                // Ensure it is exactly 32 chars (a stripped UUID), then insert hyphens
                if (camundaUserId.length() == 32) {
                    String userIdWithHyphens =
                            camundaUserId.substring(0, 8) + "-" +
                                    camundaUserId.substring(8, 12) + "-" +
                                    camundaUserId.substring(12, 16) + "-" +
                                    camundaUserId.substring(16, 20) + "-" +
                                    camundaUserId.substring(20);
                    execution.setVariable("user_id", userIdWithHyphens);
                } else {
                    // Fallback if it's not the correct length – handle however is appropriate
                    // e.g. log a warning or set a default
                    execution.setVariable("user_id", camundaUserId);
                }
            }

        }
    }
}
