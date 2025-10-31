# Luka Bot API Integration Guide for AG-UI/Dojo

## Overview

This guide provides comprehensive instructions for integrating your Luka Bot API (running on `http://localhost:8000`) with the AG-UI/Dojo frontend. Your API is fully AG-UI compatible and supports Server-Sent Events (SSE) streaming.

## API Analysis

Based on your OpenAPI specification, your API provides:

### ✅ **AG-UI Compatible Features**
- **Server-Sent Events (SSE)**: Real-time streaming responses
- **Authentication**: Guest sessions and JWT tokens
- **Agent Endpoints**: `/api/agent/luka` and `/api/copilotkit/luka`
- **Health Checks**: `/api/agent/luka/health` and `/api/agent/luka/info`
- **Password Protection**: Configurable bot access control

### 🔧 **Available Endpoints**

#### Authentication
- `POST /api/auth/guest` - Create guest session
- `POST /api/auth/telegram-miniapp` - Telegram Mini App auth
- `POST /api/auth/refresh` - Refresh JWT tokens

#### Agent Communication
- `POST /api/agent/luka` - Main agent endpoint (SSE streaming)
- `POST /api/copilotkit/luka` - CopilotKit alias
- `GET /api/agent/luka/health` - Agent health check
- `GET /api/agent/luka/info` - Agent information

#### Additional Features
- `GET /api/catalog` - Knowledge base catalog
- `GET /api/profile` - User profile management
- `POST /api/files/upload` - File upload to S3/R2

## Integration Setup

### 1. Environment Configuration

Create a `.env.local` file in your Dojo project:

```bash
# Luka Bot API Configuration
BOT_API_URL=http://localhost:8000
BOT_API_PASSWORD=your_actual_bot_password_here
```

**Important**: Replace `your_actual_bot_password_here` with the actual password configured in your Luka Bot API.

### 2. Authentication Flow

Your API uses a two-step authentication process:

1. **Guest Session Creation**: 
   ```bash
   POST /api/auth/guest
   # Returns: {"token": "guest_...", "token_type": "guest", "expires_in": 3600}
   ```

2. **Agent Requests**: Use the guest token (password handled conversationally):
   ```bash
   POST /api/agent/luka
   Authorization: Bearer guest_...
   # Body: {"messages": [{"role": "user", "content": "Hello!"}]}
   ```

### 3. Request Format

Your API expects this request format:

```json
{
  "messages": [
    {"role": "user", "content": "Hello! Can you help me?"}
  ],
  "user_id": "guest",
  "thread_id": "default",
  "agent": "luka"
}
```

**Note**: The password is handled conversationally. The bot will ask for the password in the chat, and the user provides it in their next message.

### 4. Response Format (SSE Stream)

Your API returns Server-Sent Events:

```
data: {"type":"RUN_STARTED","runId":"run_123","threadId":"default","timestamp":1234567890}

data: {"type":"TEXT_MESSAGE","messageId":"msg_123","content":"Hello! How can I help you?","role":"assistant","timestamp":1234567890}

data: {"type":"RUN_FINISHED","runId":"run_123","threadId":"default","timestamp":1234567890}
```

## Testing Your Integration

### 1. Test Authentication

```bash
# Create guest session
curl -X POST http://localhost:8000/api/auth/guest

# Expected response:
{
  "token": "guest_...",
  "token_type": "guest",
  "expires_in": 3600,
  "permissions": ["read:public_kb", "chat:ephemeral", "search:public_kb"]
}
```

### 2. Test Agent Health

```bash
curl http://localhost:8000/api/agent/luka/health

# Expected response:
{
  "status": "ok",
  "agent": {
    "name": "luka",
    "description": "Community Knowledge Assistant with BPMN workflows",
    "features": ["agentic_chat", "human_in_the_loop", "backend_tool_rendering", ...]
  }
}
```

### 3. Test Agent Communication

```bash
# Get guest token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/guest | jq -r '.token')

# Test agent (password handled conversationally)
curl -X POST http://localhost:8000/api/agent/luka \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "user_id": "guest",
    "thread_id": "test"
  }'

# The bot will respond asking for password, then you can send:
curl -X POST http://localhost:8000/api/agent/luka \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"},
      {"role": "assistant", "content": "This bot is password-protected. Please provide the password to continue."},
      {"role": "user", "content": "your_bot_password"}
    ],
    "user_id": "guest",
    "thread_id": "test"
  }'
```

## Dojo Frontend Integration

### 1. Available Features

Your Luka Bot API supports these AG-UI features in Dojo:

- ✅ **agentic_chat** - Basic conversational AI
- ✅ **human_in_the_loop** - Interactive task workflows  
- ✅ **backend_tool_rendering** - Tool execution visualization
- ✅ **shared_state** - State management between components
- ✅ **tool_based_generative_ui** - Tool-driven UI generation
- ✅ **agentic_generative_ui** - Dynamic UI generation

### 2. Accessing in Dojo

1. **Start Dojo**: `npm run dev`
2. **Navigate to**: `http://localhost:3000/bot-api/feature/agentic_chat`
3. **Test Chat**: Send a message to interact with Luka Bot

### 3. Configuration Files

The integration is configured in:

- **`src/env.ts`**: Environment variables
- **`src/agents.ts`**: Agent configuration
- **`src/agents/bot-api-agent.ts`**: BotApiAgent implementation
- **`src/menu.ts`**: Available features menu

## Troubleshooting

### Common Issues

1. **Password Required Error**
   ```
   "This bot is password-protected. Please provide the password to continue."
   ```
   **Solution**: This is normal! The bot asks for the password conversationally. Simply reply with the password in your next message.

2. **Authentication Failed**
   ```
   "Authentication failed, attempting to re-authenticate..."
   ```
   **Solution**: Check if your API is running on `http://localhost:8000`.

3. **SSE Stream Issues**
   ```
   "No response body reader available"
   ```
   **Solution**: Ensure your API returns proper SSE format with `Accept: text/event-stream`.

### Debug Steps

1. **Check API Health**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify Guest Authentication**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/guest
   ```

3. **Test Agent Endpoint**:
   ```bash
   curl http://localhost:8000/api/agent/luka/health
   ```

4. **Check Dojo Logs**: Look for errors in browser console and terminal.

## Advanced Configuration

### Custom Agent Features

You can extend the BotApiAgent to support additional features:

```typescript
// In src/agents/bot-api-agent.ts
export class BotApiAgent extends AbstractAgent {
  // Add custom methods for your specific features
  async searchKnowledgeBase(query: string) {
    // Implementation for catalog search
  }
  
  async uploadFile(file: File) {
    // Implementation for file upload
  }
}
```

### Environment Variables

```bash
# Required
BOT_API_URL=http://localhost:8000
BOT_API_PASSWORD=your_bot_password

# Optional
BOT_API_USER_ID=custom_user_id
BOT_API_THREAD_ID=custom_thread_id
```

## Security Considerations

1. **Password Protection**: Your bot requires a password - keep it secure
2. **Guest Tokens**: Guest tokens expire in 1 hour (3600 seconds)
3. **JWT Tokens**: Use proper JWT validation for production
4. **CORS**: Ensure your API allows requests from Dojo frontend

## Production Deployment

For production deployment:

1. **Update URLs**: Change `BOT_API_URL` to your production API
2. **Secure Passwords**: Use environment variables for sensitive data
3. **HTTPS**: Use HTTPS for all communications
4. **Rate Limiting**: Implement proper rate limiting
5. **Monitoring**: Set up health checks and monitoring

## Text Streaming & Rendering Requirements

To keep Dojo’s chat UI rendering clean, format every streamed event according to the AG-UI text protocol:

1. **Emit Valid JSON SSE Frames**  
   - Each chunk must be a complete JSON object prefixed by `data: ` and terminated by a blank line.  
   - Example:  
     ```
     data: {"type":"TEXT_MESSAGE","messageId":"msg_1","content":"Hello there!"}
     
     ```

2. **Use the Text Message Event Triplet**  
   - Start each assistant turn with `TEXT_MESSAGE_START`, stream one or more `TEXT_MESSAGE_CONTENT` events (each `delta` is the newly generated slice), and finish with `TEXT_MESSAGE_END`.

3. **Stick to Markdown or Plain Text**  
   - Avoid raw HTML tags (`<div>`, `<p>`, `<span>`, etc.). The frontend escapes HTML, so tags will display literally.  
   - Prefer Markdown for formatting—headings, lists, links, code fences—so Dojo’s markdown components can render them.

4. **Escape Special Characters Before Serializing**  
   - Make sure `<`, `>`, `&`, and quotes are properly escaped in the JSON string.  
   - If the model outputs HTML, convert it to Markdown or strip tags before streaming.

5. **Custom Rich Content**  
   - When you need bespoke layouts, emit a UI/state event (`{"type":"ui","component":...}`) instead of embedding HTML inside text.  
   - Only the `<Video … />` tag is whitelisted for automatic React rendering; everything else should remain Markdown.

6. **Validate SSE Output in Development**  
   - Use `curl` or a lightweight SSE client to confirm the stream is parseable JSON and renders correctly in Dojo.

Following these rules keeps the AG-UI protocol intact and ensures the Dojo components render model responses cleanly without leaking malformed HTML.

## Support

If you encounter issues:

1. Check the API health endpoint
2. Verify authentication flow
3. Test with curl commands
4. Check Dojo browser console for errors
5. Review the AG-UI protocol documentation

Your Luka Bot API is fully AG-UI compatible and ready for integration with Dojo! 🚀
