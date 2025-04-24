package ai.hhrdr.chainflow.engine.delegate;

import ai.hhrdr.chainflow.engine.utils.InputSanitizer;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;


@Component("agentQueryDelegate")
public class AgentQueryDelegate implements JavaDelegate {

    private static final Logger logger = LoggerFactory.getLogger(AgentQueryDelegate.class.getName());
    private static final String DEFAULT_ANSWER = "Hello! How can I assist you today?";

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Sanitize input
        String question = InputSanitizer.sanitizeInput((String) execution.getVariable("question"));
        String agentName = (String) execution.getVariable("agent_name");

        if (question == null || question.isEmpty()) {
            throw new IllegalArgumentException("The question variable is required but was null or empty.");
        }
        if (agentName == null || agentName.isEmpty()) {
            throw new IllegalArgumentException("The agent_name variable is required but was null or empty.");
        }

        String historyJson = (String) execution.getVariable("history");
        if (historyJson == null || historyJson.trim().isEmpty()) {
            historyJson = "[]";  // fallback
        }
        ObjectMapper objectMapper = new ObjectMapper();
        List<Map<String, String>> historyList = objectMapper.readValue(
                historyJson, new TypeReference<List<Map<String, String>>>() {}
        );
        Map<String, String> message = new HashMap<>();
        if (!historyList.isEmpty()) {
            message = historyList.get(historyList.size() - 1);
        } else {
            message.put("question", question);
            message.put("answer", ""); // Empty answer for initial request
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("messages", Collections.singletonList(message));

        // Construct URL
        String url = mindsdbURL + "/api/projects/mindsdb/agents/" + agentName + "/completions";

        // Prepare headers
        HttpHeaders headers = new HttpHeaders();
        headers.add("Content-Type", "application/json");

        // Create HTTP request
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

        try {
            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);

            String content = DEFAULT_ANSWER;
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();

                // Extract the content from the response
                content = (String) ((Map) responseBody.getOrDefault("message", new HashMap<>())).getOrDefault("content", DEFAULT_ANSWER);
            } else {
                logger.error("Unexpected response from MindsDB: {}", response);
                // Throw a RuntimeException so Camunda will raise an incident
                throw new RuntimeException("Unexpected response from MindsDB");
            }

            // Set the response as a process variable
            execution.setVariable("answer", content);

            // If the text_answer variable exists, set it to the same value as answer
            if (execution.hasVariable("text_answer")) {
                execution.setVariable("text_answer", content);
            }
        } catch (Exception e) {
            logger.error("Error while querying MindsDB: ", e);
            // Throw a RuntimeException so Camunda will raise an incident
            throw new RuntimeException("Error while querying MindsDB", e);
        }
    }
}
