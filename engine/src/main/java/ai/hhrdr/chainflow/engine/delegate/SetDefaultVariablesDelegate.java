package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.engine.form.StartFormData;
import org.camunda.bpm.engine.form.FormField;
import org.springframework.stereotype.Component;

import java.util.List;

@Component("setDefaultVariablesDelegate")
public class SetDefaultVariablesDelegate implements JavaDelegate {

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Get the process definition key to retrieve the start form data
        String processDefinitionId = execution.getProcessDefinitionId();
        StartFormData startFormData = execution.getProcessEngineServices()
                .getFormService()
                .getStartFormData(processDefinitionId);

        // Get all form fields from the start form
        List<FormField> formFields = startFormData.getFormFields();

        // Loop through all form fields
        for (FormField formField : formFields) {
            String fieldId = formField.getId();
            // Check if the actual variable is already set in the execution
            if (execution.getVariable(fieldId) == null) {
                execution.setVariable(fieldId, formField.getValue());

            }
        }
    }
}
