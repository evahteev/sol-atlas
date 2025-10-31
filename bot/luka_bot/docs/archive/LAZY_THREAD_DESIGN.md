# Lazy Thread Creation - Design Document

## Overview

ChatGPT-style thread creation: threads are only created AFTER the user sends their first message, not when they press "New Thread" or /start.

## Current vs New Behavior

### Current (Eager Creation)
1. User presses `/start` → Thread "Main Chat" created immediately
2. User presses "➕ New Thread" → Thread "Chat 2" created immediately
3. Thread appears in menu before any conversation happens

### New (Lazy Creation)
1. User presses `/start` → No thread, just welcome + example prompts
2. User types first message → Thread created with auto-generated name
3. Thread appears in menu only after first message sent

## Key Design Decisions

### 1. Welcome Prompts
Show random inspiring prompt when user starts conversation:

**Example Prompts:**
- "What would you like to explore today? 🤔"
- "I'm here to help! What's on your mind? 💭"
- "Ask me anything - let's start a conversation! 💬"
- "What can I help you with today? ✨"
- "Ready to chat! What topic interests you? 🚀"
- "Let's dive in! What would you like to discuss? 🌟"
- "I'm all ears! What question do you have? 👂"
- "Fire away! What would you like to know? 🎯"

### 2. Thread Name Generation
Generate meaningful thread name from first message:

**Strategy:**
- Use LLM to summarize first message into 3-5 word title
- Fallback to first N characters if LLM fails
- Examples:
  - "how to learn python" → "Learning Python"
  - "what's the weather in NYC" → "NYC Weather"
  - "explain quantum computing" → "Quantum Computing"
  - "hello" → "General Chat"

### 3. FSM State Management
Track when user is in "pending thread" mode:

```python
class ThreadCreationStates(StatesGroup):
    waiting_for_first_message = State()  # User has no active thread
```

### 4. Reply Keyboard Behavior

**No threads:**
```
┌─────────────────────────────┐
│ ➕ Start New Chat           │
└─────────────────────────────┘
```

**After first message (thread created):**
```
┌─────────────────────────────┐
│ ➕ New Thread               │
├─────────────────────────────┤
│ 💬 Learning Python │ ✏️│🗑️│
└─────────────────────────────┘
```

## Implementation Plan

### Phase 1: Welcome Prompts Service
**File:** `services/welcome_prompts.py`
- Store list of welcome prompts
- Random selection function
- Multi-language support (en, ru, uk)

### Phase 2: Thread Name Generator
**File:** `services/thread_name_generator.py`
- LLM-based name generation
- Fallback to simple truncation
- Max length: 20 characters
- Title case formatting

### Phase 3: Update /start Handler
**File:** `handlers/start.py`
- Remove immediate thread creation
- Show welcome message + random prompt
- Set FSM state to `waiting_for_first_message`
- Show minimal keyboard (just "➕ Start New Chat")

### Phase 4: Update New Thread Button
**File:** `handlers/keyboard_actions.py`
- Remove immediate thread creation
- Show welcome message + random prompt
- Set FSM state to `waiting_for_first_message`
- Clear current active thread pointer

### Phase 5: Update Streaming Handler
**File:** `handlers/streaming_dm.py`
- Check if user has no active thread
- If no thread: create with auto-generated name
- Generate name from first message
- Add thread to keyboard
- Process message normally

### Phase 6: Update /reset Handler
**File:** `handlers/reset.py`
- After reset, set state to `waiting_for_first_message`
- Show minimal keyboard

## User Flows

### Flow 1: Brand New User
1. User: `/start`
2. Bot: "Welcome! What would you like to explore today? 🤔"
   - Keyboard: [➕ Start New Chat]
3. User: "how do I learn python?"
4. Bot: Creates thread "Learning Python", streams response
   - Keyboard: [➕ New Thread] [💬 Learning Python | ✏️ | 🗑️]

### Flow 2: User with Existing Threads
1. User: presses "➕ New Thread"
2. Bot: "Let's dive in! What would you like to discuss? 🌟"
   - Keyboard unchanged (shows existing threads)
3. User: "best pizza recipes"
4. Bot: Creates thread "Best Pizza Recipes", streams response
   - Keyboard: [➕ New Thread] [💬 Best Pizza Recipes | ✏️ | 🗑️] [Learning Python | ✏️ | 🗑️]

### Flow 3: User Resets
1. User: `/reset`
2. Bot: "Reset complete!" + welcome prompt
   - Keyboard: [➕ Start New Chat]
3. User: "hello"
4. Bot: Creates thread "General Chat", streams response

## Edge Cases

### Empty/Short Messages
- "hi" → "General Chat"
- "?" → "Quick Question"
- "..." → "New Chat"

### Non-English Messages
- Use language detection
- Generate name in same language
- Fallback to first N characters

### Failed Name Generation
- Fallback 1: First 20 chars of message
- Fallback 2: "Chat [timestamp]"
- Never fail thread creation

### Multiple Quick Messages
- If user sends 2+ messages before thread creation completes
- Queue them, create thread once
- Process all messages with same thread_id

## Technical Considerations

### Redis Keys
```python
# Track pending thread state
"pending_thread:{user_id}" → "true"

# Store first message for name generation
"pending_message:{user_id}" → "user's first message"
```

### Race Conditions
- Use Redis locks for thread creation
- Ensure only one thread created per "new chat" session

### Performance
- Name generation should be fast (<500ms)
- Don't block message processing
- Generate name async, update thread name after

## Metrics to Track
- Time from /start to first message
- Thread name generation success rate
- User engagement with welcome prompts
- Average messages per thread

## Future Enhancements
- User can edit thread name immediately after creation
- Suggest thread names based on common topics
- Auto-categorize threads (Work, Personal, Research, etc.)
- Rich welcome messages with example questions

