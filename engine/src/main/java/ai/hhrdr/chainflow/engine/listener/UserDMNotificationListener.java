package ai.hhrdr.chainflow.engine.listener;

import org.camunda.bpm.engine.delegate.DelegateTask;
import org.camunda.bpm.engine.delegate.Expression;
import org.camunda.bpm.engine.delegate.TaskListener;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component("UserDMNotificationListener")
public class UserDMNotificationListener implements TaskListener {

    private static final Logger LOGGER = LoggerFactory.getLogger(UserDMNotificationListener.class);

    @Value("${bot.token}")
    private String botToken;

    @Value("${bot.name}")
    private String botName;

    @Value("${api.url}")
    private String apiURL;

    @Value("${api.key}")
    private String apiKey;

    // We no longer need a thread expression for DMs.
    private Expression parseModeExp;
    private Expression sendTaskButtonExp;
    private Expression completeTaskExp;
    private Expression buttonTextExp;
    private Expression buttonLinkExp;
    private Expression telegramUserIdExp;
    private Expression telegramThreadIdExp;

    @Override
    public void notify(DelegateTask delegateTask) {
        try {
            // 1. Retrieve camunda user id from process variables.
            Object camundaUserIdObj = delegateTask.getExecution().getVariable("camunda_user_id");
            if (camundaUserIdObj == null) {
                throw new IllegalArgumentException("Process variable 'camunda_user_id' must be defined.");
            }
            String camundaUserId = camundaUserIdObj.toString();

            // 2. Retrieve the Telegram user id either from the injected expression or by calling your API.
            Long telegramUserId = null;
            if (telegramUserIdExp != null) {
                Object telegramUserIdObj = telegramUserIdExp.getValue(delegateTask.getExecution());
                if (telegramUserIdObj != null) {
                    try {
                        telegramUserId = Long.parseLong(telegramUserIdObj.toString());
                    } catch (NumberFormatException e) {
                        LOGGER.warn("Invalid telegram user id format from expression: {}. Falling back to API.", telegramUserIdObj);
                    }
                }
            }
            if (telegramUserId == null) {
                try {
                    telegramUserId = retrieveTelegramUserId(camundaUserId);
                } catch (Exception e) {
                    // Log the issue and complete the task if the telegram id is not available.
                    LOGGER.warn("Could not retrieve telegram user id for camunda user {}. Exception: {}. Completing task.",
                            camundaUserId, e.getMessage());
                    delegateTask.complete();
                    return;
                }
            }

            // In case the API returns a null value or similar
            if (telegramUserId == null) {
                LOGGER.warn("Telegram user id is null for camunda user {}. Completing task without sending DM.", camundaUserId);
                delegateTask.complete();
                return;
            }

            // 3. Get additional parameters from expressions.
            String parseMode = (String) parseModeExp.getValue(delegateTask.getExecution());
            Boolean sendTaskButton = (Boolean) sendTaskButtonExp.getValue(delegateTask.getExecution());
            Boolean completeTask = (Boolean) completeTaskExp.getValue(delegateTask.getExecution());
            String buttonText = (String) buttonTextExp.getValue(delegateTask.getExecution());
            String buttonLink = (String) buttonLinkExp.getValue(delegateTask.getExecution());

            String taskId = delegateTask.getId();
            String textToSend = delegateTask.getDescription();
            String originalText = textToSend;
            if (textToSend == null) {
                LOGGER.warn("Task {} has no message to send. Skipping notification.", taskId);
                return;
            }

            if ("MarkdownV2".equalsIgnoreCase(parseMode) || "Markdown".equalsIgnoreCase(parseMode)) {
                textToSend = sanitizeTelegramMarkdown(textToSend);
            }

            // Generate a task-specific callback data if needed.
            String callbackData = "task:" + taskId.replace("-", "");

            // 4. Build JSON payload for Telegram.
            JSONObject payload = new JSONObject();
            payload.put("chat_id", telegramUserId.toString());
            payload.put("text", textToSend);
            payload.put("parse_mode", parseMode);
            // No thread id is used in a DM.

            // Optionally include thread id if provided via injected variable.
            if (telegramThreadIdExp != null) {
                Object threadIdObj = telegramThreadIdExp.getValue(delegateTask.getExecution());
                if (threadIdObj != null) {
                    try {
                        Long threadId = Long.parseLong(threadIdObj.toString());
                        payload.put("message_thread_id", threadId);
                    } catch (NumberFormatException e) {
                        LOGGER.warn("Invalid telegram thread id format from expression: {}. Skipping thread id.", threadIdObj);
                    }
                }
            }


            // Optionally add inline keyboard buttons.
            JSONArray inlineKeyboard = new JSONArray();
            JSONArray buttonRow = new JSONArray();
            if (Boolean.TRUE.equals(sendTaskButton)) {
                JSONObject taskButton = new JSONObject();
                taskButton.put("text", delegateTask.getName());
                taskButton.put("callback_data", callbackData);
                buttonRow.put(taskButton);
            }
            if (buttonText != null && buttonLink != null) {
                JSONObject additionalButton = new JSONObject();
                additionalButton.put("text", buttonText);
                if (buttonLink.startsWith("http")) {
                    additionalButton.put("url", buttonLink);
                } else {
                    additionalButton.put("callback_data", buttonLink);
                }
                buttonRow.put(additionalButton);
            }
            if (buttonRow.length() > 0) {
                inlineKeyboard.put(buttonRow);
                JSONObject replyMarkup = new JSONObject();
                replyMarkup.put("inline_keyboard", inlineKeyboard);
                payload.put("reply_markup", replyMarkup);
            }

            // 5. Send the message to Telegram.
            String url = String.format("https://api.telegram.org/bot%s/sendMessage", botToken);
            int responseCode = sendPayload(url, payload);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                LOGGER.info("Message sent successfully on first attempt.");
            } else {
                // If sending with markdown fails, fall back to plain text.
                LOGGER.warn("Initial send failed (response code: {}). Retrying as plain text fallback.", responseCode);
                payload.remove("parse_mode");
                payload.put("text", originalText);
                int fallbackResponseCode = sendPayload(url, payload);
                if (fallbackResponseCode == HttpURLConnection.HTTP_OK) {
                    LOGGER.info("Fallback message sent successfully.");
                } else {
                    String errorMessage = String.format("Fallback send failed with response code: %d", fallbackResponseCode);
                    LOGGER.error(errorMessage);
                    throw new Exception(errorMessage);
                }
            }

            if (Boolean.TRUE.equals(completeTask)) {
                delegateTask.complete();
                LOGGER.info("Task {} automatically completed after notification.", taskId);
            }
        } catch (Exception e) {
            LOGGER.error("Error sending DM notification: ", e);
            delegateTask.complete();
            // don't raise an incident if cannot send the message
//             if (delegateTask.getExecution() != null) {
//                 delegateTask.getExecution().createIncident(
//                         "failedToSendMessage",
//                         delegateTask.getExecution().getId(),
//                         "Error sending DM notification: " + e.getMessage()
//                 );
//             }
        }
    }

    /**
     * Retrieves the Telegram user id by calling your API with the given Camunda user id.
     *
     * @param camundaUserId the Camunda user id from the process execution
     * @return the Telegram user id as a Long
     * @throws Exception if the API call fails or the response is invalid
     */
    private Long retrieveTelegramUserId(String camundaUserId) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        String requestUrl = apiURL + "/api/users?camunda_user_id=" + camundaUserId;
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(requestUrl))
                .header("Content-Type", "application/json")
                .header("X-SYS-KEY", apiKey)
                .GET()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new Exception("Failed to retrieve user info. HTTP error code: " + response.statusCode());
        }
        JSONObject user = new JSONObject(response.body());
        return user.getLong("telegram_user_id");
    }

    /**
     * Sanitize the Telegram markdown by temporarily replacing **...** markers and later restoring them as single asterisks.
     */
    private String sanitizeTelegramMarkdown(String input) {
        final String BOLD_PLACEHOLDER_START = "BOLDSTART";
        final String BOLD_PLACEHOLDER_END = "BOLDEND";

        // Replace any **...** markers with placeholders.
        String withPlaceholders = input.replaceAll("\\*\\*(.*?)\\*\\*", BOLD_PLACEHOLDER_START + "$1" + BOLD_PLACEHOLDER_END);

        // Sanitize the markdown.
        String sanitized = sanitizeMarkdown(withPlaceholders);

        // Restore placeholders as single asterisks.
        return sanitized.replace(BOLD_PLACEHOLDER_START, "*").replace(BOLD_PLACEHOLDER_END, "*");
    }

    /**
     * Escapes special markdown characters while preserving code blocks and links.
     */
    private String sanitizeMarkdown(String input) {
        final String MULTILINE_CODE_REGEX = "(?<=\\n|^)```.*\\n?((?:.|\\n)*?)(?:\\n```)";
        final String SINGLE_LINE_CODE_REGEX = "(`.*?`)";
        final String LINK_REGEX = "\\[(.*?)\\]\\((.*?)\\)";
        final String SPECIAL_SYMBOL_REGEX = "([_*\\[\\]()~`>#+\\-=|{}.!])";

        String combinedRegex = MULTILINE_CODE_REGEX + "|" + SINGLE_LINE_CODE_REGEX + "|" + LINK_REGEX + "|" + SPECIAL_SYMBOL_REGEX;
        Pattern pattern = Pattern.compile(combinedRegex, Pattern.DOTALL);
        Matcher matcher = pattern.matcher(input);
        StringBuffer result = new StringBuffer();

        while (matcher.find()) {
            String replacement;
            String multilineCodeContent = matcher.group(1);
            String singleLineCode = matcher.group(2);
            String linkLabel = matcher.group(3);
            String linkUrl = matcher.group(4);
            String specialSymbol = matcher.group(5);

            if (multilineCodeContent != null) {
                String escapedContent = multilineCodeContent.replace("`", "\\`");
                replacement = matcher.group(0).replace(multilineCodeContent, escapedContent);
            } else if (singleLineCode != null) {
                replacement = singleLineCode;
            } else if (linkLabel != null && linkUrl != null) {
                Pattern specialPattern = Pattern.compile(SPECIAL_SYMBOL_REGEX);
                Matcher specialMatcher = specialPattern.matcher(linkLabel);
                StringBuffer sbLink = new StringBuffer();
                while (specialMatcher.find()) {
                    specialMatcher.appendReplacement(sbLink, "\\\\" + specialMatcher.group(1));
                }
                specialMatcher.appendTail(sbLink);
                String escapedLinkLabel = sbLink.toString();
                replacement = matcher.group(0).replace(linkLabel, escapedLinkLabel);
            } else if (specialSymbol != null) {
                replacement = "\\" + specialSymbol;
            } else {
                replacement = matcher.group(0);
            }
            matcher.appendReplacement(result, Matcher.quoteReplacement(replacement));
        }
        matcher.appendTail(result);
        return result.toString();
    }

    /**
     * Sends the JSON payload to Telegram and returns the HTTP response code.
     */
    private int sendPayload(String urlString, JSONObject payload) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json; utf-8");
        connection.setDoOutput(true);

        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = payload.toString().getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        int responseCode = connection.getResponseCode();
        String responseBody = "";
        InputStream inputStream = (responseCode >= 200 && responseCode < 300)
                ? connection.getInputStream() : connection.getErrorStream();
        if (inputStream != null) {
            try (BufferedReader in = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = in.readLine()) != null) {
                    response.append(line);
                }
                responseBody = response.toString();
            }
        }
        LOGGER.info("Telegram response (code {}): {}", responseCode, responseBody);
        return responseCode;
    }
}
