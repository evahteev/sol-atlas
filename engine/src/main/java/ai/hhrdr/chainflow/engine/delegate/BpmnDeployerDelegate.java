package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RepositoryService;
import org.camunda.bpm.engine.repository.Deployment;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.model.bpmn.Bpmn;
import org.camunda.bpm.model.bpmn.BpmnModelInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

@Component("bpmnDeployerDelegate")
public class BpmnDeployerDelegate implements JavaDelegate {

    @Autowired
    private RepositoryService repositoryService;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // 1. Retrieve BPMN XML from a process variable
        String bpmnXml = (String) execution.getVariable("bpmnXml");
        String bpmnXmlName = (String) execution.getVariable("bpmnXmlName");
        execution.setVariable("deployed", false);

        if (bpmnXml == null || bpmnXml.trim().isEmpty()) {
            execution.setVariable("error", "BPMN XML is null or empty.");
            throw new IllegalArgumentException("No BPMN XML found in variable 'bpmnXml'.");
        }

        try {
            // 2. Validate the BPMN using Camunda's Model API
            BpmnModelInstance modelInstance = Bpmn.readModelFromStream(
                    new ByteArrayInputStream(bpmnXml.getBytes(StandardCharsets.UTF_8))
            );
            Bpmn.validateModel(modelInstance);
        } catch (Exception e) {
            execution.setVariable("error", e.getMessage());
            execution.setVariable("bpmnXml", bpmnXml); // bpmnXml input != bpmnXml variable
            return;
        }

        // 3. Deploy the BPMN XML to the Camunda engine
        Deployment deployment = repositoryService
                .createDeployment()
                .addString(bpmnXmlName + ".bpmn", bpmnXml)
                .deploy();

        // 4. Store the deployment ID in another process variable
        String deploymentId = deployment.getId();
        if (deploymentId == null) {
            execution.setVariable("error", "Deployment ID is null.");
            execution.setVariable("bpmnXml", bpmnXml);
            throw new IllegalStateException("Deployment failed, no deployment ID returned.");
        }
        execution.setVariable("deploymentId", deploymentId);
        execution.setVariable("deployed", true);
    }
}