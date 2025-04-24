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

@Component("agentExistenceDelegate")
public class AgentExistenceDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(AgentExistenceDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve the base agent name from process variables
        String agentName = (String) execution.getVariable("agentName");

        // Construct names following the naming convention
        String agentNameMain = agentName + "_agent";
        String chatbotName = agentName + "_chatbot";

        // Check if the agent exists
        boolean agentExists = checkAgentExists(agentNameMain);

        // Check if the chatbot exists
        boolean chatbotExists = checkChatbotExists(chatbotName);

        LOGGER.info("Agent exists: " + agentExists + ", Chatbot exists: " + chatbotExists);

        // Set the process variable 'chatbot_exists' to true only if both agent and chatbot exist.
        execution.setVariable("chatbotExists", agentExists || chatbotExists);
    }

    /**
     * Check if an agent exists by issuing a DESCRIBE AGENT SQL query.
     */
    private boolean checkAgentExists(String agentName) throws Exception {
        String url = mindsdbURL + "/api/sql/query";
        String query = "DESCRIBE AGENT " + agentName + ";"; // Adjust this if your SQL dialect differs

        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        int status = response.statusCode();

        if (status >= 200 && status < 300) {
            JsonNode respJson = mapper.readTree(response.body());
            JsonNode dataNode = respJson.get("data");
            if (dataNode != null && dataNode.isArray() && dataNode.size() > 0) {
                LOGGER.info("Agent '" + agentName + "' exists.");
                return true;
            }
        }
        LOGGER.info("Agent '" + agentName + "' does not exist.");
        return false;
    }

    /**
     * Check if a chatbot exists by issuing a DESCRIBE CHATBOT SQL query.
     */
    private boolean checkChatbotExists(String chatbotName) throws Exception {
        String url = mindsdbURL + "/api/sql/query";
        String query = "DESCRIBE CHATBOT " + chatbotName + ";";

        ObjectNode payload = mapper.createObjectNode();
        payload.put("query", query);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        int status = response.statusCode();

        if (status >= 200 && status < 300) {
            JsonNode respJson = mapper.readTree(response.body());
            JsonNode dataNode = respJson.get("data");
            if (dataNode != null && dataNode.isArray() && dataNode.size() > 0) {
                LOGGER.info("Chatbot '" + chatbotName + "' exists.");
                return true;
            }
        }
        LOGGER.info("Chatbot '" + chatbotName + "' does not exist.");
        return false;
    }
}
