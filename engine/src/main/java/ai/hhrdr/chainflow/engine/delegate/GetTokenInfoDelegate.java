package ai.hhrdr.chainflow.engine.delegate;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.JavaDelegate;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONArray;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.logging.Logger;

@Component("getTokenInfoDelegate")
public class GetTokenInfoDelegate implements JavaDelegate {

    @Value("${dexguruapi.url}")
    private String apiURL;

    private static final Logger LOGGER = Logger.getLogger(GetTokenInfoDelegate.class.getName());

    @Override
    public void execute(DelegateExecution execution) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        String tokenAddress = (String) execution.getVariable("form_tokenAddress");
        String messageParseMode = (String) execution.getVariable("message_parseMode");

        // Prepare the JSON payload
        String jsonPayload = "{\"ids\":[\"" + tokenAddress + "\"],\"limit\":1}";

        // Create the POST request with the JSON payload
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiURL + "/v3/tokens"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        try {
            // Send the request and parse the response
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            JSONObject responseObject = new JSONObject(response.body());
            JSONArray dataArray = responseObject.getJSONArray("data");

            if (dataArray.length() > 0) {
                JSONObject tokenData = dataArray.getJSONObject(0);

                // Extract and save token information to execution context
                execution.setVariable("token_info", tokenData.toString());
                execution.setVariable("token_price", tokenData.optDouble("priceUSD", 0.0));

                // Extract and save required information to execution context
                String symbol = tokenData.getJSONArray("symbols").optString(0, "N/A");
                String logoURI = tokenData.getJSONArray("logoURI").optString(0, "");
                String name = tokenData.optString("name", "Unknown Token");
                String network = tokenData.optString("network", "Unknown Network");
                Long decimals = tokenData.getLong("decimals");
                String address = tokenData.getString("address");

                execution.setVariable("token_symbol", symbol);
                execution.setVariable("token_logo", logoURI);
                execution.setVariable("token_name", name);
                execution.setVariable("token_network", network);
                execution.setVariable("token_decimals", decimals);
                execution.setVariable("token_address", address);

                // Build a notification message for the token
                String notificationMessage;
                if (messageParseMode == null) {
                    // If no message parse mode is provided, default to HTML formatting.
                    notificationMessage = buildNotificationMessage(tokenData);
                } else if ("MarkdownV2".equalsIgnoreCase(messageParseMode) || "Markdown".equalsIgnoreCase(messageParseMode)) {
                    notificationMessage = buildNotificationMessageMarkdown(tokenData);
                } else {
                    // Fallback to HTML formatting for any other value
                    notificationMessage = buildNotificationMessage(tokenData);
                }
                execution.setVariable("token_notification_message", notificationMessage);

                LOGGER.info("Notification message saved: " + notificationMessage);
            } else {
                LOGGER.warning("No token data found in the response.");
            }
        } catch (Exception e) {
            LOGGER.severe("Failed to fetch token info. Exception: " + e.getMessage());
            throw e;
        }
    }

    private String buildNotificationMessage(JSONObject tokenData) throws JSONException {
        String name = tokenData.optString("name", "Unknown Token");
        String symbol = tokenData.getJSONArray("symbols").optString(0, "N/A");
        double priceUSD = tokenData.optDouble("priceUSD", 0.0);
        double priceChange24h = tokenData.optDouble("priceUSDChange24h", 0.0) * 100; // Convert to percentage
        double liquidityUSD = tokenData.optDouble("liquidityUSD", 0.0);
        double volume24hUSD = tokenData.optDouble("volume24hUSD", 0.0);

        String priceChangeEmoji = priceChange24h >= 0 ? "📈" : "📉"; // Up or down arrow based on change

        return String.format(
                "💰 <b>%s</b> (%s)\n" + // Token name and symbol
                        "💵 <b>Price:</b> $%.4f %s (24h Change: %.2f%%)\n" + // Price with change indicator
                        "💧 <b>Liquidity:</b> $%.2f\n" + // DEX Liquidity
                        "📊 <b>24h Volume:</b> $%.2f", // DEX Volume
                name, symbol, priceUSD, priceChangeEmoji, priceChange24h, liquidityUSD, volume24hUSD
        );
    }

    private String buildNotificationMessageMarkdown(JSONObject tokenData) throws JSONException {
        String name = tokenData.optString("name", "Unknown Token");
        String symbol = tokenData.getJSONArray("symbols").optString(0, "N/A");
        double priceUSD = tokenData.optDouble("priceUSD", 0.0);
        double priceChange24h = tokenData.optDouble("priceUSDChange24h", 0.0) * 100; // Convert to percentage
        double liquidityUSD = tokenData.optDouble("liquidityUSD", 0.0);
        double volume24hUSD = tokenData.optDouble("volume24hUSD", 0.0);

        String priceChangeEmoji = priceChange24h >= 0 ? "📈" : "📉"; // Up or down arrow based on change

        return String.format(
                "💰 **%s** (%s)\n" +           // Token name and symbol
                        "💵 **Price:** $%.4f %s (24h Change: %.2f%%)\n" + // Price with change indicator
                        "💧 **Liquidity:** $%.2f\n" +    // DEX Liquidity
                        "📊 **24h Volume:** $%.2f",       // DEX Volume
                name, symbol, priceUSD, priceChangeEmoji, priceChange24h, liquidityUSD, volume24hUSD
        );
    }

}
