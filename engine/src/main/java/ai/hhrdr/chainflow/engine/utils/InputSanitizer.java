package ai.hhrdr.chainflow.engine.utils;

public class InputSanitizer {

    /**
     * Sanitizes user input to reduce the risk of SQL injection attacks.
     * Replaces dangerous characters and patterns.
     *
     * @param userInput The user-supplied input.
     * @return The sanitized input string.
     */
    public static String sanitizeInput(String userInput) {
        if (userInput == null || userInput.isEmpty()) {
            return userInput;
        }

        // Replace single and double quotes
        String sanitizedInput = userInput.replace("'", " ").replace("\"", " ");

        // Remove SQL comment markers
        sanitizedInput = sanitizedInput.replaceAll("(?i)(--|#|/\\*.*?\\*/)", " ");

        // Replace semicolons, which end queries
        sanitizedInput = sanitizedInput.replace(";", " ");

        // Remove parentheses to prevent subqueries
        sanitizedInput = sanitizedInput.replace("(", " ").replace(")", " ");

        // Replace other dangerous SQL operators and keywords
        String[] dangerousPatterns = {
                "\\bUNION\\b", "\\bSELECT\\b", "\\bINSERT\\b", "\\bUPDATE\\b", "\\bDELETE\\b",
                "\\bDROP\\b", "\\bCREATE\\b", "\\bALTER\\b", "\\bEXEC\\b", "\\bEXECUTE\\b",
                "\\bOR\\b", "\\bAND\\b", "\\bLIKE\\b", "\\bIN\\b", "\\bEXISTS\\b",
                "--", ";", "\\bWHERE\\b", "\\bFROM\\b"
        };

        for (String pattern : dangerousPatterns) {
            sanitizedInput = sanitizedInput.replaceAll("(?i)" + pattern, "");
        }

        // Collapse multiple spaces into a single space
        sanitizedInput = sanitizedInput.replaceAll("\\s+", " ");

        // Trim leading and trailing whitespace
        sanitizedInput = sanitizedInput.trim();

        return sanitizedInput;
    }
}
