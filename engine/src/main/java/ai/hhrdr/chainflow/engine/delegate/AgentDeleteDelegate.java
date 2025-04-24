package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.web3j.abi.datatypes.Bool;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.logging.Logger;

@Component("agentDeleteDelegate")
public class AgentDeleteDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(AgentDeleteDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final HttpClient client = HttpClient.newHttpClient();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve variables
        String chatBotName = (String) execution.getVariable("config_chatbotName");
        String camundaUserId = (String) execution.getVariable("camunda_user_id");
        if (chatBotName == null || chatBotName.isEmpty()) {
            throw new IllegalArgumentException("One or more required process variables are missing.");
        }
        String fullChatBotName = camundaUserId + "_" + chatBotName;
        try {
            // Delete the chatbot
            deleteChatBot(fullChatBotName);
            // Delete the agents
//             deleteAgent(agentName);
//            if (deleteKnowledge) {
//                // Delete the skill
//                deleteSkill(skillName);
//                // Delete the knowledge base
//                deleteKnowledgeBase(knowledgeBaseName);
//            }
        } catch (Exception e) {
            LOGGER.severe("Error deleting agents, skills, or knowledge base: " + e.getMessage());
            throw new RuntimeException("Failed to delete agents, skills, or knowledge base", e);
        }
    }

    private void deleteChatBot(String agentName) throws Exception {
        String url = mindsdbURL + "/api/projects/mindsdb/chatbots/" + agentName;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .DELETE()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200 || response.statusCode() == 204) {
            LOGGER.info("Chatbot '" + agentName + "' deleted successfully.");
        } else {
            LOGGER.warning("Failed to delete agent '" + agentName + "': " + response.body());
        }
    }

    private void deleteAgent(String agentName) throws Exception {
        String url = mindsdbURL + "/api/projects/mindsdb/agents/" + agentName;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .DELETE()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200 || response.statusCode() == 204) {
            LOGGER.info("Agent '" + agentName + "' deleted successfully.");
        } else {
            LOGGER.warning("Failed to delete agent '" + agentName + "': " + response.body());
        }
    }

    private void deleteSkill(String skillName) throws Exception {
        String url = mindsdbURL + "/api/projects/mindsdb/skills/" + skillName;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .DELETE()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200 || response.statusCode() == 204) {
            LOGGER.info("Skill '" + skillName + "' deleted successfully.");
        } else {
            LOGGER.warning("Failed to delete skill '" + skillName + "': " + response.body());
        }
    }

    private void deleteKnowledgeBase(String knowledgeBaseName) throws Exception {
        String url = mindsdbURL + "/api/sql/query";

        String query = "DROP KNOWLEDGE BASE IF EXISTS " + knowledgeBaseName + ";";

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString("{\"query\":\"" + query + "\"}"))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 200 || response.statusCode() == 204) {
            LOGGER.info("Knowledge base '" + knowledgeBaseName + "' deleted successfully.");
        } else {
            LOGGER.warning("Failed to delete knowledge base '" + knowledgeBaseName + "': " + response.body());
        }
    }
}
