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

import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

@Component("UserNotificationListener")
public class UserNotificationListener implements TaskListener {

    private static final Logger LOGGER = LoggerFactory.getLogger(UserNotificationListener.class);

    @Value("${bot.token}")
    private String botToken;

    @Value("${bot.name}")
    private String botName;

    private Expression telegramUserIdExp;
    private Expression telegramThreadIdExp;
    private Expression parseModeExp;
    private Expression sendTaskButtonExp;
    private Expression completeTaskExp;
    private Expression buttonTextExp;
    private Expression buttonLinkExp;

    @Override
    public void notify(DelegateTask delegateTask) {
        try {
            // Retrieve values from expressions
            Long telegramUserId = null;
            if (telegramUserIdExp == null) {
                throw new IllegalArgumentException("telegramUserIdExp must be defined.");
            }
            Object userIdObj = telegramUserIdExp.getValue(delegateTask.getExecution());
            if (userIdObj instanceof Number) {
                telegramUserId = ((Number) userIdObj).longValue();
            } else if (userIdObj != null) {
                throw new IllegalArgumentException("telegramUserIdExp must be a Number (Integer or Long) or null.");
            }

            Long telegramThreadId = null;
            if (telegramThreadIdExp != null) {
                Object telegramThreadIdObj = telegramThreadIdExp.getValue(delegateTask.getExecution());
                if (telegramThreadIdObj instanceof Number) {
                    telegramThreadId = ((Number) telegramThreadIdObj).longValue();
                } else if (telegramThreadIdObj != null) {
                    throw new IllegalArgumentException("telegramThreadIdExp must be a Number (Integer or Long) or null.");
                }
            }

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
                // First convert any **...** markers to placeholders, sanitize, then restore them as single asterisks.
                textToSend = sanitizeTelegramMarkdown(textToSend);
            }

            // Generate the task-specific callback
            String callbackData = "task:" + taskId.replace("-", "");

            // Construct JSON payload
            JSONObject payload = new JSONObject();
            payload.put("chat_id", telegramUserId.toString());
            payload.put("text", textToSend);
            payload.put("parse_mode", parseMode);
            if (telegramThreadId != null) {
                payload.put("message_thread_id", telegramThreadId);  // Only include if not null
            }

            // Build inline keyboard
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

            String url = String.format("https://api.telegram.org/bot%s/sendMessage", botToken);
            int responseCode = sendPayload(url, payload);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                LOGGER.info("Message sent successfully on first attempt.");
            } else {
                // If using Markdown and the message failed, try fallback (plain text)
                LOGGER.warn("Initial send failed (response code: {}). Retrying as plain text fallback.", responseCode);
                // Remove markdown formatting by removing the parse_mode and using original text.
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
            LOGGER.error("Error sending user notification: ", e);
            if (delegateTask.getExecution() != null) {
                delegateTask.getExecution().createIncident(
                        "failedToSendMessage",
                        delegateTask.getExecution().getId(),
                        "Error sending user notification: " + e.getMessage()
                );
            }
        }
    }

    /**
     * This method applies a sanitation similar to your provided JavaScript code.
     * It first replaces any **...** bold markers with placeholders so they won’t be escaped,
     * then sanitizes the markdown by escaping special symbols (except in code blocks and links),
     * and finally restores the bold placeholders as single asterisks.
     */
    private String sanitizeTelegramMarkdown(String input) {
        // Use placeholders that don't contain any special symbols
        final String BOLD_PLACEHOLDER_START = "BOLDSTART";
        final String BOLD_PLACEHOLDER_END = "BOLDEND";

        // Replace any **...** markers with the placeholders.
        String withPlaceholders = input.replaceAll("\\*\\*(.*?)\\*\\*", BOLD_PLACEHOLDER_START + "$1" + BOLD_PLACEHOLDER_END);

        // Sanitize the rest of the markdown.
        String sanitized = sanitizeMarkdown(withPlaceholders);

        // Restore placeholders as single asterisks (Telegram MarkdownV2 expects *bold*).
        return sanitized.replace(BOLD_PLACEHOLDER_START, "*").replace(BOLD_PLACEHOLDER_END, "*");
    }


    /**
     * Sanitize markdown input.
     * - Detects multiline code blocks and escapes backticks inside them.
     * - Leaves single-line code blocks unchanged.
     * - Detects links and escapes special symbols inside the link label.
     * - Escapes all other special symbols.
     *
     * @param input markdown input (possibly invalid)
     * @return sanitized markdown that should be valid for Telegram
     */
    private String sanitizeMarkdown(String input) {
        // Patterns (in Java strings, backslashes are doubled)
        final String MULTILINE_CODE_REGEX = "(?<=\\n|^)```.*\\n?((?:.|\\n)*?)(?:\\n```)";
        final String SINGLE_LINE_CODE_REGEX = "(`.*?`)";
        final String LINK_REGEX = "\\[(.*?)\\]\\((.*?)\\)";
        final String SPECIAL_SYMBOL_REGEX = "([_*\\[\\]()~`>#+\\-=|{}.!])";

        // Combine the patterns with '|' so that each alternative is tried.
        String combinedRegex = MULTILINE_CODE_REGEX + "|" + SINGLE_LINE_CODE_REGEX + "|" + LINK_REGEX + "|" + SPECIAL_SYMBOL_REGEX;
        Pattern pattern = Pattern.compile(combinedRegex, Pattern.DOTALL);
        Matcher matcher = pattern.matcher(input);
        StringBuffer result = new StringBuffer();

        while (matcher.find()) {
            String replacement;
            // Groups:
            // group(1): multiline code block content (inside ```...```)
            // group(2): single-line code block (e.g. `code`)
            // group(3): link label (inside [label](url))
            // group(4): link URL
            // group(5): a special symbol (if none of the above match)
            String multilineCodeContent = matcher.group(1);
            String singleLineCode = matcher.group(2);
            String linkLabel = matcher.group(3);
            String linkUrl = matcher.group(4);
            String specialSymbol = matcher.group(5);

            if (multilineCodeContent != null) {
                // For multiline code blocks, escape backticks inside the code.
                String escapedContent = multilineCodeContent.replace("`", "\\`");
                replacement = matcher.group(0).replace(multilineCodeContent, escapedContent);
            } else if (singleLineCode != null) {
                // Leave single-line code blocks unchanged.
                replacement = singleLineCode;
            } else if (linkLabel != null && linkUrl != null) {
                // Escape special symbols inside the link label.
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
                // For any other special symbol, escape it.
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
     * Helper method that sends the payload to Telegram.
     * Returns the HTTP response code.
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

