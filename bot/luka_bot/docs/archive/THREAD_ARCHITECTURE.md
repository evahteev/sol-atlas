# Thread Architecture - Unified Conversation Model

## Overview

The **Thread** model is the universal conversation model for the Luka bot, supporting DMs, group chats, and topic-based conversations with a unified architecture.

All conversation configuration (language, LLM settings, tools, knowledge bases) is stored in the Thread, while `GroupLink` acts as a lightweight many-to-many relationship tracker.

---

## Architecture Principles

### 1. **Thread as Source of Truth**
- All conversation configuration stored in Thread
- GroupLink just links users to threads
- One Thread per conversation context

### 2. **Separation of Concerns**
```
Thread (group_123)        ← Conversation config, KB, LLM settings
    ↑
    ├─ GroupLink (user_1 → group_123)  ← User access
    ├─ GroupLink (user_2 → group_123)
    └─ GroupLink (user_3 → group_123)

GroupSettings (group_123) ← Moderation rules, filters (separate from conversation)
    ↓
UserReputation (user_1, group_123)  ← Per-user reputation in group
UserReputation (user_2, group_123)
UserReputation (user_3, group_123)
```

**Key Design**:
- **Thread**: Conversation configuration (what bot says, tools, KB)
- **GroupSettings**: Moderation rules (what bot moderates, filters)
- **UserReputation**: Per-user metrics (points, violations, achievements)

### 3. **Thread Types**
- `dm`: Personal user threads
- `group`: Group conversation threads
- `topic`: Topic/supergroup forum threads

### 4. **Moderation Models** (New in v1.0)
- `GroupSettings`: Per-group moderation configuration (filters, thresholds)
- `UserReputation`: Per-user reputation tracking in groups (points, violations)
- See `MODERATION_SYSTEM.md` for details

---

## Thread Model Fields

```python
@dataclass
class Thread:
    # Identity
    thread_id: str              # "user_123", "group_-456", "group_-456_topic_789"
    owner_id: int               # User who owns/created
    name: str                   # Display name
    thread_type: str            # "dm", "group", "topic"
    
    # Group/topic references
    group_id: Optional[int]     # Telegram group ID (for group/topic threads)
    topic_id: Optional[int]     # Telegram message_thread_id (for topic threads)
    
    # Language & Localization
    language: str               # "en", "ru", etc.
    
    # Agent Customization
    agent_name: Optional[str]           # Custom agent name
    agent_description: Optional[str]    # Agent description
    
    # LLM Settings
    llm_provider: Optional[str]         # "ollama", "openai", etc.
    model_name: Optional[str]           # Model name
    system_prompt: Optional[str]        # Custom personality
    
    # Tool Configuration
    enabled_tools: list[str]            # Whitelist (empty = all enabled)
    disabled_tools: list[str]           # Blacklist
    
    # Knowledge Base
    knowledge_bases: list[str]          # KB indices (e.g., ["tg-kb-group-123"])
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_active: bool
    
    # Camunda (workflow integration)
    process_instance_id: Optional[str]
    active_workflows: list[str]
```

---

## Thread ID Conventions

### DM Threads
```python
thread_id = str(uuid.uuid4())  # Random UUID
# Example: "550e8400-e29b-41d4-a716-446655440000"
```

### Group Threads
```python
thread_id = f"group_{group_id}"
# Example: "group_-1001234567890"
```

### Topic Threads
```python
thread_id = f"group_{group_id}_topic_{topic_id}"
# Example: "group_-1001234567890_topic_42"
```

---

## GroupLink Model (Simplified)

```python
@dataclass
class GroupLink:
    user_id: int          # User ID
    group_id: int         # Group ID
    thread_id: str        # Reference to Thread
    user_role: str        # "member", "admin", "owner"
    created_at: datetime
    updated_at: datetime
    is_active: bool       # Bot removed or user left
```

**Purpose**: Lightweight many-to-many mapping between users and groups.

**What it does NOT store**:
- ❌ KB index (stored in Thread.knowledge_bases)
- ❌ Language (stored in Thread.language)
- ❌ Group title/username (transient, fetched from Telegram API)
- ❌ Any configuration (stored in Thread)

---

## Service Layer Updates

### ThreadService

New methods for groups/topics:

```python
# Group threads
async def get_group_thread(group_id: int) -> Optional[Thread]
async def create_group_thread(group_id, group_title, owner_id, language="en", **kwargs) -> Thread

# Topic threads
async def get_topic_thread(group_id: int, topic_id: int) -> Optional[Thread]
async def create_topic_thread(group_id, topic_id, topic_name, owner_id, **kwargs) -> Thread

# Helper methods
@staticmethod
def _get_group_thread_id(group_id: int) -> str
@staticmethod
def _get_topic_thread_id(group_id: int, topic_id: int) -> str
```

### GroupService

Updated methods now delegate to ThreadService:

```python
# Language (now from Thread)
async def get_group_language(group_id: int) -> str
    # Returns thread.language

async def update_group_language(group_id: int, language: str) -> bool
    # Updates thread.language

# KB Index (now from Thread)
async def get_group_kb_index(group_id: int) -> Optional[str]
    # Returns thread.knowledge_bases[0]

# Group Link Creation
async def create_group_link(user_id, group_id, group_title, language="en", user_role="member") -> GroupLink
    # 1. Ensures Thread exists (creates if missing)
    # 2. Creates GroupLink with thread_id reference
```

---

## Data Flow Examples

### Example 1: Bot Added to Group

```python
# 1. Create Thread
thread = await thread_service.create_group_thread(
    group_id=-1001234567890,
    group_title="Crypto Traders",
    owner_id=user_id,
    language="en"
)
# Creates Thread with:
#   thread_id = "group_-1001234567890"
#   language = "en"
#   knowledge_bases = ["tg-kb-group-1001234567890"]

# 2. Create GroupLink for user who added bot
link = await group_service.create_group_link(
    user_id=user_id,
    group_id=-1001234567890,
    group_title="Crypto Traders",
    language="en",
    user_role="admin"
)
# Creates GroupLink referencing thread_id
```

### Example 2: User Mentions Bot in Group

```python
# 1. Get group thread
thread = await thread_service.get_group_thread(group_id)

# 2. Use thread configuration
bot_name = thread.agent_name or settings.LUKA_NAME
language = thread.language
kb_indices = thread.knowledge_bases
system_prompt = thread.system_prompt

# 3. Generate response with thread context
async for chunk in llm_service.stream_response(
    message_text,
    user_id=user_id,
    thread_id=thread.thread_id,
    thread=thread  # Pass full thread for configuration
):
    ...
```

### Example 3: Admin Changes Group Language

```python
# 1. Update Thread language
await group_service.update_group_language(group_id, "ru")
# Internally:
#   thread = await thread_service.get_group_thread(group_id)
#   thread.language = "ru"
#   await thread_service.update_thread(thread)

# 2. All subsequent messages use new language
language = await group_service.get_group_language(group_id)  # Returns "ru"
```

### Example 4: /reset Command

```python
# 1. Get all users in group
user_ids = await redis_client.smembers(f"group_users:{group_id}")

# 2. Delete all GroupLinks
for uid in user_ids:
    await group_service.delete_group_link(uid, group_id)

# 3. Delete Thread
thread = await thread_service.get_group_thread(group_id)
await redis_client.delete(f"thread:{thread.thread_id}")
await redis_client.delete(f"thread_history:{thread.thread_id}")

# 4. Delete KB index
await es_service.delete_index(kb_index)

# ✅ Complete reset - all data removed
```

---

## Benefits of This Architecture

### 1. **Single Source of Truth**
- All configuration in Thread
- No duplication across GroupLinks
- Easy to maintain consistency

### 2. **Scalability**
- GroupLink is lightweight (just user ↔ group mapping)
- Thread configuration shared by all group members
- Easy to support many users per group

### 3. **Flexibility**
- Per-group agent customization
- Per-topic configuration inheritance
- Easy to add new configuration fields

### 4. **Consistency**
- Language changes affect all users immediately
- Settings changes visible to everyone
- No sync issues between user links

### 5. **Clean Separation**
- Thread = conversation configuration
- GroupLink = access control
- Clear responsibilities

---

## Migration Notes

### Breaking Changes

1. **GroupLink fields removed**:
   - `kb_index` → now in `Thread.knowledge_bases`
   - `language` → now in `Thread.language`
   - `group_title` → fetched from Telegram API
   - `group_username` → fetched from Telegram API

2. **Thread field renamed**:
   - `user_id` → `owner_id` (for clarity)

3. **GroupService methods updated**:
   - All methods now delegate to Thread
   - Automatic Thread creation when needed

### Migration Strategy

**No Redis migration needed** - just clear Redis:
```bash
redis-cli FLUSHDB
```

On next bot start:
- Groups auto-initialize on first message
- Threads created automatically
- GroupLinks reference new Threads

---

## Redis Keys

### Thread Keys
```
thread:{thread_id}                    # Thread hash (all fields)
thread_history:{thread_id}            # Conversation history
user_threads:{user_id}                # Set of user's thread IDs
user_active_thread:{user_id}          # Active thread ID (DMs only)
```

### GroupLink Keys
```
group_link:{user_id}:{group_id}       # GroupLink hash
user_groups:{user_id}                 # Set of user's group IDs
group_users:{group_id}                # Set of group's user IDs
```

### Topic Tracking
```
topic_greeted:{group_id}:{topic_id}   # TTL key (has greeting been sent)
```

---

## Future Enhancements

### 1. **Topic KB Separation**
Currently: Topics share group KB
Future: Separate KB per topic
```python
thread.knowledge_bases = [
    f"tg-kb-group-{abs(group_id)}-topic-{topic_id}"
]
```

### 2. **Advanced Tool Configuration**
```python
thread.enabled_tools = ["search_knowledge_base", "get_youtube_transcript"]
thread.disabled_tools = ["write_code"]
thread.tool_settings = {
    "search_knowledge_base": {"max_results": 10}
}
```

### 3. **Multi-KB Support**
```python
thread.knowledge_bases = [
    f"tg-kb-group-{group_id}",      # Group KB
    f"tg-kb-user-{owner_id}",       # Owner's personal KB
    "tg-kb-shared-crypto",          # Shared topic KB
]
```

### 4. **Per-User Thread Preferences**
Future: Users can have personal preferences within group threads:
```python
@dataclass
class ThreadPreference:
    user_id: int
    thread_id: str
    ui_language: str  # Personal UI language (may differ from thread language)
    notifications: bool
```

---

## Summary

The unified Thread architecture provides:
- ✅ Single source of truth for configuration
- ✅ Scalable for groups with many users
- ✅ Flexible for future enhancements
- ✅ Clean separation of concerns
- ✅ Easy to maintain and extend

**Key Principle**: Thread stores configuration, GroupLink stores access.

