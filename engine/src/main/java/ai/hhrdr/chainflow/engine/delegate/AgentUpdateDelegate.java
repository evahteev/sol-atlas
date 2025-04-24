package ai.hhrdr.chainflow.engine.delegate;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
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

@Component("agentUpdateDelegate")
public class AgentUpdateDelegate implements JavaDelegate {

    private static final Logger LOGGER = Logger.getLogger(AgentUpdateDelegate.class.getName());

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        LOGGER.info("Starting AgentUpdateDelegate...");
        String agentName      = (String) execution.getVariable("config_agentName");
        String model          = (String) execution.getVariable("config_agentModel");
        String provider       = (String) execution.getVariable("config_agentProvider");
        String oldPrompt         = (String) execution.getVariable("config_agentPrompt");
        String oldAgentLanguage  = (String) execution.getVariable("config_agentLanguage");

//        String agentSkillsStr = (String) execution.getVariable("agentSkills");
        ArrayNode skillsArray = mapper.createArrayNode();  // don't rewrite skills
//        if (agentSkillsStr != null && !agentSkillsStr.isEmpty()) {
//            String[] agentSkills = agentSkillsStr.split(",");
//            for (String skill : agentSkills) {
//                skillsArray.add(skill.trim());
//            }
//        }

        String newAgentLanguage  = (String) execution.getVariable("form_agentLanguage");
        String newPrompt         = (String) execution.getVariable("form_agentPrompt");

        if ((newPrompt == null || newPrompt.isEmpty()) && (newAgentLanguage == null || newAgentLanguage.isEmpty())) {
            return;
        }

        if (newAgentLanguage == null || newAgentLanguage.isEmpty()) {
            newAgentLanguage = oldAgentLanguage;
        }
        if (newPrompt == null || newPrompt.isEmpty()) {
            newPrompt = oldPrompt;

        }
        else {
            newPrompt += " Language to use: " + newAgentLanguage;
        }

        upsertAgent(
                agentName,      // name
                provider,
                skillsArray,         // keep the same skills
                model,
                newPrompt
        );

        execution.setVariable("config_agentPrompt", newPrompt);
        execution.setVariable("config_agentLanguage", newAgentLanguage);

        LOGGER.info("AgentUpdateDelegate completed successfully.");
    }

    /**
     * Helper method to do a single PUT upsert to the MindsDB endpoint.
     */
    private void upsertAgent(String agentName,
                             String agentProvider,
                             ArrayNode skills,
                             String model,
                             String promptTemplate) throws Exception {
        String url = mindsdbURL + "/api/projects/mindsdb/agents/" + agentName;

        ObjectNode agent = mapper.createObjectNode();
        agent.put("name", agentName);
        agent.put("model_name", model);
        agent.put("provider", agentProvider);
        agent.put("verbose", true);

        if (skills != null) {
            agent.set("skills", skills);
        }

        // Add params as needed
        ObjectNode params = mapper.createObjectNode();
        params.put("model", model);
        params.put("prompt_template", promptTemplate);

        agent.set("params", params);

        ObjectNode payload = mapper.createObjectNode();
        payload.set("agent", agent);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() == 200 || response.statusCode() == 201) {
            LOGGER.info("Agent '" + agentName + "' updated successfully via PUT.");
        } else {
            throw new RuntimeException("Failed to update agent '" + agentName + "': " + response.body());
        }
    }
}
