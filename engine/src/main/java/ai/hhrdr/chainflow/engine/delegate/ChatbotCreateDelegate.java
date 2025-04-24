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

@Component("chatbotCreateDelegate")
public class ChatbotCreateDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(ChatbotCreateDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve agentName from the process variables
        String chatName = (String) execution.getVariable("chatName");
        String camundaUserId = (String) execution.getVariable("camunda_user_id");

        String chatBotName = camundaUserId + "_" + chatName;

        String agentNameMain = (String) execution.getVariable("agentName");

        String guruDatabaseName  = "guru_chatbot_db";

        try {
            // Check if the chatbot already has a webhook token
            String chatbotWebhookToken = getChatbotWebhook(chatBotName);

            // If not, create the chatbot and try fetching the token again after a brief wait
            if (chatbotWebhookToken == null || chatbotWebhookToken.isEmpty()) {
                createChatbot(chatBotName, guruDatabaseName, agentNameMain);
                Thread.sleep(10000); // wait for the chatbot to be fully created
                chatbotWebhookToken = getChatbotWebhook(chatBotName);
            }

            execution.setVariable("chatbotWebhookToken", chatbotWebhookToken);

        } catch (Exception e) {
            LOGGER.severe("Error creating chatbot: " + e.getMessage());
            throw new RuntimeException("Failed to create chatbot", e);
        }
    }

    /**
     * Creates a chatbot using the given chatbot name, database name, and agent name.
     */
    private void createChatbot(String chatbotName, String databaseName, String agentName) throws Exception {
        String url = mindsdbURL + "/api/sql/query";

        // Build the SQL query to create the chatbot
        String query = "CREATE CHATBOT " + chatbotName
                + " USING database='" + databaseName + "', agent='" + agentName + "';";

        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        int code = response.statusCode();

        if (code >= 200 && code < 300) {
            LOGGER.info("Chatbot '" + chatbotName + "' created successfully via SQL query.");
        } else {
            throw new RuntimeException(
                    "Failed to create chatbot '" + chatbotName + "': " + response.body()
            );
        }
    }

    /**
     * Retrieves the webhook token for the specified chatbot.
     */
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
            LOGGER.info("Failed to fetch chatbot details for '" + chatbotName + "': HTTP " + statusCode + " - " + response.body());
            return null;
        }

        JsonNode respJson = mapper.readTree(response.body());
        JsonNode webhookTokenNode = respJson.get("webhook_token");
        if (webhookTokenNode == null || webhookTokenNode.asText().isEmpty()) {
            LOGGER.info("No 'webhook_token' found for chatbot '" + chatbotName + "'.");
            return null;
        }
        String webhookToken = webhookTokenNode.asText();
        LOGGER.info("Webhook token for chatbot '" + chatbotName + "': " + webhookToken);
        return webhookToken;
    }
}
