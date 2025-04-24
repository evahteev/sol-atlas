package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.stereotype.Component;

@Component("chatbotDefaultsSetupDelegate")
public class ChatbotDefaultsSetupDelegate implements JavaDelegate {

        /**
         * Safely converts a value to a String.
         * Returns an empty string if the value is null.
         */
        private String safeToString(Object value) {
            return (value != null) ? value.toString() : "";
        }

        @Override
        public void execute(DelegateExecution execution) throws Exception {
            // Retrieve variables from the process execution
            Object configChatID = execution.getVariable("config_chatID");
            Object configThreadID = execution.getVariable("config_threadID");
            Object telegramUserID = execution.getVariable("telegram_user_id");
            Object formChatName = execution.getVariable("form_chatName");
            String existingChatName = safeToString(execution.getVariable("chatName"));
            Object configchatHumanName = execution.getVariable("config_chatHumanName");

            // Safely convert values to strings
            String chatIDString = safeToString(configChatID);
            String threadIDString = safeToString(configThreadID);

            // Prepend underscore for chatID if not empty
            if (!chatIDString.isEmpty()) {
                chatIDString = "_" + chatIDString.replaceFirst("^-", "");
            } else {
                execution.setVariable("config_chatID", telegramUserID);
            }

            // Prepend underscore for threadID if not empty
            if (!threadIDString.isEmpty()) {
                threadIDString = "_" + threadIDString;
            }

            // Check if the existing chatName already contains both chatIDString and threadIDString.
            // If not, update it.
            // Check if the existing chatName is "dm"
            if ("dm".equals(existingChatName)) {
                // Leave chatName as is and set chatbotHumanName to the same value without any additions.
                execution.setVariable("chatbotHumanName", existingChatName);
                execution.setVariable("chatbotHumanName", existingChatName);
            } else if (existingChatName.trim().isEmpty()
                    || !(existingChatName.contains(chatIDString) && existingChatName.contains(threadIDString))) {
                // If the current chatName is empty or doesn't already contain the expected id portions then update it.
                String chatNameString = safeToString(formChatName);
                String chatName = chatNameString + chatIDString + threadIDString;
                execution.setVariable("chatName", chatName);
                String defaultChatbotHumanName = chatNameString + " #" + chatIDString + threadIDString;
                execution.setVariable("chatbotHumanName", defaultChatbotHumanName);
            } else {
                // Otherwise use the provided config_chatHumanName if available, or fall back to the existing chatName.
                String chatbotHumanName = (configchatHumanName != null)
                        ? configchatHumanName.toString()
                        : existingChatName;
                execution.setVariable("chatbotHumanName", chatbotHumanName);
            }
            // provision other defaults
            execution.setVariable("form_reply", null);
            execution.setVariable("form_answer", null);
            execution.setVariable("question_discovery_agent_answer", null);
            execution.setVariable("chatbotWebhookToken", null);
            execution.setVariable("buttonLink", null);
            execution.setVariable("buttonText", null);
        }
    }


