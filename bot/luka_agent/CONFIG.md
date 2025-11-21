# Luka Agent Configuration Strategy

**How luka_agent accesses external service configurations without depending on luka_bot.**

---

## Problem Statement

luka_agent tools need access to external service configurations:
- **Elasticsearch**: URL, credentials, indices for KB search
- **YouTube API**: API key for transcript fetching
- **LLM Settings**: Provider URLs, API keys, model names
- **S3/R2**: Credentials for file storage
- **External APIs**: Google Maps, Twitter, etc.

**Challenge**: luka_agent is a standalone, reusable module. It should NOT import from luka_bot or ag_ui_gateway (creates circular dependency).

---

## Chosen Solution: Dependency Injection via Service Layer

### Architecture

```
luka_agent/tools/
├── knowledge_base.py       # Imports from luka_bot.services (runtime)
├── youtube.py              # Imports from luka_bot.services (runtime)
└── sub_agent.py            # Imports from luka_bot.services (runtime)

luka_bot/services/
├── elasticsearch_service.py    # Has access to settings.ELASTICSEARCH_URL
├── youtube_service.py           # Has access to settings.YOUTUBE_API_KEY
└── workflow_context_service.py # Has access to filesystem

luka_bot/core/
└── config.py               # All configuration (Pydantic settings)
```

**How it works**:
1. **luka_agent tools** define what they need (KB search, YouTube transcripts)
2. **Tools import services at runtime** (inside implementation functions, not module-level)
3. **Services** handle all external resource access (ES, APIs, filesystem)
4. **Services** have access to luka_bot config (settings singleton)

### Example: knowledge_base.py

```python
# luka_agent/tools/knowledge_base.py

async def search_knowledge_base_impl(
    query: str,
    user_id: int,
    # ... other params
) -> str:
    """Implementation imports service at runtime."""
    try:
        # Import INSIDE function (runtime dependency injection)
        from luka_bot.services.elasticsearch_service import get_elasticsearch_service

        # Service has access to settings.ELASTICSEARCH_URL, credentials, etc.
        es_service = get_elasticsearch_service()

        # Tool doesn't need to know about config
        results = await es_service.search(index="...", query=query)

        return format_results(results)

    except ImportError:
        # Graceful degradation if service not available
        return "Error: Knowledge base service not configured."
```

**WHY This Works**:
- ✅ luka_agent doesn't import luka_bot at module level (no circular dependency)
- ✅ Services encapsulate all config access (single responsibility)
- ✅ Tools remain platform-agnostic (don't care about Elasticsearch URL)
- ✅ Graceful degradation if service unavailable (web-only deployment without ES)
- ✅ Testing is easy (mock services, not config)

---

## Configuration Flow

### 1. Environment Variables → Settings

```bash
# .env file
ELASTICSEARCH_URL=http://localhost:9220
ELASTICSEARCH_ENABLED=true
YOUTUBE_API_KEY=AIzaSy...
OLLAMA_URL=http://localhost:11434
```

### 2. Settings → Services

```python
# luka_bot/core/config.py
class ElasticsearchSettings(EnvBaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9220"
    ELASTICSEARCH_ENABLED: bool = True

settings = Settings()  # Global singleton

# luka_bot/services/elasticsearch_service.py
from luka_bot.core.config import settings

class ElasticsearchService:
    def __init__(self):
        self.url = settings.ELASTICSEARCH_URL
        self.enabled = settings.ELASTICSEARCH_ENABLED
        self.client = Elasticsearch(self.url) if self.enabled else None

    async def search(self, index, query):
        if not self.enabled:
            raise ServiceUnavailableError("Elasticsearch not enabled")
        return await self.client.search(index=index, query=query)

_service_instance = None

def get_elasticsearch_service() -> ElasticsearchService:
    """Singleton pattern."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ElasticsearchService()
    return _service_instance
```

### 3. Services → Tools

```python
# luka_agent/tools/knowledge_base.py
async def search_knowledge_base_impl(...):
    from luka_bot.services.elasticsearch_service import get_elasticsearch_service

    service = get_elasticsearch_service()
    results = await service.search(...)
    return results
```

**Benefits**:
- Config changes in ONE place (luka_bot/core/config.py)
- Services handle connection management, retries, caching
- Tools remain simple and focused on business logic

---

## Service Layer Responsibilities

### ElasticsearchService
- **Owns**: Connection pooling, index management, query building
- **Reads from config**: ELASTICSEARCH_URL, ELASTICSEARCH_ENABLED, credentials
- **Used by tools**: knowledge_base.py

### YouTubeService (hypothetical)
- **Owns**: YouTube API client, transcript parsing, caching
- **Reads from config**: YOUTUBE_API_KEY, YOUTUBE_TRANSCRIPT_ENABLED
- **Used by tools**: youtube.py

### WorkflowContextService
- **Owns**: Sub-agent discovery, config.yaml parsing, README reading
- **Reads from config**: Filesystem paths (luka_agent/sub_agents/)
- **Used by tools**: sub_agent.py

### LLMProviderService
- **Owns**: LLM client management, failover logic, streaming
- **Reads from config**: OLLAMA_URL, OPENAI_API_KEY, model names
- **Used by**: Graph nodes (agent_node)

---

## Alternative Solutions (Rejected)

### ❌ Option 1: Duplicate Config in luka_agent

```python
# luka_agent/config.py (BAD)
class LukaAgentSettings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9220"
    YOUTUBE_API_KEY: str = ""
```

**Problems**:
- Config duplication (luka_bot and luka_agent have same settings)
- Out of sync issues (change in one place, forget other)
- Requires separate .env parsing

### ❌ Option 2: Pass Config to Tools

```python
# BAD - Config passed to every tool
def create_knowledge_base_tool(
    user_id: int,
    thread_id: str,
    elasticsearch_url: str,  # Config param
    elasticsearch_credentials: dict,  # Config param
):
    # Tool needs to manage connection
    client = Elasticsearch(elasticsearch_url, **credentials)
```

**Problems**:
- Tools become responsible for connection management
- Config params explode (every tool needs 5+ config params)
- Hard to test (must mock Elasticsearch client)
- Violates separation of concerns

### ❌ Option 3: Import Config Directly

```python
# luka_agent/tools/knowledge_base.py (BAD)
from luka_bot.core.config import settings  # Module-level import

async def search_knowledge_base_impl(...):
    url = settings.ELASTICSEARCH_URL
    client = Elasticsearch(url)
```

**Problems**:
- Module-level import creates circular dependency
- luka_agent depends on luka_bot (not standalone)
- Can't use luka_agent in other projects

---

## Best Practices

### DO ✅

1. **Import services inside implementation functions**
   ```python
   async def search_kb_impl(...):
       from luka_bot.services.elasticsearch_service import get_elasticsearch_service
       service = get_elasticsearch_service()
   ```

2. **Use singleton service pattern**
   ```python
   def get_elasticsearch_service() -> ElasticsearchService:
       global _service_instance
       if _service_instance is None:
           _service_instance = ElasticsearchService()
       return _service_instance
   ```

3. **Handle service unavailability gracefully**
   ```python
   try:
       from luka_bot.services.x import get_x_service
       service = get_x_service()
   except ImportError:
       return "Error: Service not configured."
   except ServiceUnavailableError:
       return "Error: Service temporarily unavailable."
   ```

4. **Keep services in luka_bot/services/**
   - Services own config access
   - Services handle external resources (ES, APIs, DB)
   - Services provide clean interfaces to tools

### DON'T ❌

1. **Don't import config at module level**
   ```python
   # BAD
   from luka_bot.core.config import settings
   ELASTICSEARCH_URL = settings.ELASTICSEARCH_URL
   ```

2. **Don't pass config to tool factories**
   ```python
   # BAD
   create_kb_tool(user_id, thread_id, elasticsearch_url, ...)
   ```

3. **Don't manage connections in tools**
   ```python
   # BAD
   async def search_kb_impl(...):
       client = Elasticsearch(settings.ELASTICSEARCH_URL)
       # Tools shouldn't manage clients
   ```

4. **Don't create duplicate config classes**
   ```python
   # BAD - Don't create luka_agent/config.py
   class LukaAgentSettings(BaseSettings):
       # Duplicates luka_bot config
   ```

---

## Testing Strategy

### Unit Testing Tools (No Config Needed)

```python
# luka_agent/tests/test_knowledge_base.py

@pytest.mark.asyncio
async def test_search_kb_impl(mocker):
    """Test tool with mocked service."""

    # Mock the service
    mock_service = mocker.Mock()
    mock_service.search = AsyncMock(return_value=["result1", "result2"])

    # Mock the service getter
    mocker.patch(
        "luka_bot.services.elasticsearch_service.get_elasticsearch_service",
        return_value=mock_service
    )

    # Test tool
    result = await search_knowledge_base_impl(
        query="test",
        user_id=123,
        thread_id="thread",
        language="en",
        knowledge_bases=["kb1"]
    )

    assert "result1" in result
    mock_service.search.assert_called_once()
```

**Benefits**:
- No real Elasticsearch needed
- Fast tests
- Focus on tool logic, not service internals

### Integration Testing (With Real Config)

```python
# luka_bot/tests/integration/test_kb_search.py

@pytest.mark.asyncio
@pytest.mark.integration
async def test_kb_search_with_real_es():
    """Test with real Elasticsearch (uses settings from .env.test)."""

    # Uses real settings.ELASTICSEARCH_URL
    from luka_agent.tools import create_tools_for_user

    tools = create_tools_for_user(
        user_id=123,
        thread_id="test",
        knowledge_bases=["test-kb"],
        enabled_tools=["knowledge_base"],
    )

    kb_tool = next(t for t in tools if t.name == "search_knowledge_base")
    result = await kb_tool.ainvoke({"query": "test"})

    assert isinstance(result, str)
```

**Benefits**:
- Tests real config loading
- Catches integration issues
- Can use test .env file

---

## Configuration Checklist

### Adding New Tool with External Dependencies

- [ ] **Identify external resources needed**
  - [ ] Elasticsearch? YouTube API? LLM? S3?

- [ ] **Check if service exists**
  - [ ] Look in `luka_bot/services/`
  - [ ] If exists: use `get_*_service()` pattern
  - [ ] If missing: create new service

- [ ] **Check if config exists**
  - [ ] Look in `luka_bot/core/config.py`
  - [ ] If exists: service will read it
  - [ ] If missing: add to appropriate Settings class

- [ ] **Tool implementation**
  - [ ] Import service inside implementation function
  - [ ] Call service methods (no direct API calls)
  - [ ] Handle ImportError gracefully
  - [ ] Handle ServiceUnavailableError gracefully

- [ ] **Testing**
  - [ ] Unit test: Mock service
  - [ ] Integration test: Use real config (optional)

---

## Summary

### Key Principle
**luka_agent tools delegate all external resource access to luka_bot services via runtime dependency injection.**

### Architecture Pattern
```
Environment (.env)
    ↓
Config (settings singleton in luka_bot)
    ↓
Services (luka_bot/services/*.py)
    ↓
Tools (luka_agent/tools/*.py - runtime import)
```

### Benefits
- ✅ No circular dependencies
- ✅ luka_agent remains standalone
- ✅ Config in ONE place
- ✅ Services encapsulate complexity
- ✅ Easy to test (mock services)
- ✅ Graceful degradation (web-only deployments)

### Example Tools
- `knowledge_base.py` → imports `get_elasticsearch_service()` at runtime
- `youtube.py` → imports `get_youtube_service()` at runtime (future)
- `sub_agent.py` → imports `get_workflow_context_service()` at runtime

This pattern keeps luka_agent clean, reusable, and platform-agnostic while maintaining access to all necessary configurations through the service layer.
