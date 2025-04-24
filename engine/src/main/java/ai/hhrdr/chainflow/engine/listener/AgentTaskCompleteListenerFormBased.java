package ai.hhrdr.chainflow.engine.listener;

import ai.hhrdr.chainflow.engine.utils.InputSanitizer;
import com.fasterxml.jackson.core.JsonParseException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.camunda.bpm.engine.delegate.BpmnError;
import org.camunda.bpm.engine.delegate.DelegateTask;
import org.camunda.bpm.engine.delegate.Expression;
import org.camunda.bpm.engine.delegate.TaskListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Logger;

@Component("agentTaskListenerFormBased")
public class AgentTaskCompleteListenerFormBased implements TaskListener {

    private static final Logger logger = Logger.getLogger(AgentTaskCompleteListenerFormBased.class.getName());
    private final ObjectMapper mapper = new ObjectMapper();
    private static final String DEFAULT_ANSWER = "AGENT_FAILED";

    @Value("${mindsdb.url}")
    private String mindsdbURL;

    private Expression agentName;
    private Expression systemPrompt;
    private Expression outputVar;
    private Expression formFieldsNames; // New variable for allowed fields

    @Override
    public void notify(DelegateTask delegateTask) {
        logger.info("AgentTaskListener triggered for task: " + delegateTask.getId());

        String agentNameValue = extractStringValue(agentName, delegateTask);
        String systemPromptValue = extractStringValue(systemPrompt, delegateTask);
        String outputVarValue = extractStringValue(outputVar, delegateTask);
        if (outputVarValue == null || outputVarValue.trim().isEmpty()) {
            outputVarValue = agentNameValue + "_answer";
        }
        delegateTask.setVariable(outputVarValue, null);

        String questionValue = InputSanitizer.sanitizeInput(delegateTask.getDescription());
        if (questionValue == null) {
            questionValue = delegateTask.getDescription();
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("task_id", delegateTask.getId());
        payload.put("question", questionValue);
        payload.put("system_prompt", systemPromptValue);

        Map<String, String> message = new HashMap<>();
        message.put("question", questionValue);
        message.put("answer", "");
        payload.put("messages", new Object[]{message});

        String url = mindsdbURL + "/api/projects/mindsdb/agents/" + agentNameValue + "/completions";
        HttpHeaders headers = new HttpHeaders();
        headers.add("Content-Type", "application/json");

        try {
            String jsonPayload = mapper.writeValueAsString(payload);
            HttpEntity<String> requestEntity = new HttpEntity<>(jsonPayload, headers);

            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<Map> response = restTemplate.postForEntity(url, requestEntity, Map.class);

            String agentOutputJson = DEFAULT_ANSWER;
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> responseBody = response.getBody();
                Object messageObj = responseBody.get("message");
                if (messageObj instanceof Map) {
                    Map messageMap = (Map) messageObj;
                    agentOutputJson = (String) messageMap.getOrDefault("content", DEFAULT_ANSWER);
                    agentOutputJson = agentOutputJson.replaceAll("```", "").trim();

                }
            } else {
                logger.severe("Unexpected response from MindsDB: " + response);
                throw new RuntimeException("Unexpected response from MindsDB");
            }

            try {
                String formFieldsNamesValue = extractStringValue(formFieldsNames, delegateTask);
                String[] allowedVariables = {"token_sell", "token_buy", "form_sell_amount", "form_max_slippage_percentage", "form_autoconfirm_swap", "chain_id", "dst_chain_id"};

                if (formFieldsNamesValue != null && !formFieldsNamesValue.trim().isEmpty()) {
                    allowedVariables = formFieldsNamesValue.split(",");
                }

                Map<String, Object> agentResult = mapper.readValue(agentOutputJson, new TypeReference<Map<String, Object>>() {});
                if (agentResult.containsKey("error")) {
                    String errorMessage = agentResult.get("error").toString();
                    delegateTask.setVariable("completion_agent_answer", errorMessage);
                    throw new BpmnError("FORM_COMPLETION_ERROR", errorMessage);
                }

                for (String key : allowedVariables) {
                    if ("form_autoconfirm_swap".equals(key)) {
                        Object existingValue = delegateTask.getVariable("form_autoconfirm_swap");
                        if (existingValue == null) {
                            delegateTask.setVariable("form_autoconfirm_swap", true);
                        }
                    }
                    if (agentResult.containsKey(key)) {
                        delegateTask.setVariable(key, agentResult.get(key));
                    }
                }
                String taskName = delegateTask.getName();
                delegateTask.setVariable("completion_agent_answer",
                        "AI: I started " + taskName + " process with following settings: " + agentResult.toString());
            } catch (JsonParseException e) {
                delegateTask.setVariable("completion_agent_answer", agentOutputJson);
                throw new BpmnError("FORM_COMPLETION_ERROR", "Prompt error");
            }

            delegateTask.complete();

        } catch (Exception e) {
            logger.severe("Error while querying MindsDB: " + e.getMessage());
            throw new RuntimeException("Error while querying MindsDB", e);
        }
    }

    private String extractStringValue(Expression expression, DelegateTask delegateTask) {
        if (expression != null) {
            Object value = expression.getValue(delegateTask.getExecution());
            if (value instanceof String) {
                return (String) value;
            }
        }
        return null;
    }
}
