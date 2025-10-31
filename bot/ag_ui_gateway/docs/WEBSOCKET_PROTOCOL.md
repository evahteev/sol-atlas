# WebSocket Protocol Specification: AG-UI Gateway

**Version:** 1.0  
**Protocol:** AG-UI + Custom Extensions  
**Connection:** WSS (WebSocket Secure)  

---

## Table of Contents

1. [Overview](#overview)
2. [Connection Flow](#connection-flow)
3. [Message Format](#message-format)
4. [Client → Server Events](#client--server-events)
5. [Server → Client Events](#server--client-events)
6. [Error Handling](#error-handling)
7. [Connection Management](#connection-management)
8. [Examples](#examples)

---

## Overview

The AG-UI Gateway WebSocket protocol provides real-time bidirectional communication between clients and the server. It implements the **AG-UI protocol** for agent-user interaction with custom extensions for Luka Bot specific features.

### Endpoints

```
Production: wss://api.your-domain.com/ws/chat
Development: ws://localhost:8000/ws/chat

Task Notifications: wss://api.your-domain.com/ws/tasks
```

### Key Features

- Real-time LLM response streaming
- Tool execution visibility
- Dynamic form rendering (tasks)
- Live task notifications
- Command execution
- Knowledge base search

---

## Connection Flow

### 1. Establish WebSocket Connection

```javascript
const ws = new WebSocket('wss://api.your-domain.com/ws/chat');
```

### 2. Authentication Handshake

**Client sends auth message:**

```json
{
  "type": "auth",
  "token": "guest_abc123..." // or JWT token
}
```

**Server responds with auth success:**

```json
{
  "type": "auth_success",
  "mode": "guest", // or "authenticated"
  "user_id": 123456789, // null for guest
  "permissions": [
    "read:public_kb",
    "chat:ephemeral"
  ],
  "message": "Guest mode - limited features",
  "upgrade_url": "/api/auth/telegram-miniapp",
  "rate_limits": {
    "messages_per_minute": 10,
    "total_messages": 20
  }
}
```

### 3. Ready for Communication

Once authenticated, the client can send and receive AG-UI protocol events.

### 4. Heartbeat (Optional)

```json
// Client → Server
{
  "type": "ping"
}

// Server → Client
{
  "type": "pong",
  "timestamp": "2025-10-18T14:30:00Z"
}
```

---

## Message Format

All messages are JSON objects with a `type` field:

```json
{
  "type": "event_name",
  "field1": "value1",
  "field2": "value2"
}
```

### Base Message Structure

```typescript
interface BaseMessage {
  type: string;
  timestamp?: string; // ISO 8601
  message_id?: string; // Unique message ID
}
```

---

## Client → Server Events

### auth

Authenticate the WebSocket connection.

```json
{
  "type": "auth",
  "token": "guest_abc123..." // or JWT
}
```

---

### user_message

Send a chat message to the AI assistant.

```json
{
  "type": "user_message",
  "message": "Tell me about DeFi lending protocols",
  "thread_id": "thread-abc-123", // optional
  "metadata": {
    "client": "web",
    "version": "1.0.0"
  }
}
```

**Fields:**
- `message` (required): User's text input
- `thread_id` (optional): Thread context for authenticated users
- `metadata` (optional): Additional client info

**Guest Limitations:**
- No `thread_id` (ephemeral chat only)
- Limited to 20 total messages

---

### command

Execute a bot command.

```json
{
  "type": "command",
  "command": "tasks", // start, tasks, search, profile, etc.
  "args": {
    "filter": "inbox",
    "limit": 10
  }
}
```

**Available Commands:**
- `start` - Main menu
- `tasks` - Task management
- `search` - KB search
- `profile` - User profile
- `chat` - Thread management
- `groups` - Group management
- `catalog` - Browse KB catalog

**Guest Access:**
- Only `catalog` and `search` (public KBs) allowed
- Other commands return `UPGRADE_REQUIRED` error

---

### form_submit

Submit a form (task or start form).

```json
{
  "type": "form_submit",
  "form_id": "task-456",
  "values": {
    "amount": "1000",
    "description": "User input",
    "s3_document": "https://cdn.example.com/file.pdf"
  },
  "action": "approve" // button name clicked
}
```

**Fields:**
- `form_id` (required): Task or form ID
- `values` (required): Form field values
- `action` (optional): Action button name

---

### search_kb

Search knowledge base(s).

```json
{
  "type": "search_kb",
  "query": "DeFi lending protocols",
  "kb_ids": ["crypto-kb", "defi-kb"], // empty = search all accessible
  "max_results": 10,
  "search_method": "text" // text, vector, or hybrid
}
```

**Fields:**
- `query` (required): Search query
- `kb_ids` (optional): Specific KBs to search
- `max_results` (optional): Limit results (default: 10)
- `search_method` (optional): Search type (default: "text")

**Guest Access:**
- Only public KBs searchable
- Limited to 10 searches per minute

---

### thread_switch

Switch active thread (authenticated only).

```json
{
  "type": "thread_switch",
  "thread_id": "thread-xyz-789"
}
```

---

### cancel_action

Cancel ongoing action (e.g., stop LLM generation).

```json
{
  "type": "cancel_action",
  "action_id": "msg-123"
}
```

---

## Server → Client Events

### auth_success

Authentication completed successfully.

```json
{
  "type": "auth_success",
  "mode": "authenticated",
  "user_id": 123456789,
  "permissions": [
    "read:public_kb",
    "read:private_kb",
    "execute:workflows",
    "view:tasks"
  ],
  "message": "Authenticated successfully"
}
```

---

### uiContext

Navigation and prompt context synchronized with the Telegram UX. Emitted after authentication, commands, and chat messages.

```json
{
  "type": "uiContext",
  "contextId": "3c7d4d3c-21d6-4ab1-a12a-81e1c5a1c742",
  "timestamp": 1739211145123,
  "activeMode": "start",
  "modes": [
    {"id": "start", "label": "🏠 Start", "emoji": "🏠", "requiresAuth": false, "showInMenu": true},
    {"id": "tasks", "label": "📋 Tasks", "emoji": "📋", "requiresAuth": true, "showInMenu": true, "badgeCount": 3},
    {"id": "profile", "label": "👤 Profile", "emoji": "👤", "requiresAuth": true, "showInMenu": true}
  ],
  "quickPrompts": [
    {"id": "c1e5a90a12f3", "text": "Summarize the latest group updates", "source": "group"},
    {"id": "7dbe0ac44b2f", "text": "Prepare a weekly digest", "source": "generic"}
  ],
  "scopeControls": [
    {"id": "edit_groups", "label": "⚙️ Edit groups", "emoji": "⚙️", "selected": false},
    {"id": "all_sources", "label": "🌐 All sources", "emoji": "🌐", "selected": true},
    {"id": "my_groups", "label": "🎯 Only selected", "emoji": "🎯", "selected": false}
  ],
  "userInfo": {
    "userId": "123456789",
    "displayName": "Maria",
    "language": "en",
    "isGuest": false
  },
  "metadata": {
    "groupCount": 4,
    "taskCount": 3,
    "scope": {
      "source": "all",
      "groupIds": []
    }
  }
}
```

Clients should render navigation buttons, quick prompt chips, and scope toggles directly from this payload.

**Key fields:**
- `modes[].requiresAuth`: Hide or gate menu items for guests.
- `modes[].badgeCount`: Optional counters (e.g., pending tasks).
- `modes[].disabled`: Present when the server recommends disabling the entry.
- `scopeControls[]`: Render ⚙️/🌐/🎯 scope toggles with `selected` state.
- `quickPrompts[]`: Up to three localized shortcuts ordered by relevance.

---

### textStreamDelta

Streaming text chunk from LLM.

```json
{
  "type": "textStreamDelta",
  "delta": "DeFi (Decentralized Finance) refers to...",
  "message_id": "msg-789",
  "metadata": {
    "model": "llama3.2",
    "provider": "ollama"
  }
}
```

**Fields:**
- `delta` (required): Text chunk
- `message_id` (required): Message identifier
- `metadata` (optional): LLM metadata

**Streaming Mode:**
- **Cumulative:** Each delta contains full text so far (OpenAI style)
- **Incremental:** Each delta contains only new text (Ollama style)

*Current implementation: Cumulative (extract delta on client)*

---

### toolInvocation

Tool execution started.

```json
{
  "type": "toolInvocation",
  "tool_id": "tool-123",
  "tool_name": "search_knowledge_base",
  "args": {
    "query": "DeFi protocols",
    "kb_id": "crypto-kb"
  },
  "emoji": "🔍"
}
```

**Fields:**
- `tool_id` (required): Unique tool execution ID
- `tool_name` (required): Tool function name
- `args` (required): Tool arguments
- `emoji` (optional): Visual indicator

**Common Tools:**
- `search_knowledge_base` - 🔍
- `get_youtube_transcript` - 📺
- `execute_task` - 📋
- `get_support_info` - 🎧

---

### toolResult

Tool execution completed.

```json
{
  "type": "toolResult",
  "tool_id": "tool-123",
  "success": true,
  "result": {
    "results": [
      {
        "text": "Aave is a decentralized lending protocol...",
        "score": 0.92,
        "source": "crypto-kb",
        "sender": "CryptoPro",
        "date": "2025-10-15T12:00:00Z",
        "link": "t.me/c/1234567890/12345"
      }
    ],
    "total": 15
  }
}
```

**Fields:**
- `tool_id` (required): Matches toolInvocation
- `success` (required): Boolean
- `result` (required if success): Tool output
- `error` (required if !success): Error message

---

### taskList

Snapshot of Camunda user tasks. Used to populate the task drawer and inline menus; emitted after `/start`, `/tasks`, general chat responses, and whenever a task submission changes the queue.

```json
{
  "type": "taskList",
  "timestamp": 1739211180456,
  "source": "chatbot_start",
  "tasks": [
    {
      "id": "bc7e1f2d-daa4-4c5f-aa8d-98f8f3fdc6f0",
      "name": "Verify knowledge base",
      "status": "pending",
      "createdAt": 1739207600000,
      "dueAt": null,
      "metadata": {
        "processInstanceId": "a1b2c3d4",
        "description": "Review the latest KB sync",
        "assignee": 123456789
      }
    },
    {
      "id": "a1d3c2b5-9087-4a14-8d6b-55a3f6713f8d",
      "name": "Review escalation…",
      "status": "pending",
      "createdAt": 1739205500000,
      "metadata": {
        "processInstanceId": "d4c3b2a1",
        "description": null,
        "assignee": 123456789
      }
    }
  ],
  "pagination": {
    "limit": 2,
    "offset": 0,
    "total": 2
  },
  "metadata": {
    "taskCount": 2
  }
}
```

When there are no pending tasks (and the user is viewing `start` or `tasks`), an empty state is returned:

```json
{
  "type": "taskList",
  "timestamp": 1739211209123,
  "source": "chatbot_start",
  "tasks": [],
  "emptyState": {
    "title": "📋 Your Tasks",
    "message": "✅ No pending tasks"
  }
}
```

---

### formRequest

Request user to fill form (task).

```json
{
  "type": "formRequest",
  "form_id": "task-456",
  "title": "Approve Transfer",
  "description": "Please review and approve this transfer",
  "process_info": {
    "process_id": "proc-789",
    "process_name": "Payment Processing"
  },
  "fields": [
    {
      "type": "text",
      "name": "amount",
      "label": "Amount",
      "value": "1000",
      "required": true,
      "readonly": true
    },
    {
      "type": "text",
      "name": "description",
      "label": "Description",
      "value": "",
      "required": true,
      "readonly": false,
      "placeholder": "Enter description"
    },
    {
      "type": "file",
      "name": "s3_document",
      "label": "Attachment",
      "required": false,
      "accept": "*/*",
      "maxSize": 20971520
    },
    {
      "type": "button",
      "name": "approve",
      "label": "Approve",
      "variant": "primary"
    },
    {
      "type": "button",
      "name": "reject",
      "label": "Reject",
      "variant": "secondary"
    }
  ]
}
```

**Field Types:**
- `text` - Text input
- `textarea` - Multi-line text
- `number` - Numeric input
- `file` - File upload
- `button` - Action button
- `select` - Dropdown (future)
- `checkbox` - Boolean (future)

---

### stateUpdate

Agent state change notification.

```json
{
  "type": "stateUpdate",
  "status": "generating", // or: waiting, tool_executing, complete, error
  "thread_id": "thread-abc-123",
  "metadata": {
    "workflow_id": "proc-789",
    "task_count": 3,
    "message": "Processing your request..."
  }
}
```

**Status Values:**
- `generating` - LLM generating response
- `waiting` - Waiting for user input
- `tool_executing` - Tool is running
- `complete` - Action completed
- `error` - Error occurred

---

### taskNotification

Real-time task notification (from Warehouse WebSocket).

```json
{
  "type": "taskNotification",
  "event": "created", // created, updated, completed, deleted
  "task": {
    "id": "task-456",
    "name": "Approve Transfer",
    "description": "Review payment request",
    "process_id": "proc-789",
    "process_name": "Payment Processing",
    "created": "2025-10-18T14:30:00Z",
    "assignee": "user_123456789"
  }
}
```

**Event Types:**
- `created` - New task assigned
- `updated` - Task modified
- `completed` - Task finished
- `deleted` - Task cancelled

**Action:** Client should fetch task details and render form.

---

### catalogData

Knowledge base catalog data.

```json
{
  "type": "catalogData",
  "catalog": {
    "featured": [
      {
        "id": "crypto-kb",
        "name": "Crypto Signals",
        "icon": "💰",
        "stats": {
          "messages": 15420,
          "contributors": 234
        }
      }
    ],
    "by_category": {
      "crypto": [...],
      "tech": [...]
    },
    "my_kbs": [...],
    "stats": {
      "total_public": 45,
      "total_private": 3
    }
  }
}
```

---

### error

Error occurred during processing.

```json
{
  "type": "error",
  "code": "WORKFLOW_ERROR",
  "message": "Failed to start workflow: chatbot_start",
  "details": {
    "workflow_key": "chatbot_start",
    "reason": "Process definition not found"
  },
  "severity": "error", // error, warning, info
  "recoverable": false
}
```

**Common Error Codes:**
- `UPGRADE_REQUIRED` - Guest needs to authenticate
- `RATE_LIMIT_EXCEEDED` - Too many messages
- `WORKFLOW_ERROR` - Camunda error
- `TOOL_ERROR` - Tool execution failed
- `VALIDATION_ERROR` - Invalid input
- `PERMISSION_DENIED` - No access

---

### messageComplete

Message generation completed.

```json
{
  "type": "messageComplete",
  "message_id": "msg-789",
  "total_length": 1847,
  "metadata": {
    "tokens": 450,
    "duration_ms": 3200,
    "tools_used": ["search_knowledge_base"]
  }
}
```

---

## Error Handling

### WebSocket Close Codes

| Code | Reason | Action |
|------|--------|--------|
| 1000 | Normal closure | None |
| 1008 | Policy violation (invalid auth) | Re-authenticate |
| 1011 | Internal server error | Retry with backoff |
| 4001 | Invalid message format | Fix client |
| 4002 | Rate limit exceeded | Wait and retry |
| 4003 | Permission denied | Check permissions |

### Error Event Format

```json
{
  "type": "error",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many messages. Please slow down.",
  "details": {
    "limit": 10,
    "window": 60,
    "retry_after": 45
  }
}
```

### Client Error Handling

```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  if (event.code === 1008) {
    // Re-authenticate
    authenticate();
  } else if (event.code === 1011) {
    // Retry with exponential backoff
    setTimeout(() => reconnect(), retryDelay);
  }
};
```

---

## Connection Management

### Reconnection Strategy

**Exponential Backoff:**

```javascript
let retryCount = 0;
const maxRetries = 5;
const baseDelay = 1000; // 1 second

function reconnect() {
  if (retryCount >= maxRetries) {
    console.error('Max retries exceeded');
    return;
  }
  
  const delay = baseDelay * Math.pow(2, retryCount);
  retryCount++;
  
  setTimeout(() => {
    console.log(`Reconnecting... (attempt ${retryCount})`);
    connect();
  }, delay);
}
```

### Heartbeat

Keep connection alive with periodic pings:

```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000); // Every 30 seconds
```

### Graceful Shutdown

```javascript
window.addEventListener('beforeunload', () => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.close(1000, 'Client closing');
  }
});
```

---

## Examples

### Example 1: Simple Chat Message

**Client sends:**

```json
{
  "type": "user_message",
  "message": "What is DeFi?"
}
```

**Server streams response:**

```json
// 1. State update
{
  "type": "stateUpdate",
  "status": "generating"
}

// 2. Text chunks
{
  "type": "textStreamDelta",
  "delta": "DeFi",
  "message_id": "msg-001"
}

{
  "type": "textStreamDelta",
  "delta": "DeFi (Decentralized Finance)",
  "message_id": "msg-001"
}

{
  "type": "textStreamDelta",
  "delta": "DeFi (Decentralized Finance) refers to financial services...",
  "message_id": "msg-001"
}

// 3. Complete
{
  "type": "messageComplete",
  "message_id": "msg-001"
}

{
  "type": "stateUpdate",
  "status": "complete"
}
```

---

### Example 2: Chat with KB Search Tool

**Client sends:**

```json
{
  "type": "user_message",
  "message": "Find information about Aave lending rates"
}
```

**Server response:**

```json
// 1. Tool invocation
{
  "type": "toolInvocation",
  "tool_id": "tool-123",
  "tool_name": "search_knowledge_base",
  "args": {
    "query": "Aave lending rates",
    "kb_id": "crypto-kb"
  },
  "emoji": "🔍"
}

// 2. Tool result
{
  "type": "toolResult",
  "tool_id": "tool-123",
  "success": true,
  "result": {
    "results": [
      {
        "text": "Current Aave USDC lending rate: 3.2% APY...",
        "score": 0.95
      }
    ]
  }
}

// 3. Text response
{
  "type": "textStreamDelta",
  "delta": "Based on the latest data, Aave USDC lending rate is...",
  "message_id": "msg-002"
}

// 4. Complete
{
  "type": "messageComplete",
  "message_id": "msg-002"
}
```

---

### Example 3: Task Notification & Form

**Server sends task notification:**

```json
{
  "type": "taskNotification",
  "event": "created",
  "task": {
    "id": "task-456",
    "name": "Approve Transfer",
    "process_id": "proc-789"
  }
}

// Followed by form request
{
  "type": "formRequest",
  "form_id": "task-456",
  "title": "Approve Transfer",
  "fields": [
    {
      "type": "text",
      "name": "amount",
      "value": "1000",
      "readonly": true
    },
    {
      "type": "button",
      "name": "approve",
      "label": "Approve"
    }
  ]
}
```

**Client submits form:**

```json
{
  "type": "form_submit",
  "form_id": "task-456",
  "values": {
    "amount": "1000"
  },
  "action": "approve"
}
```

**Server confirms:**

```json
{
  "type": "stateUpdate",
  "status": "complete",
  "metadata": {
    "message": "Task approved successfully"
  }
}
```

---

### Example 4: Guest Upgrade Flow

**Guest sends message:**

```json
{
  "type": "command",
  "command": "tasks"
}
```

**Server responds with upgrade prompt:**

```json
{
  "type": "error",
  "code": "UPGRADE_REQUIRED",
  "message": "Tasks feature requires authentication. Sign in to continue.",
  "details": {
    "upgrade_url": "/api/auth/telegram-miniapp",
    "feature": "tasks"
  },
  "severity": "info",
  "recoverable": true
}
```

---

## Rate Limiting

### Guest Mode

- 10 messages per minute
- 20 total messages per session
- After limit, receive `UPGRADE_REQUIRED` error

### Authenticated Mode

- 30 messages per minute
- Unlimited total messages

### Rate Limit Error

```json
{
  "type": "error",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many messages. Please wait 45 seconds.",
  "details": {
    "limit": 10,
    "window": 60,
    "retry_after": 45
  }
}
```

---

## Security Considerations

1. **Authentication:** Always verify token before processing messages
2. **Rate Limiting:** Enforce per-connection limits
3. **Validation:** Validate all incoming message schemas
4. **Timeout:** Close idle connections after 30 minutes
5. **Max Message Size:** Limit to 1MB per message

---

## Related Documents

- [API Specification](./API_SPECIFICATION.md)
- [Authentication](./AUTHENTICATION.md)
- [Guest Mode](./GUEST_MODE.md)
- [Data Models](./DATA_MODELS.md)

---

**Version History:**
- v1.0 (2025-10-18): Initial protocol specification
