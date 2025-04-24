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
import java.util.*;
import java.util.logging.Logger;

@Component("getUserInfoDelegate")
public class GetUserInfoDelegate implements JavaDelegate {

    @Value("${api.url}")
    private String apiURL;

    @Value("${api.key}")
    private String apiKey;

    @Value("${application.url}")
    private String applicationUrl;

    private static final Logger LOGGER = Logger.getLogger(GetUserInfoDelegate.class.getName());

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
            JSONObject user = new JSONObject(response.body());

            // Safely retrieve the telegram_user_id as a Long (allowing null if absent/empty)
            Long telegramUserId = null;
            if (user.has("telegram_user_id") && !user.isNull("telegram_user_id")) {
                telegramUserId = user.getLong("telegram_user_id");
            }
            execution.setVariable("telegram_user_id", telegramUserId);

            String userName = null;
            if (user.has("username") && !user.isNull("username")) {
                userName = user.getString("username");
            }
            execution.setVariable("username", userName);

            Boolean isBlock = user.getBoolean("is_block");
            execution.setVariable("isBlock", isBlock);

            String userId = user.getString("id");
            execution.setVariable("user_id", userId);

            String webappUserId = user.getString("webapp_user_id");
            webappUserId = webappUserId.replace("-", "");
            execution.setVariable("webapp_user_id", webappUserId);

            Boolean isAdmin = user.getBoolean("is_admin");
            execution.setVariable("user_is_admin", isAdmin);

            Boolean isPremium = user.getBoolean("is_premium");
            execution.setVariable("user_is_premium", isPremium);

            // Handle the web3_wallets array and convert it to a List<Map<String, Object>>
            JSONArray web3WalletsJson = user.getJSONArray("web3_wallets");
            List<Map<String, Object>> walletList = new ArrayList<>();

            JSONObject firstWallet = null;
            JSONObject internalWallet = null;

            if (web3WalletsJson.length() > 0) {
                for (int i = 0; i < web3WalletsJson.length(); i++) {
                    JSONObject walletJson = web3WalletsJson.getJSONObject(i);

                    // Convert JSONObject to a Map
                    Map<String, Object> walletMap = new HashMap<>();
                    for (Iterator it = walletJson.keys(); it.hasNext(); ) {
                        String key = (String) it.next();
                        walletMap.put(key, walletJson.get(key));
                    }
                    walletList.add(walletMap);

                    // Find the first wallet with network_type "thirdweb_ecosystem"
                    if (firstWallet == null && "thirdweb_ecosystem".equals(walletJson.optString("network_type"))) {
                        firstWallet = walletJson;
                    }
                    if (internalWallet == null && "guru".equals(walletJson.optString("network_type"))) {
                        internalWallet = walletJson;
                    }
                }

                if (firstWallet != null) {
                    String walletAddress = firstWallet.getString("wallet_address");
                    execution.setVariable("wallet_address", walletAddress);
                    LOGGER.info("Set wallet_address to: " + walletAddress);
                } else {
                    LOGGER.warning("No wallets found with network_type 'thirdweb_ecosystem'.");
                }

                if (internalWallet != null) {
                    String walletAddressInternal = internalWallet.getString("wallet_address");
                    execution.setVariable("wallet_address_internal", walletAddressInternal);
                    LOGGER.info("Set wallet_address_internal to: " + walletAddressInternal);
                } else {
                    LOGGER.warning("No wallets found with network_type 'guru'.");
                }


            } else {
                LOGGER.warning("No wallets found in web3_wallets array.");
            }

            // Set the converted List as the process variable for multi-instance subprocess iteration
            execution.setVariable("web3Wallets", walletList);

            String inviteLink = applicationUrl + "?ref=" + userId;
            execution.setVariable("invite_link", inviteLink);

        } catch (Exception e) {
            LOGGER.severe("Failed to get User Info. Exception: " + e.getMessage());
            throw e; // Rethrow to indicate process failure if needed
        }
    }
}
