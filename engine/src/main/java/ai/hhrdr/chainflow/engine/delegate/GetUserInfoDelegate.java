package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.json.JSONArray;
import org.json.JSONObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.logging.Logger;


@Component("getUserInfoDelegate")
public class GetUserInfoDelegate implements JavaDelegate {

    @Value("${api.url}")
    private String apiURL;

    @Value("${api.key}")
    private String apiKey;

    @Value("${bot.name}")
    private String botName;

    private static final Logger LOGGER = Logger.getLogger(AddEventDelegate.class.getName());

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        String camundaUserId = (String) execution.getVariable("camunda_user_id");

        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiURL + "/api/users?camunda_user_id=" + camundaUserId))
                .header("Content-Type", "application/json")
                .header("X-SYS-KEY", apiKey) // Ensure your API key is correctly set up for authorization
                .GET()
                .build();

        try {
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            // Assuming the response body contains a JSON object
            JSONObject user = new JSONObject(response.body());
            Long telegramUserId = user.getLong("telegram_user_id");
            execution.setVariable("telegram_user_id", telegramUserId);
            String userId = user.getString("id");
            execution.setVariable("user_id", userId);
            Boolean isAdmin = user.getBoolean("is_admin");
            execution.setVariable("user_is_admin", isAdmin);
            Boolean isPremium = user.getBoolean("is_premium");
            execution.setVariable("user_is_premium", isPremium);
            // Handle the web3_wallets array
            JSONArray web3Wallets = user.getJSONArray("web3_wallets");
            if (web3Wallets.length() > 0) {
                // Get the last wallet in the array
                JSONObject lastWallet = web3Wallets.getJSONObject(web3Wallets.length() - 1);
                String walletAddress = lastWallet.getString("wallet_address");
                execution.setVariable("wallet_address", walletAddress);
                LOGGER.info("Set wallet_address to: " + walletAddress);
            } else {
                LOGGER.warning("No wallets found in web3_wallets array.");
            }
            // Create the JSON object for invite_ref and encode it to Base64
            String ref = "ref-" + userId;
            // remove all hyphens
            ref = ref.replace("-", "");
            String inviteLink = "https://t.me/" + botName + "?start=" + ref;
            execution.setVariable("invite_link", inviteLink);

        } catch (Exception e) {
            LOGGER.severe("Failed get User Info. Exception: " + e.getMessage());
            throw e; // Rethrow if you want to indicate failure in the process
        }
    }



}
