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

@Component("EmbedMessageInKBDelegate")
public class EmbedMessageInKBDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(EmbedMessageInKBDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        String formQuestion = (String) execution.getVariable("form_question");
        String agentName = (String) execution.getVariable("agentName");
        String knowledgeBaseName = agentName + "_kb";

        if (knowledgeBaseName.equals("_kb")) {
            throw new IllegalArgumentException("Knowledge base name (config_knowledgeBaseName) is required but missing.");
        }
        if (formQuestion == null || formQuestion.isEmpty()) {
            throw new IllegalArgumentException("No content (form_question) to embed in KB.");
        }

        String sanitizedContent = InputSanitizer.sanitizeInput(formQuestion);

        try {
            saveToKnowledgeBase(knowledgeBaseName, sanitizedContent);
        } catch (Exception e) {
            LOGGER.severe("Error embedding content into knowledge base: " + e.getMessage());
            throw new RuntimeException("Failed to embed content into the knowledge base", e);
        }
    }

    private void saveToKnowledgeBase(String knowledgeBaseName, String content) throws Exception {
        String url = mindsdbURL + "/api/sql/query";

        String query = "INSERT INTO mindsdb.`" + knowledgeBaseName + "` (content) VALUES ('" + content + "');";

        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200 || response.statusCode() == 201) {
            LOGGER.info("Content embedded into knowledge base '" + knowledgeBaseName + "' successfully.");
        } else {
            throw new RuntimeException("Failed to embed content into knowledge base '"
                    + knowledgeBaseName + "': " + response.body());
        }
    }
}
