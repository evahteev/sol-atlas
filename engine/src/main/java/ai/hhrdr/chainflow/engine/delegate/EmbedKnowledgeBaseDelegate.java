package ai.hhrdr.chainflow.engine.delegate;

import ai.hhrdr.chainflow.engine.utils.InputSanitizer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.logging.Logger;

@Component("embedKnowledgeBaseDelegate")
public class EmbedKnowledgeBaseDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(EmbedKnowledgeBaseDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve variables
        String knowledgeBaseName = (String) execution.getVariable("config_knowledgeBaseName");
        String formQuestion = (String) execution.getVariable("form_question");
        String formReply = (String) execution.getVariable("form_reply");
        String answer = (String) execution.getVariable("answer");

        if (formReply == null || formReply.isEmpty()) {
            formReply = formQuestion;
        }
        if (knowledgeBaseName == null || knowledgeBaseName.isEmpty() ||
                formReply == null || formReply.isEmpty() ||
                answer == null || answer.isEmpty()) {
            throw new IllegalArgumentException("Knowledge base name, form_question, and answer are required but missing.");
        }

        // Sanitize input
        String sanitizedContent = InputSanitizer.sanitizeInput("Human: " + formReply + " AI: " + answer);

        try {
            // Save content to knowledge base
            saveToKnowledgeBase(knowledgeBaseName, sanitizedContent);
        } catch (Exception e) {
            LOGGER.severe("Error embedding knowledge into the knowledge base: " + e.getMessage());
            throw new RuntimeException("Failed to embed knowledge into the knowledge base", e);
        }
    }

    private void saveToKnowledgeBase(String knowledgeBaseName, String content) throws Exception {
        String url = mindsdbURL + "/api/sql/query";

        // Create SQL insert statement
        String query = "INSERT INTO mindsdb.`" + knowledgeBaseName + "` (content) VALUES ('" + content + "');";

        // Build the request payload
        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        // Send HTTP POST request
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // Handle response
        if (response.statusCode() == 200 || response.statusCode() == 201) {
            LOGGER.info("Content embedded into knowledge base '" + knowledgeBaseName + "' successfully.");
        } else {
            throw new RuntimeException("Failed to embed content into knowledge base '" + knowledgeBaseName + "': " + response.body());
        }
    }
}
