package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.RuntimeService;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.engine.impl.persistence.entity.ExecutionEntity;
import org.springframework.stereotype.Component;

@Component("chatbotMessageDelegate")
public class ChatbotMessageDelegate implements JavaDelegate {

    @Override
    public void execute(DelegateExecution execution) throws Exception {

        // Get references to runtime and repository services
        RuntimeService runtimeService = execution.getProcessEngineServices().getRuntimeService();

        // Retrieve relevant process variables
        String camundaUserId = (String) execution.getVariable("camunda_user_id");
        String chatName = (String) execution.getVariable("chatName");
        String form_chatName = (String) execution.getVariable("form_chatName");


        Long threadID = (Long) execution.getVariable("config_threadID");
        Long chatID = (Long) execution.getVariable("config_chatID");


        if (chatName == null || chatName.isEmpty()) {
            chatName = "dm";
        }

        // Construct the business key (matching the initiating process)
        String accountId = addHyphensToUuid(camundaUserId);
        String businessKey = accountId + "-active-" + chatName;

        // Retrieve additional variables to pass along
        String chatbotMessage = (String) execution.getVariable("chatbotMessage");
        String buttonLink     = (String) execution.getVariable("buttonLink");
        String buttonText     = (String) execution.getVariable("buttonText");
        Boolean directSend     = (Boolean) execution.getVariable("directSend");

        if (directSend == null) {
            directSend = false;
        }

        ExecutionEntity executionEntity = (ExecutionEntity) execution;
        String rootProcessInstanceId = executionEntity.getRootProcessInstanceId();

        // Correlate the message to start a new process instance with the given business key.
        runtimeService
                .createMessageCorrelation("MESSAGE_CHATBOT")
                .processInstanceBusinessKey(businessKey)
                .setVariable("chatbotMessage", chatbotMessage)
                .setVariable("callingProcessInstanceId", rootProcessInstanceId)
                .setVariable("camunda_user_id", camundaUserId)
                .setVariable("config_chatID", chatID)
                .setVariable("config_threadID", threadID)
                .setVariable("form_chatName", form_chatName)
                .setVariable("form_directSend", directSend)
                .setVariable("chatName", chatName)
                .setVariable("buttonLink", buttonLink)
                .setVariable("buttonText", buttonText)
                .correlateStartMessage(); // use correlateStartMessage() for a message start event
    }

    /**
     * Restores hyphens in a UUID string from which hyphens have been removed.
     *
     * @param uuidWithoutHyphens A 32-character string representing a UUID with no hyphens.
     * @return A string in the standard UUID format (8-4-4-4-12).
     * @throws IllegalArgumentException if the input string is not exactly 32 characters long.
     */
    public static String addHyphensToUuid(String uuidWithoutHyphens) {
        if (uuidWithoutHyphens == null || uuidWithoutHyphens.length() != 32) {
            throw new IllegalArgumentException(
                    "UUID string must be exactly 32 characters long (no hyphens). Provided: " +
                            (uuidWithoutHyphens == null ? "null" : uuidWithoutHyphens.length())
            );
        }

        return uuidWithoutHyphens.substring(0, 8) + "-" +
                uuidWithoutHyphens.substring(8, 12) + "-" +
                uuidWithoutHyphens.substring(12, 16) + "-" +
                uuidWithoutHyphens.substring(16, 20) + "-" +
                uuidWithoutHyphens.substring(20, 32);
    }
}
