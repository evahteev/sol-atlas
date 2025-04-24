package ai.hhrdr.chainflow.engine.listener;

import ai.hhrdr.chainflow.engine.utils.InputSanitizer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.camunda.bpm.engine.delegate.DelegateTask;
import org.camunda.bpm.engine.delegate.Expression;
import org.camunda.bpm.engine.delegate.TaskListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.*;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component("agentTaskListener")
public class AgentTaskListener implements TaskListener {

    private static final Logger logger = Logger.getLogger(AgentTaskListener.class.getName());
    private final ObjectMapper mapper = new ObjectMapper();
    private static final String DEFAULT_ANSWER = "AGENT_FAILED";

    /**
     * Base URL for MindsDB. Example: "http://localhost:47334".
     * Adjust it based on your environment.
     */
    @Value("${mindsdb.url}")
    private String mindsdbURL;

    // Corresponds to <camunda:field name="agentName" />
    private Expression agentName;
    // Corresponds to <camunda:field name="systemPrompt" />
    private Expression systemPrompt;

    @Override
    public void notify(DelegateTask delegateTask) {
        logger.info("AgentTaskListener triggered for task: " + delegateTask.getId());

        // Evaluate expressions to obtain String values
        String questionValue = delegateTask.getDescription();
        String agentNameValue = extractStringValue(agentName, delegateTask);
        String systemPromptValue = extractStringValue(systemPrompt, delegateTask);
        String taskId = delegateTask.getId();

        delegateTask.setVariable(agentNameValue + "_answer", "AGENT_FAILED");

        questionValue = InputSanitizer.sanitizeInput(questionValue);

        Map<String, String> message = new HashMap<>();
        if (questionValue == null) {
            questionValue = delegateTask.getDescription();
        }

        message.put("question", questionValue);
        message.put("answer", ""); // Empty answer for initial request

        // Build the JSON payload
        Map<String, Object> payload = new HashMap<>();
        payload.put("messages", Collections.singletonList(message));
        payload.put("task_id", delegateTask.getId());
        payload.put("question", questionValue);


        // Construct the URL using the evaluated agent name value
        String url = mindsdbURL + "/api/projects/mindsdb/agents/" + agentNameValue + "/completions";

        // Prepare HTTP headers
        HttpHeaders headers = new HttpHeaders();
        headers.add("Content-Type", "application/json");

        try {
            // Serialize the payload into a proper JSON string
            String jsonPayload = mapper.writeValueAsString(payload);

            // Create the HTTP request entity with the serialized payload
            HttpEntity<String> requestEntity = new HttpEntity<>(jsonPayload, headers);

            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestEntity, Map.class);

            String content = DEFAULT_ANSWER;
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                // Extract the 'content' from the 'message' map in the response body
                Object messageObj = responseBody.get("message");
                if (messageObj instanceof Map) {
                    Map messageMap = (Map) messageObj;
                    content = (String) messageMap.getOrDefault("content", DEFAULT_ANSWER);
                    // Remove code block markers (e.g., triple backticks) from the content string
                    content = content.replaceAll("```", "").trim();
                }
            } else {
                logger.severe("Unexpected response from MindsDB: " + response);
                // Throw a RuntimeException so that Camunda raises an incident
                throw new RuntimeException("Unexpected response from MindsDB");
            }

            Pattern thinkPattern = Pattern.compile("<think>([\\s\\S]*?)</think>", Pattern.CASE_INSENSITIVE);
            Matcher matcher = thinkPattern.matcher(content);
            List<String> thinkBlocks = new ArrayList<>();
            StringBuffer cleanedContent = new StringBuffer();

            // Find and remove think blocks while collecting their content
            while (matcher.find()) {
                String blockContent = matcher.group(1).trim();
                thinkBlocks.add(blockContent);
                matcher.appendReplacement(cleanedContent, "");
            }
            matcher.appendTail(cleanedContent);
            content = cleanedContent.toString().trim();

            // Combine think blocks into a single string (separated by spaces or newlines)
            String llmThinkString = String.join(" ", thinkBlocks);
            if (!llmThinkString.isEmpty()) {
                // Save the combined think content in a separate process variable.
                // For example, if outputVarValue is "agent_answer", the thinking will be stored in "agent_answerThinking".
                delegateTask.setVariable(agentNameValue + "_answer" + "Thinking", llmThinkString);
            }
            // Set the response as a process variable
            delegateTask.setVariable(agentNameValue + "_answer", content);
            delegateTask.complete();

        } catch (Exception e) {
            logger.severe("Error while querying MindsDB: " + e.getMessage());
            // Throw a RuntimeException so that Camunda raises an incident
            throw new RuntimeException("Error while querying MindsDB", e);
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

    /**
     * Helper method to extract a Long value from an Expression.
     */
    private Long extractLongValue(Expression expression, DelegateTask delegateTask) {
        if (expression != null) {
            Object value = expression.getValue(delegateTask.getExecution());
            if (value instanceof Long) {
                return (Long) value;
            } else if (value != null) {
                throw new IllegalArgumentException("Value is not of type Long: " + value);
            }
        }
        return null;
    }
}
