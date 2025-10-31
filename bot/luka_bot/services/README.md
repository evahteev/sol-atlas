# Luka Bot Services Layer

**Architecture**: Service Layer implementing business logic with singleton pattern

**Last Updated**: 2025-10-13

---

## 📋 Overview

The services layer provides core business logic for luka_bot, implementing clean separation between handlers (presentation) and data access (models). Services manage state, external integrations, and complex operations.

### Key Characteristics

- **Pattern**: Singleton for stateful services, Factory for utilities
- **Storage**: Redis-first with Elasticsearch for search
- **Async**: All I/O operations are async
- **i18n**: Multi-language support (en, ru)
- **Fail-Safe**: LLM provider fallback for reliability

---

## 🗂️ Service Inventory

### Core Infrastructure (3 services)

| Service | Type | Purpose | Singleton |
|---------|------|---------|-----------|
| `llm_provider_fallback.py` | Infrastructure | LLM provider failover (Ollama→OpenAI) | ✅ |
| `llm_model_factory.py` | Factory | Creates LLM models with fallback | ❌ |
| `llm_service.py` | Service | Agent-based LLM interactions | ✅ |

### Data Management (3 services)

| Service | Type | Purpose | Singleton |
|---------|------|---------|-----------|
| `thread_service.py` | Service | Conversation thread CRUD | ✅ |
| `user_profile_service.py` | Service | User profile management | ✅ |
| `group_service.py` | Service | Telegram group management | ✅ |

### Knowledge Base (2 services)

| Service | Type | Purpose | Singleton |
|---------|------|---------|-----------|
| `elasticsearch_service.py` | Service | KB indexing and search | ✅ |
| `rag_service.py` | Utility | RAG prompt templates | ❌ |

### Moderation (2 services)

| Service | Type | Purpose | Singleton |
|---------|------|---------|-----------|
| `moderation_service.py` | Service | Group moderation & reputation | ✅ |
| `reply_tracker_service.py` | Service | Track bot replies for retroactive moderation | ✅ |

### UI/UX Enhancement (5 services)

| Service | Type | Purpose | Singleton |
|---------|------|---------|-----------|
| `message_state_service.py` | Service | Track streaming messages | ✅ |
| `divider_service.py` | Utility | Thread divider messages | ❌ |
| `thread_name_generator.py` | Utility | Generate thread names | ❌ |
| `welcome_prompts.py` | Utility | Random welcome prompts | ❌ |
| `messaging_service.py` | Utility | Message splitting/editing | ❌ |

**Total**: 16 services (9 singletons, 7 utilities)

---

## 🏗️ Architecture Patterns

### 1. Singleton Pattern (9 services)

Most stateful services use the singleton pattern to ensure single instance per process:

```python
_service_instance: Optional[ServiceClass] = None

def get_service() -> ServiceClass:
    global _service_instance
    if _service_instance is None:
        _service_instance = ServiceClass()
        logger.info("✅ ServiceClass singleton created")
    return _service_instance
```

**Services using Singleton**:
- `elasticsearch_service.py`
- `group_service.py`
- `llm_provider_fallback.py`
- `llm_service.py`
- `message_state_service.py`
- `moderation_service.py`
- `reply_tracker_service.py`
- `thread_service.py`
- `user_profile_service.py`

### 2. Factory Pattern (1 service)

`llm_model_factory.py` provides factory functions for creating LLM models:

```python
async def create_llm_model_with_fallback(
    context: Optional[str] = None,
    model_settings: Optional[ModelSettings] = None,
    force_provider: Optional[ProviderType] = None
) -> OpenAIModel:
    # Returns configured model instance
```

### 3. Utility Modules (6 services)

Stateless helper functions without singleton pattern:
- `divider_service.py`
- `messaging_service.py`
- `rag_service.py`
- `thread_name_generator.py`
- `welcome_prompts.py`

---

## 📊 Service Dependencies

```
┌─────────────────────────────────────────┐
│         Handler Layer                   │
│  (streaming_dm, group_messages, etc.)   │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│       Service Layer (Singleton)         │
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │ llm_service │◄───┤ llm_provider │  │
│  │             │    │   _fallback  │  │
│  └──────┬──────┘    └──────────────┘  │
│         │                              │
│         ▼                              │
│  ┌──────────────┐   ┌──────────────┐  │
│  │llm_model     │   │ thread       │  │
│  │  _factory    │   │   _service   │  │
│  └──────────────┘   └──────┬───────┘  │
│                            │          │
│  ┌──────────────┐          │          │
│  │ user_profile │◄─────────┘          │
│  │   _service   │                     │
│  └──────────────┘                     │
│                                       │
│  ┌──────────────┐   ┌──────────────┐ │
│  │ elasticsearch│   │ moderation   │ │
│  │   _service   │   │   _service   │ │
│  └──────────────┘   └──────────────┘ │
└───────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│       Infrastructure Layer               │
│                                         │
│  ┌─────────┐  ┌──────────┐  ┌─────┐   │
│  │  Redis  │  │Elasticsearch│ │ LLM │   │
│  └─────────┘  └──────────┘  └─────┘   │
└─────────────────────────────────────────┘
```

---

## 📚 Detailed Service Documentation

### Core Infrastructure Services

#### 1. `llm_provider_fallback.py`

**Purpose**: Automatic LLM provider failover ensuring bot never stops working

**Pattern**: Singleton  
**Dependencies**: Redis, LLM providers (Ollama, OpenAI)

**Key Features**:
- Provider health tracking with Redis TTL (30 minutes)
- Automatic failover (Ollama → OpenAI)
- Health checks with 3-second timeout
- Startup initialization method
- Provider statistics

**Usage**:
```python
from luka_bot.services.llm_provider_fallback import get_llm_provider_fallback

fallback = get_llm_provider_fallback()
provider = await fallback.get_working_provider()
stats = await fallback.get_provider_stats()
await fallback.initialize_on_startup()  # Called on bot start
```

**Where Used**: `__main__.py` (startup), `llm_model_factory.py`, handlers

---

#### 2. `llm_model_factory.py`

**Purpose**: Creates LLM models with automatic provider selection

**Pattern**: Factory Functions  
**Dependencies**: `llm_provider_fallback.py`, pydantic-ai

**Key Functions**:
- `create_llm_model_with_fallback()` - Main factory function
- `get_provider_status()` - Get all providers status
- `_create_ollama_model()` - Internal Ollama model creation
- `_create_openai_model()` - Internal OpenAI model creation

**Usage**:
```python
from luka_bot.services.llm_model_factory import create_llm_model_with_fallback

# Basic usage
model = await create_llm_model_with_fallback(context="user_123")

# With custom settings
custom_settings = ModelSettings(temperature=0.1, max_tokens=500)
model = await create_llm_model_with_fallback(
    context="moderation",
    model_settings=custom_settings
)

# Force specific provider (testing)
model = await create_llm_model_with_fallback(force_provider="openai")
```

**Where Used**: `llm_service.py`, agents

---

#### 3. `llm_service.py`

**Purpose**: Agent-based LLM interactions with pydantic-ai

**Pattern**: Singleton  
**Dependencies**: pydantic-ai agents, `llm_model_factory.py`, Redis

**Key Features**:
- Agent factory integration
- Streaming responses with tool execution
- Conversation history management (Redis)
- i18n support (language injection)
- Tool notifications (emoji-based: 🔍, 📺, etc.)
- Context-aware system prompts

**Main Methods**:
- `stream_response()` - Stream LLM response with history
- `_get_history()` - Retrieve conversation history
- `_get_default_system_prompt()` - Get system prompt with i18n

**Usage**:
```python
from luka_bot.services.llm_service import get_llm_service

llm_service = get_llm_service()
async for chunk in llm_service.stream_response(
    user_message="Hello",
    user_id=123,
    thread=thread
):
    if chunk["type"] == "text":
        print(chunk["text"], end="")
    elif chunk["type"] == "tool_notification":
        print(chunk["text"])  # emoji like 🔍
```

**Where Used**: `streaming_dm.py`, `group_messages.py` (mentions)

---

### Data Management Services

#### 4. `thread_service.py`

**Purpose**: Conversation thread CRUD operations (Redis)

**Pattern**: Singleton  
**Dependencies**: Redis

**Key Features**:
- DM threads (user conversations)
- Group threads (group-wide conversations)
- Topic threads (forum topics)
- Active thread tracking
- History management (up to 100 messages)
- Thread ID helpers for groups/topics

**Main Methods**:
- `create_thread()` - Create new DM thread
- `get_thread()` - Get thread by ID
- `list_threads()` - List user's threads
- `get_group_thread()` - Get/create group thread
- `get_topic_thread()` - Get/create topic thread
- `set_active_thread()` - Set active thread for user
- `update_thread()` - Update thread metadata

**Usage**:
```python
from luka_bot.services.thread_service import get_thread_service

thread_service = get_thread_service()

# Create thread
thread = await thread_service.create_thread(user_id, name="Chat 1")

# Get group thread
group_thread = await thread_service.get_group_thread(group_id=-1001234567)

# Set active
await thread_service.set_active_thread(user_id, thread.thread_id)
```

**Where Used**: All handlers, divider service

---

#### 5. `user_profile_service.py`

**Purpose**: User profile management (Redis)

**Pattern**: Singleton  
**Dependencies**: Redis

**Key Features**:
- Profile CRUD operations
- Language preference tracking
- Onboarding state management
- KB index tracking
- Auto-creation on first access

**Main Methods**:
- `get_or_create_profile()` - Get or create profile
- `get_profile()` - Get profile by user ID
- `get_language()` - Get user language
- `update_language()` - Update user language
- `mark_onboarding_complete()` - Mark onboarding done
- `get_kb_index()` - Get user's KB index

**Usage**:
```python
from luka_bot.services.user_profile_service import get_user_profile_service

profile_service = get_user_profile_service()

# Get or create
profile = await profile_service.get_or_create_profile(user_id, telegram_user)

# Get language
language = await profile_service.get_language(user_id)

# Update language
await profile_service.update_language(user_id, "ru")
```

**Where Used**: `i18n_middleware.py`, handlers, agents

---

#### 6. `group_service.py`

**Purpose**: Telegram group management (Redis)

**Pattern**: Singleton (async getter)  
**Dependencies**: Redis, `thread_service.py`

**Key Features**:
- Group link creation/updates
- Group thread management
- KB index tracking
- Group metadata caching (15 min TTL)
- Member listing

**Main Methods**:
- `create_group_link()` - Create/update group link
- `get_group_link()` - Get group link
- `list_user_groups()` - List user's groups
- `get_group_kb_index()` - Get group KB index
- `get_group_language()` - Get group language
- `get_cached_group_metadata()` - Get cached metadata

**Usage**:
```python
from luka_bot.services.group_service import get_group_service

group_service = await get_group_service()

# Create group link
link = await group_service.create_group_link(
    user_id=123,
    group_id=-1001234567,
    group_title="My Group",
    language="en"
)

# List groups
groups = await group_service.list_user_groups(user_id=123)
```

**Where Used**: `group_messages.py`, `groups_enhanced.py`, `group_commands.py`

---

### Knowledge Base Services

#### 7. `elasticsearch_service.py`

**Purpose**: Elasticsearch knowledge base operations

**Pattern**: Singleton (async getter)  
**Dependencies**: Elasticsearch

**Key Features**:
- Index template management (user KB, group KB, topics)
- Immediate message indexing (text-only)
- Multiple search methods (text, vector, hybrid)
- Bulk indexing support
- Metrics tracking

**Main Methods**:
- `ensure_templates()` - Create index templates
- `index_message()` - Index single message
- `bulk_index_messages()` - Bulk index
- `search_text()` - Text search
- `search_vector()` - Vector search
- `search_hybrid()` - Hybrid search
- `get_index_stats()` - Get index statistics

**Usage**:
```python
from luka_bot.services.elasticsearch_service import get_elasticsearch_service

es_service = await get_elasticsearch_service()

# Ensure templates exist
await es_service.ensure_templates()

# Index message
await es_service.index_message(
    index_name="tg-kb-user-123",
    message_data={
        "message_id": 1,
        "message_text": "Hello world",
        "sender_id": 123,
        "sender_name": "John",
        "role": "user",
        "message_date": datetime.utcnow().isoformat()
    }
)

# Search
results = await es_service.search_text(
    index_name="tg-kb-user-123",
    query="hello",
    size=5
)
```

**Where Used**: `group_messages.py` (indexing), `search.py`, agents (KB tools)

---

#### 8. `rag_service.py`

**Purpose**: RAG prompt templates for knowledge base queries

**Pattern**: Utility Functions  
**Dependencies**: `elasticsearch_service.py`

**Key Functions**:
- `build_rag_answer_prompt()` - Build answer prompt with context
- `build_rag_summary_prompt()` - Build summary prompt
- `build_rag_topic_prompt()` - Build topic extraction prompt
- `rag_search_and_answer()` - Complete RAG workflow
- `rag_summarize_messages()` - Summarize message history

**Usage**:
```python
from luka_bot.services.rag_service import build_rag_answer_prompt, rag_search_and_answer

# Build prompt manually
prompt = build_rag_answer_prompt(
    question="What is X?",
    messages=search_results,
    language="en"
)

# Complete RAG workflow
result = await rag_search_and_answer(
    question="What is X?",
    index_name="tg-kb-user-123",
    search_method="hybrid",
    max_results=5,
    language="en"
)
# Returns: {"answer": "...", "sources": [...], "metadata": {...}}
```

**Where Used**: Agents (KB search tool), handlers

---

### Moderation Services

#### 9. `moderation_service.py`

**Purpose**: Group moderation, reputation, and content filtering

**Pattern**: Singleton (async getter)  
**Dependencies**: Redis, LLM

**Key Features**:
- GroupSettings management (per-group/topic)
- UserReputation tracking (points, violations)
- Background message moderation
- Achievement system (50+ achievements)
- Ban management (threshold-based)
- Two-prompt architecture (moderation_prompt + system_prompt)

**Main Methods**:
- `get_group_settings()` - Get group settings
- `update_group_settings()` - Update settings
- `get_user_reputation()` - Get reputation
- `update_user_reputation()` - Update reputation
- `evaluate_message_moderation()` - Evaluate message with LLM
- `check_user_achievements()` - Check for achievements
- `get_group_leaderboard()` - Get top users

**Usage**:
```python
from luka_bot.services.moderation_service import get_moderation_service

moderation = await get_moderation_service()

# Get settings
settings = await moderation.get_group_settings(group_id=-1001234567)

# Get reputation
reputation = await moderation.get_user_reputation(
    user_id=123,
    group_id=-1001234567
)

# Evaluate message
result = await moderation.evaluate_message_moderation(
    message_text="Hello world",
    group_settings=settings,
    user_id=123,
    group_id=-1001234567
)
# Returns: {"helpful": 1, "violation": None, "action": "none"}
```

**Where Used**: `moderation_background.py`, `group_admin.py`, `reputation_viewer.py`

---

#### 10. `reply_tracker_service.py`

**Purpose**: Track bot replies for retroactive moderation

**Pattern**: Singleton  
**Dependencies**: Redis

**Key Features**:
- Track bot reply message IDs
- TTL-based cleanup (5 minutes)
- Support retroactive deletion
- Fast Redis storage

**Main Methods**:
- `track_reply()` - Track bot reply to user message
- `get_bot_reply()` - Get bot reply ID
- `remove_reply()` - Remove tracked reply
- `get_stats()` - Get tracking statistics

**Usage**:
```python
from luka_bot.services.reply_tracker_service import get_reply_tracker_service

tracker = get_reply_tracker_service()

# Track reply
await tracker.track_reply(
    chat_id=-1001234567,
    user_message_id=123,
    bot_reply_id=124
)

# Get bot reply (for retroactive deletion)
bot_reply_id = await tracker.get_bot_reply(
    chat_id=-1001234567,
    user_message_id=123
)
if bot_reply_id:
    await bot.delete_message(chat_id, bot_reply_id)
```

**Where Used**: `group_messages.py` (mentions), `moderation_background.py`

---

### UI/UX Enhancement Services

#### 11. `message_state_service.py`

**Purpose**: Track bot messages for real-time editing during streaming

**Pattern**: Singleton  
**Dependencies**: Redis

**Key Features**:
- Track streaming message state
- Enable real-time updates ("..." → "🔍" → results)
- 1-hour TTL
- Message type tracking (thinking/streaming/final)

**Main Methods**:
- `save_message()` - Save message state
- `get_message()` - Get message state
- `delete_message()` - Delete message state

**Usage**:
```python
from luka_bot.services.message_state_service import get_message_state_service

msg_state = get_message_state_service()

# Save state
await msg_state.save_message(
    user_id=123,
    message_id=456,
    chat_id=123,
    message_type="thinking",
    original_text="..."
)

# Get state
state = await msg_state.get_message(user_id=123)
```

**Where Used**: `streaming_dm.py`, `llm_service.py`

---

#### 12. `divider_service.py`

**Purpose**: Thread divider messages (context switching UX)

**Pattern**: Utility Functions  
**Dependencies**: `thread_service.py`, `user_profile_service.py`

**Key Functions**:
- `send_thread_divider()` - Send divider when switching threads
- `get_last_message_preview()` - Get preview of last message

**Usage**:
```python
from luka_bot.services.divider_service import send_thread_divider

await send_thread_divider(message, old_thread_id, new_thread)
# Sends: "📌 Switched to: Chat 1\n💬 Last: Hello world..."
```

**Where Used**: `streaming_dm.py` (thread switching), `chat.py`

---

#### 13. `thread_name_generator.py`

**Purpose**: Generate meaningful thread names from messages

**Pattern**: Utility Functions  
**Dependencies**: LLM (via factory)

**Key Functions**:
- `generate_thread_name()` - Generate thread name
- Strategy: LLM → smart truncation → fallback

**Usage**:
```python
from luka_bot.services.thread_name_generator import generate_thread_name

name = await generate_thread_name(
    message="How do I deploy a Python app?",
    language="en",
    max_length=20
)
# Returns: "Python Deployment"
```

**Where Used**: `streaming_dm.py` (lazy thread creation)

---

#### 14. `welcome_prompts.py`

**Purpose**: Random inspiring prompts for new conversations

**Pattern**: Utility Functions  
**Dependencies**: None

**Key Functions**:
- `get_random_welcome_prompt()` - Get random prompt
- `get_welcome_message()` - Get personalized welcome
- `get_new_thread_prompt()` - Get new thread prompt

**Usage**:
```python
from luka_bot.services.welcome_prompts import get_random_welcome_prompt

prompt = get_random_welcome_prompt(language="en")
# Returns: "What would you like to explore today? 🤔"
```

**Where Used**: `start.py`, `chat.py`

---

#### 15. `messaging_service.py`

**Purpose**: Message splitting and editing for long responses

**Pattern**: Utility Functions  
**Dependencies**: None

**Key Functions**:
- `split_long_message()` - Split at 4096 char limit
- `edit_and_send_parts()` - Edit first part, send rest

**Usage**:
```python
from luka_bot.services.messaging_service import edit_and_send_parts

await edit_and_send_parts(initial_message, long_html_text)
# Edits initial message with first part
# Sends remaining parts as new messages
```

**Where Used**: `streaming_dm.py`, handlers

---

## 🔧 Usage Guidelines

### Importing Services

```python
# ✅ GOOD: Use getter functions
from luka_bot.services.thread_service import get_thread_service

thread_service = get_thread_service()

# ❌ BAD: Don't instantiate directly
from luka_bot.services.thread_service import ThreadService
service = ThreadService()  # Creates duplicate instance!
```

### Service Lifecycle

1. **Lazy Initialization**: Services created on first `get_*()` call
2. **Singleton Caching**: Single instance per process
3. **No Cleanup**: Services live for process lifetime
4. **Startup Check**: Only `llm_provider_fallback` initialized on bot start

### Error Handling

Services use different error handling approaches:
- Some return `None` on errors
- Some log and re-raise
- Some catch and return fallback values

**Best Practice**: Always check return values and handle None cases

---

## 🎯 Design Principles

### 1. Separation of Concerns
Each service has single, clear responsibility

### 2. Redis-First Storage
Fast, persistent storage for all state

### 3. Async All The Way
All I/O operations are async for performance

### 4. i18n by Default
Most services support multiple languages

### 5. Fail-Safe Operations
LLM provider fallback ensures uptime

### 6. Singleton Pattern
Prevents duplicate instances and resource waste

---

## 📈 Metrics & Observability

### Services with Metrics

- `elasticsearch_service.py`: Index/search metrics
- `llm_provider_fallback.py`: Provider health stats
- `reply_tracker_service.py`: Tracking stats

### Logging Standards

All services use `loguru` with consistent format:
- ✅ Success: `✅ Operation completed`
- ⚠️ Warning: `⚠️ Warning message`
- ❌ Error: `❌ Error message`
- 🔍 Debug: `🔍 Debug info`

---

## 🧪 Testing Services

### Unit Testing

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_thread_service():
    # Mock Redis
    mock_redis = AsyncMock()
    
    # Create service with mock
    service = ThreadService()
    service.redis = mock_redis
    
    # Test
    thread = await service.create_thread(user_id=123, name="Test")
    assert thread.name == "Test"
```

### Integration Testing

```python
@pytest.mark.integration
async def test_elasticsearch_service():
    es_service = await get_elasticsearch_service()
    
    # Ensure templates
    await es_service.ensure_templates()
    
    # Index test message
    await es_service.index_message(...)
    
    # Search
    results = await es_service.search_text(...)
    assert len(results) > 0
```

---

## 🔗 Related Documentation

- [Refactoring TODO](./refactoring_todo.md) - Planned improvements
- [Architecture Docs](../../docs/architecture/) - System architecture
- [Handler Docs](../handlers/README.md) - Handler layer docs

---

## 📞 Support

For questions or issues with services:
1. Check this README
2. Review service docstrings
3. Check [refactoring_todo.md](./refactoring_todo.md) for known issues
4. Ask in team chat

---

**Maintained by**: Luka Bot Team  
**Version**: 1.0  
**Last Review**: 2025-10-13

