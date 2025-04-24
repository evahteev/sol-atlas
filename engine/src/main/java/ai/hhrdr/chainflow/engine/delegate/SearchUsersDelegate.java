package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.camunda.bpm.engine.impl.el.FixedValue;
import org.camunda.bpm.engine.impl.el.Expression;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

@Component("searchUsersDelegate")
public class SearchUsersDelegate implements JavaDelegate {

    @Value("${api.url}")
    private String apiURL;

    @Value("${api.key}")
    private String apiKey;

    private Object filterBy; // Can accept FixedValue or Expression
    private Object outputVariableName; // Can accept FixedValue or Expression

    private static final Logger LOGGER = Logger.getLogger(SearchUsersDelegate.class.getName());
    private static final int PAGE_SIZE = 100;

    public void setFilterBy(Object filterBy) {
        this.filterBy = filterBy;
    }

    public void setOutputVariableName(Object outputVariableName) {
        this.outputVariableName = outputVariableName;
    }

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        // Resolve filterBy and outputVariableName based on their actual types
        String filterValue = resolveValue(filterBy, execution);
        String outputVarName = resolveValue(outputVariableName, execution);

        if (outputVarName == null || outputVarName.isEmpty()) {
            outputVarName = "allUsers"; // Default output variable name
        }

        List<String> camundaUserIds = new ArrayList<>();
        int page = 1;
        int totalFetched = 0;

        HttpClient client = HttpClient.newHttpClient();

        try {
            while (true) {
                StringBuilder queryUrlBuilder = new StringBuilder(apiURL + "/api/users/search?page=" + page + "&page_size=" + PAGE_SIZE);
                if (filterValue != null && !filterValue.isEmpty()) {
                    queryUrlBuilder.append("&").append(filterValue);
                }

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(queryUrlBuilder.toString()))
                        .header("Content-Type", "application/json")
                        .header("X-SYS-KEY", apiKey)
                        .GET()
                        .build();

                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
                JSONObject responseObject = new JSONObject(response.body());
                JSONArray usersArray = responseObject.getJSONArray("users");
                int total = responseObject.getInt("total");

                for (int i = 0; i < usersArray.length(); i++) {
                    JSONObject userJson = usersArray.getJSONObject(i);
                    String camundaUserId = userJson.getString("camunda_user_id");
                    camundaUserIds.add(camundaUserId);
                }

                totalFetched += usersArray.length();
                LOGGER.info("Fetched page " + page + ": " + usersArray.length() + " users");

                if (totalFetched >= total) {
                    LOGGER.info("All users fetched. Total: " + totalFetched);
                    break;
                }

                page++;
            }

            execution.setVariable(outputVarName, camundaUserIds);

        } catch (Exception e) {
            LOGGER.severe("Failed to fetch users. Exception: " + e.getMessage());
            throw e;
        }
    }

    private String resolveValue(Object value, DelegateExecution execution) {
        if (value instanceof FixedValue) {
            return (String) ((FixedValue) value).getValue(execution);
        } else if (value instanceof Expression) {
            return (String) ((Expression) value).getValue(execution);
        }
        return null;
    }
}
