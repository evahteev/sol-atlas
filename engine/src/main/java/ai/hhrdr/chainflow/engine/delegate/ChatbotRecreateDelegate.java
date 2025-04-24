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

@Component("chatbotRecreateDelegate")
public class ChatbotRecreateDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(ChatbotRecreateDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final HttpClient client = HttpClient.newHttpClient();

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {

        String chatBotName = (String) execution.getVariable("config_chatbotName");
        String agentName = (String) execution.getVariable("agentName");
        String agentNameMain = agentName + "_agent";

        String guruDatabaseName  = "guru_chatbot_db";
        try {
            // Attempt to delete the chatbot if it exists
            deleteChatBot(chatBotName);
            // Wait to ensure deletion is processed
            Thread.sleep(10000);

            // Create the chatbot
            createChatbot(chatBotName, guruDatabaseName, agentNameMain);
            // Wait to ensure creation is processed
            Thread.sleep(10000);

            // Describe the chatbot to retrieve the webhook token
            String chatbotWebhookToken = describeChatbot(chatBotName);

            // If webhook token is null, it might indicate an incomplete creation. Retry the process.
            if (chatbotWebhookToken == null) {
                LOGGER.warning("Webhook token is null. Retrying chatbot recreation for '" + chatBotName + "'.");
                // Delete the chatbot again
                deleteChatBot(chatBotName);
                Thread.sleep(10000);
                // Recreate the chatbot
                createChatbot(chatBotName, guruDatabaseName, agentNameMain);
                Thread.sleep(10000);
                // Describe again to get the webhook token
                chatbotWebhookToken = describeChatbot(chatBotName);

                if (chatbotWebhookToken == null) {
                    throw new RuntimeException("Failed to retrieve webhook token after recreation for chatbot '" + chatBotName + "'.");
                }
            }

            // Set the retrieved webhook token in the execution context
            execution.setVariable("chatbot_webhook_token", chatbotWebhookToken);
            LOGGER.info("Chatbot '" + chatBotName + "' successfully recreated with webhook token.");

        } catch (Exception e) {
            LOGGER.severe("Error recreating chatbot: " + e.getMessage());
            throw new RuntimeException("Error recreating chatbot", e);
        }
    }

    /**
     * Deletes the specified chatbot.
     *
     * @param chatBotName The name of the chatbot to delete.
     * @throws Exception if the deletion fails.
     */
    private void deleteChatBot(String chatBotName) throws Exception {
        String url = mindsdbURL + "/api/projects/mindsdb/chatbots/" + chatBotName;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .DELETE()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200 || response.statusCode() == 204) {
            LOGGER.info("Chatbot '" + chatBotName + "' deleted successfully.");
        } else if (response.statusCode() == 404) {
            LOGGER.info("Chatbot '" + chatBotName + "' does not exist. No deletion needed.");
        } else {
            LOGGER.warning("Failed to delete chatbot '" + chatBotName + "': " + response.body());
            throw new RuntimeException("Failed to delete chatbot '" + chatBotName + "'. HTTP Status: " + response.statusCode());
        }
    }

    /**
     * Creates a new chatbot with the specified parameters.
     *
     * @param chatbotName  The name of the chatbot to create.
     * @param databaseName The name of the database to use.
     * @param agentName    The name of the agent to associate with the chatbot.
     * @throws Exception if the creation fails.
     */
    private void createChatbot(String chatbotName, String databaseName, String agentName) throws Exception {
        String url = mindsdbURL + "/api/sql/query";

        // Construct the SQL query for chatbot creation
        String query = "CREATE CHATBOT " + chatbotName
                + " USING database='" + databaseName + "', agent='" + agentName + "';";

        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        int code = response.statusCode();
        if (code >= 200 && code < 300) {
            LOGGER.info("Chatbot '" + chatbotName + "' created successfully via SQL query.");
        } else {
            LOGGER.severe("Failed to create chatbot '" + chatbotName + "': " + response.body());
            throw new RuntimeException(
                    "Failed to create chatbot '" + chatbotName + "'. HTTP Status: " + code
            );
        }
    }

    /**
     * Describes the specified chatbot to retrieve its webhook token.
     *
     * @param chatbotName The name of the chatbot to describe.
     * @return The webhook token of the chatbot.
     * @throws Exception if the description fails or the webhook token is not found.
     */
    private String describeChatbot(String chatbotName) throws Exception {
        String url = mindsdbURL + "/api/sql/query";

        // Construct the SQL query for describing the chatbot
        String query = "DESCRIBE CHATBOT " + chatbotName + ";";

        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        int code = response.statusCode();

        if (code < 200 || code >= 300) {
            LOGGER.severe("Failed to describe chatbot '" + chatbotName + "'. HTTP Status: " + code + ". Response: " + response.body());
            throw new RuntimeException(
                    "Failed to describe chatbot '" + chatbotName + "'. HTTP Status: " + code
            );
        }

        JsonNode respJson = mapper.readTree(response.body());

        // Extract column names
        JsonNode columnNamesNode = respJson.get("column_names");
        if (columnNamesNode == null || !columnNamesNode.isArray()) {
            LOGGER.severe("No 'column_names' in describe result for chatbot '" + chatbotName + "'. Response: " + response.body());
            throw new RuntimeException("Invalid describe response: 'column_names' missing.");
        }

        // Find the index of the "WEBHOOK_TOKEN" column
        int tokenIndex = -1;
        for (int i = 0; i < columnNamesNode.size(); i++) {
            if ("WEBHOOK_TOKEN".equalsIgnoreCase(columnNamesNode.get(i).asText())) {
                tokenIndex = i;
                break;
            }
        }
        if (tokenIndex < 0) {
            LOGGER.severe("No 'WEBHOOK_TOKEN' column found in describe result for chatbot '" + chatbotName + "'. Response: " + response.body());
            throw new RuntimeException("Column 'WEBHOOK_TOKEN' not found.");
        }

        // Extract data rows
        JsonNode dataNode = respJson.get("data");
        if (dataNode == null || !dataNode.isArray() || dataNode.size() == 0) {
            LOGGER.warning("No data found in describe result for chatbot '" + chatbotName + "'.");
            return null;
        }

        // Assume the first row contains the relevant information
        JsonNode firstRow = dataNode.get(0);
        if (!firstRow.isArray() || firstRow.size() <= tokenIndex) {
            LOGGER.severe("Row does not have enough columns to retrieve 'WEBHOOK_TOKEN' for chatbot '" + chatbotName + "'. Response: " + response.body());
            throw new RuntimeException("Insufficient data to retrieve 'WEBHOOK_TOKEN'.");
        }

        // Extract the webhook token
        String webhookToken = firstRow.get(tokenIndex).asText();
        if (webhookToken == null || webhookToken.isEmpty()) {
            LOGGER.warning("Webhook token is null or empty for chatbot '" + chatbotName + "'.");
            return null;
        }

        LOGGER.info("Retrieved webhook_token='" + webhookToken + "' for chatbot='" + chatbotName + "'.");
        return webhookToken;
    }
}
