package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

// Delegate for unblocking the user and saving the Blofin account
@Component("UnblockUserDelegate")
public class UnblockUserDelegate implements JavaDelegate {

    private static final Logger LOGGER = LoggerFactory.getLogger(UnblockUserDelegate.class);

    @Value("${api.url}")
    private String apiURL;

    @Value("${api.key}")
    private String apiKey;

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        Long blofinUid = (Long) execution.getVariable("form_bloFinUID");
        String camundaUserId = (String) execution.getVariable("camunda_user_id");

        if (camundaUserId == null) {
            LOGGER.error("User ID is missing in process variables.");
            return;
        }

        String url = apiURL + "/api/users";
        URL obj = new URL(url);
        HttpURLConnection connection = (HttpURLConnection) obj.openConnection();

        // Set up connection properties
        connection.setRequestMethod("PUT");
        connection.setRequestProperty("Content-Type", "application/json; utf-8");
        connection.setRequestProperty("X-SYS-KEY", apiKey);
        connection.setDoOutput(true);

        // Create JSON body
        String jsonInputString;
        if (blofinUid != null) {
            jsonInputString = String.format(
                    "{\"camunda_user_id\": \"%s\", \"is_block\": false, \"blofin_user_id\": \"%d\"}",
                    camundaUserId, blofinUid
            );
        } else {
            jsonInputString = String.format(
                    "{\"camunda_user_id\": \"%s\", \"is_block\": false}",
                    camundaUserId
            );
        }

        // Write JSON body to request
        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = jsonInputString.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        // Check response code
        int responseCode = connection.getResponseCode();
        if (responseCode == HttpURLConnection.HTTP_OK) {
            LOGGER.info("User unblocked and Blofin account saved successfully.");
            execution.setVariable("isBlock", false);
        } else {
            LOGGER.error("Failed to update user information. Response code: " + responseCode);
            throw new RuntimeException("Failed to update user information.");
        }
    }
}
