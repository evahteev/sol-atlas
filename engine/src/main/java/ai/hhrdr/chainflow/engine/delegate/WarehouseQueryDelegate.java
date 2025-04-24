package ai.hhrdr.chainflow.engine.delegate;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.beans.factory.annotation.Value;

import java.util.List;
import java.util.Map;

@Component("warehouseQueryDelegate")
public class WarehouseQueryDelegate implements JavaDelegate {

    private static final Logger logger = LoggerFactory.getLogger(WarehouseQueryDelegate.class.getName());
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${warehouse.url}")
    private String warehouseUrl;


    @Value("${warehouse.key}")
    private String auth_token;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Retrieve process variables
        String queryId = (String) execution.getVariable("query_id");
        String parametersJson = (String) execution.getVariable("parameters");

        if (warehouseUrl == null || queryId == null || auth_token == null) {
            throw new IllegalArgumentException("Missing required process variables: warehouse_url, query_id, or auth_token");
        }
        Map<String, Object> parameters = objectMapper.readValue(parametersJson, new TypeReference<Map<String, Object>>() {});

        parameters.put("max_age", 10);

        String url = warehouseUrl + "/api/queries/" + queryId + "/results";
        logger.info("Querying Warehouse API at: " + url);

        // Prepare headers
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", auth_token);
        headers.set("Content-Type", "application/json");

        // Prepare payload
        Map<String, Object> payload = parameters;
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

        RestTemplate restTemplate = new RestTemplate();
        boolean retry = true;
        int retryCount = 0;
        int maxRetries = 5;

        while (retry && retryCount < maxRetries) {
            try {
                ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
                if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                    Map<String, Object> responseBody = response.getBody();
                    if (responseBody.containsKey("job")) {
                        logger.info("Query is processing, retrying... (Attempt " + (retryCount + 1) + "/" + maxRetries + ")");
                        Thread.sleep(3000); // Wait before retrying
                        retryCount++;
                    } else {
                        // Successfully received data
                        Map<String, Object> queryResult = (Map<String, Object>) responseBody.get("query_result");
                        Map<String, Object> data = (Map<String, Object>) queryResult.get("data");
                        List<Map<String, Object>> rows = (List<Map<String, Object>>) data.get("rows");
                        execution.setVariable("warehouse_query_result", rows);
                        retry = false;
                    }
                } else {
                    throw new RuntimeException("Unexpected response from Warehouse API: " + response.getStatusCode());
                }
            } catch (Exception e) {
                logger.error("Error querying warehouse: ", e);
                throw new RuntimeException("Error while querying warehouse", e);
            }
        }
    }
}
