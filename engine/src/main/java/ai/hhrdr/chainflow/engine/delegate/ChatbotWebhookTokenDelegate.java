package ai.hhrdr.chainflow.engine.delegate;

import com.fasterxml.jackson.databind.JsonNode;
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

@Component("chatbotWebhookTokenDelegate")
public class ChatbotWebhookTokenDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(ChatbotWebhookTokenDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final HttpClient client = HttpClient.newHttpClient();
    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve the chatbot name from process variables
        String chatName = (String) execution.getVariable("chatName");
        String camundaUserId = (String) execution.getVariable("camunda_user_id");
        String chatBotName = camundaUserId + "_" + chatName;

        try {
            // Retrieve the webhook token by describing the chatbot
            String chatbotWebhookToken = getChatbotWebhook(chatBotName);

            if (chatbotWebhookToken == null) {
                execution.setVariable("chatbotWebhookToken", null);
            }

            // Set the retrieved webhook token in the execution context
            execution.setVariable("chatbotWebhookToken", chatbotWebhookToken);
            LOGGER.info("Successfully retrieved webhook token for chatbot '" + chatBotName + "'.");
        } catch (Exception e) {
            LOGGER.severe("Error retrieving webhook token: " + e.getMessage());
            throw new RuntimeException("Error retrieving webhook token for chatbot '" + chatBotName + "'.", e);
        }
    }

    private String getChatbotWebhook(String chatbotName) throws Exception {
        String url = mindsdbURL + "/api/projects/mindsdb/chatbots/" + chatbotName;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();

        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        int statusCode = response.statusCode();
        if (statusCode < 200 || statusCode >= 300) {
            LOGGER.info(
                    "Failed to fetch chatbot details for '" + chatbotName + "': HTTP " + statusCode + " - " + response.body()
            );
            return null;
        }

        JsonNode respJson = mapper.readTree(response.body());

        JsonNode webhookTokenNode = respJson.get("webhook_token");
        if (webhookTokenNode == null || webhookTokenNode.asText().isEmpty()) {
            LOGGER.info("No 'webhook_token' found for chatbot '" + chatbotName + "'. Returning null.");
            return null;
        }

        String webhookToken = webhookTokenNode.asText();
        LOGGER.info("Webhook token for chatbot '" + chatbotName + "': " + webhookToken);
        return webhookToken;

    }
}
