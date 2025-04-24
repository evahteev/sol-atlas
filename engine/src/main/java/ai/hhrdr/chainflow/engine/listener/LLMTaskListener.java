package ai.hhrdr.chainflow.engine.listener;

import ai.hhrdr.chainflow.engine.utils.InputSanitizer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.camunda.bpm.engine.delegate.DelegateTask;
import org.camunda.bpm.engine.delegate.Expression;
import org.camunda.bpm.engine.delegate.TaskListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.logging.Logger;

@Component("LLMTaskListener")
public class LLMTaskListener implements TaskListener {

    private static final Logger LOGGER = Logger.getLogger(LLMTaskListener.class.getName());
    private final ObjectMapper mapper = new ObjectMapper();

    /**
     * Base URL for MindsDB. Example: "http://localhost:47334".
     * Adjust it based on your environment.
     */
    @Value("${mindsdb.url}")
    private String mindsdbUrl;
    // ==================== Field Injections ========================
    private Expression chatId;    // corresponds to <camunda:field name="chatId" />
    private Expression threadId;    // corresponds to <camunda:field name="chatId" />
    private Expression userId;    // corresponds to <camunda:field name="userId" />
    private Expression outputVar;

    @Override
    public void notify(DelegateTask delegateTask) {
        LOGGER.info("LLMTaskListener triggered for task: " + delegateTask.getId());


        Long threadIdValue = null;
        if (threadId != null) {
            Object telegramThreadIdObj = threadId.getValue(delegateTask.getExecution());
            if (telegramThreadIdObj instanceof Number) {
                threadIdValue = ((Number) telegramThreadIdObj).longValue();
            } else if (telegramThreadIdObj != null) {
                throw new IllegalArgumentException("telegramThreadIdExp must be a Number (Integer or Long) or null.");
            }

        }

        String questionValue = delegateTask.getDescription();

        questionValue = InputSanitizer.sanitizeInput(questionValue);

        String outputVarValue = extractStringValue(outputVar, delegateTask);
        // these variables, are coming from field injections ^

        delegateTask.setVariable(outputVarValue, "AGENT_FAILED");

        // webhook token
        String webhookToken = (String) delegateTask.getVariable("chatbotWebhookToken");

        String chatName = (String) delegateTask.getVariable("chatName");
        String camundaUserId = (String) delegateTask.getVariable("camunda_user_id");

        String chatBotName = camundaUserId + "_" + chatName;


        // 3. Build the final MindsDB webhook URL:
        //    <mindsdb_url>/api/webhooks/chatbots/<webhook_token>
        String webhookUrl = mindsdbUrl + "/api/webhooks/chatbots/" + webhookToken;

        ObjectNode payload = mapper.createObjectNode();
        payload.put("task_id", delegateTask.getId());
        payload.put("agent_name", chatBotName);
        payload.put("user_id", camundaUserId);
        payload.put("output_var", outputVarValue);
        payload.put("thread_id", threadIdValue);
        payload.put("question", questionValue);

        // 5. Send POST request to MindsDB
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(webhookUrl))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                    .build();

            HttpClient client = HttpClient.newHttpClient();
            client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenAccept(response -> LOGGER.info("LLMTaskListener: Async webhook call completed. Response: " + response.body()))
                    .exceptionally(e -> {
                        LOGGER.severe("LLMTaskListener: Async webhook call failed. Exception: " + e.getMessage());
                        return null;
                    });
        } catch (Exception e) {
            LOGGER.severe("LLMTaskListener: Exception occurred during async call setup: " + e.getMessage());
            throw new RuntimeException(e);
        }
    }

    /**
     * Helper method to extract a String value from an Expression.
     */
    private String extractStringValue(Expression expression, DelegateTask delegateTask) {
        if (expression != null) {
            Object value = expression.getValue(delegateTask.getExecution());
            if (value instanceof String) {
                return (String) value;
            } else if (value != null) {
                throw new IllegalArgumentException("Value is not of type String: " + value);
            }
        }
        return null;
    }


}
