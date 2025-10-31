# Lazy Thread Creation - TODO Checklist

## Phase 1: Core Services (Foundation)

### ✅ TODO 1: Create Welcome Prompts Service
**File:** `services/welcome_prompts.py`
**Dependencies:** None
**Effort:** 30 min

**Tasks:**
- [ ] Create list of 8-10 welcome prompts (en, ru, uk)
- [ ] Add `get_random_prompt(language: str)` function
- [ ] Add emoji variations
- [ ] Export `get_welcome_message(user_id, language)` function

**Output:**
```python
def get_random_welcome_prompt(language: str = "en") -> str:
    """Returns random welcome prompt."""
    
def get_welcome_message(first_name: str, language: str = "en") -> str:
    """Returns full welcome message with prompt."""
```

---

### ✅ TODO 2: Create Thread Name Generator Service
**File:** `services/thread_name_generator.py`
**Dependencies:** None (uses existing llm_service)
**Effort:** 45 min

**Tasks:**
- [ ] Create `generate_thread_name(message: str)` function
- [ ] Use LLM with specific prompt to generate 3-5 word title
- [ ] Add fallback strategies (truncate, timestamp)
- [ ] Add length limits (max 20 chars)
- [ ] Add title case formatting
- [ ] Handle empty/short messages
- [ ] Add caching to avoid regenerating

**Output:**
```python
async def generate_thread_name(message: str, language: str = "en") -> str:
    """Generate meaningful thread name from first message."""
    # Returns: "Learning Python", "NYC Weather", etc.
```

---

## Phase 2: FSM State Management

### ✅ TODO 3: Add FSM States for Thread Creation
**File:** `handlers/keyboard_actions.py` (add to existing states)
**Dependencies:** None
**Effort:** 15 min

**Tasks:**
- [ ] Add `ThreadCreationStates` class with `waiting_for_first_message`
- [ ] Document state meaning
- [ ] Export from handlers module

**Output:**
```python
class ThreadCreationStates(StatesGroup):
    waiting_for_first_message = State()
    # User has no active thread, waiting for first message to create one
```

---

## Phase 3: Keyboard Updates

### ✅ TODO 4: Update Reply Keyboard for Empty State
**File:** `keyboards/threads_menu.py`
**Dependencies:** None
**Effort:** 20 min

**Tasks:**
- [ ] Add `get_empty_state_keyboard()` function
- [ ] Shows only "➕ Start New Chat" button
- [ ] Update placeholder text
- [ ] Add docstring

**Output:**
```python
async def get_empty_state_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard when user has no threads yet."""
    # Shows: [➕ Start New Chat]
```

---

## Phase 4: Handler Updates (Core Logic)

### ✅ TODO 5: Refactor /start Handler
**File:** `handlers/start.py`
**Dependencies:** TODO 1, TODO 3, TODO 4
**Effort:** 30 min

**Tasks:**
- [ ] Remove `thread_service.create_thread()` call
- [ ] Import welcome prompts service
- [ ] Show welcome message with random prompt
- [ ] Set FSM state to `waiting_for_first_message`
- [ ] Show empty state keyboard (if no threads exist)
- [ ] Show normal keyboard (if threads exist from before)
- [ ] Update logging

**Changes:**
```python
# OLD:
thread = await thread_service.create_thread(user_id, "Main Chat")

# NEW:
welcome = get_welcome_message(first_name, "en")
await state.set_state(ThreadCreationStates.waiting_for_first_message)
keyboard = await get_empty_state_keyboard()
```

---

### ✅ TODO 6: Refactor "New Thread" Button Handler
**File:** `handlers/keyboard_actions.py`
**Dependencies:** TODO 1, TODO 3, TODO 4
**Effort:** 30 min

**Tasks:**
- [ ] Remove `thread_service.create_thread()` call
- [ ] Import welcome prompts service
- [ ] Show welcome message with random prompt
- [ ] Set FSM state to `waiting_for_first_message`
- [ ] Clear active thread pointer
- [ ] Keep existing threads visible in keyboard
- [ ] Update logging

**Changes:**
```python
# OLD:
thread = await thread_service.create_thread(user_id)

# NEW:
welcome = get_random_welcome_prompt("en")
await thread_service.clear_active_thread(user_id)  # New method needed
await state.set_state(ThreadCreationStates.waiting_for_first_message)
```

---

### ✅ TODO 7: Update Streaming DM Handler (CRITICAL)
**File:** `handlers/streaming_dm.py`
**Dependencies:** TODO 2, TODO 3
**Effort:** 60 min

**Tasks:**
- [ ] Check FSM state at start of handler
- [ ] If `waiting_for_first_message`: create thread with auto-generated name
- [ ] Call `generate_thread_name()` service
- [ ] Create thread with generated name
- [ ] Set as active thread
- [ ] Clear FSM state
- [ ] Update keyboard to show new thread
- [ ] Continue with normal streaming response
- [ ] Handle race conditions (multiple messages quickly)
- [ ] Add error handling for name generation failures

**Logic Flow:**
```python
# 1. Check state
current_state = await state.get_state()

# 2. If waiting for first message
if current_state == ThreadCreationStates.waiting_for_first_message:
    # Generate name
    thread_name = await generate_thread_name(text)
    
    # Create thread
    thread = await thread_service.create_thread(user_id, thread_name)
    
    # Clear state
    await state.clear()
    
    # Update keyboard
    threads = await thread_service.list_threads(user_id)
    keyboard = await get_threads_keyboard(threads, thread.thread_id)
    await message.answer("✨ Started new chat!", reply_markup=keyboard)

# 3. Continue with normal streaming
# ... existing streaming logic ...
```

---

### ✅ TODO 8: Update /reset Handler
**File:** `handlers/reset.py`
**Dependencies:** TODO 3, TODO 4
**Effort:** 15 min

**Tasks:**
- [ ] After reset, set FSM state to `waiting_for_first_message`
- [ ] Show empty state keyboard
- [ ] Show welcome prompt in reset confirmation
- [ ] Update reset message

**Changes:**
```python
# After clearing everything:
await state.set_state(ThreadCreationStates.waiting_for_first_message)
keyboard = await get_empty_state_keyboard()
```

---

## Phase 5: Thread Service Enhancements

### ✅ TODO 9: Add Clear Active Thread Method
**File:** `services/thread_service.py`
**Dependencies:** None
**Effort:** 10 min

**Tasks:**
- [ ] Add `clear_active_thread(user_id: int)` method
- [ ] Deletes active thread pointer from Redis
- [ ] Used when starting new thread creation flow

**Output:**
```python
async def clear_active_thread(self, user_id: int) -> None:
    """Clear active thread pointer for user."""
    await redis_client.delete(f"user_active_thread:{user_id}")
```

---

## Phase 6: Edge Cases & Polish

### ✅ TODO 10: Handle Empty State Button
**File:** `handlers/keyboard_actions.py`
**Dependencies:** TODO 1, TODO 3
**Effort:** 20 min

**Tasks:**
- [ ] Add handler for "➕ Start New Chat" button
- [ ] Show welcome prompt
- [ ] Set FSM state to `waiting_for_first_message`
- [ ] Keep empty keyboard

**Implementation:**
```python
@router.message(F.text == "➕ Start New Chat")
async def handle_start_new_chat_button(message: Message, state: FSMContext):
    # Same as "New Thread" but for empty state
```

---

### ✅ TODO 11: Handle Race Conditions
**File:** `handlers/streaming_dm.py`
**Dependencies:** TODO 7
**Effort:** 30 min

**Tasks:**
- [ ] Use Redis lock when creating thread
- [ ] Ensure only one thread created per session
- [ ] Queue subsequent messages if thread creation in progress
- [ ] Handle lock timeout

**Implementation:**
```python
# Use Redis lock
lock_key = f"thread_creation_lock:{user_id}"
async with redis_lock(lock_key, timeout=5):
    # Create thread safely
```

---

### ✅ TODO 12: Update /chats Handler
**File:** `handlers/chats.py`
**Dependencies:** None
**Effort:** 10 min

**Tasks:**
- [ ] Handle case when user has no threads
- [ ] Show helpful message: "Start chatting to create your first thread!"
- [ ] Don't show empty inline keyboard

---

## Phase 7: Testing & Validation

### ✅ TODO 13: Test User Flow - New User
**Manual Testing**
**Dependencies:** All above
**Effort:** 20 min

**Test Cases:**
- [ ] New user types /start → sees welcome prompt, empty keyboard
- [ ] User types first message → thread created with good name
- [ ] Thread appears in keyboard with 💬 indicator
- [ ] Second message goes to same thread
- [ ] Thread name makes sense

---

### ✅ TODO 14: Test User Flow - Existing User
**Manual Testing**
**Dependencies:** All above
**Effort:** 20 min

**Test Cases:**
- [ ] User with threads presses "New Thread"
- [ ] Sees welcome prompt, existing threads still visible
- [ ] Types message → new thread created and appears
- [ ] Can switch back to old threads
- [ ] Active indicator moves correctly

---

### ✅ TODO 15: Test Edge Cases
**Manual Testing**
**Dependencies:** All above
**Effort:** 30 min

**Test Cases:**
- [ ] Very short message ("hi") → reasonable name
- [ ] Very long message → name truncated properly
- [ ] Non-English message → name generated correctly
- [ ] Empty message → fallback name used
- [ ] Multiple quick messages → only one thread created
- [ ] /reset → returns to empty state properly

---

## Summary

**Total TODOs:** 15
**Estimated Total Effort:** ~6 hours
**Critical Path:** TODO 1 → 2 → 3 → 7 (core functionality)

**Priority Order:**
1. TODO 1, 2, 3, 4 (foundation) - 2 hours
2. TODO 5, 6, 7 (core logic) - 2 hours
3. TODO 8, 9, 10, 11, 12 (polish) - 1.5 hours
4. TODO 13, 14, 15 (testing) - 1 hour

**Can Start Immediately:** TODO 1, TODO 2, TODO 3, TODO 4

**Blocking Others:** TODO 7 is critical - everything depends on it working correctly

