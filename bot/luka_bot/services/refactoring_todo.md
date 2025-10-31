# Services Layer Refactoring TODO

**Status**: Planning  
**Priority**: Medium-High  
**Estimated Effort**: 2-3 weeks  
**Last Updated**: 2025-10-13

---

## 🎯 Executive Summary

The services layer works well but has technical debt that impacts maintainability, testability, and consistency. This document outlines planned refactorings to improve code quality while maintaining backward compatibility.

### Key Issues

1. **Inconsistent Dependency Injection** - Mixed patterns for Redis client injection
2. **Async/Sync Confusion** - Some getters are async without reason
3. **Boilerplate Duplication** - ~100 lines of repeated singleton code
4. **No Type Contracts** - Missing Protocol interfaces for services
5. **Tight Coupling** - Services import each other directly
6. **Inconsistent Error Handling** - No standard exception hierarchy

### Expected Benefits

- ✅ **Better Testing**: Dependency injection enables mocking
- ✅ **Less Code**: Eliminate ~100 lines of boilerplate
- ✅ **Type Safety**: Protocol interfaces improve IDE support
- ✅ **Maintainability**: Consistent patterns easier to understand
- ✅ **Debugging**: Custom exceptions with clear error messages

---

## 📊 Priority Matrix

| Priority | Issue | Impact | Effort | Risk | Benefit |
|----------|-------|--------|--------|------|---------|
| 🔴 **P0** | Async/Sync getters | High | Low | Low | High |
| 🔴 **P0** | Update `__init__.py` | High | Low | None | High |
| 🔴 **P1** | Inconsistent DI | High | Medium | Low | High |
| 🟡 **P2** | Error handling | Medium | Medium | Low | High |
| 🟡 **P2** | Singleton boilerplate | Medium | Medium | Low | Medium |
| 🟡 **P2** | Missing protocols | Medium | Medium | None | Medium |
| 🟡 **P3** | Service dependencies | Medium | Low | Low | Medium |
| 🟢 **P4** | Health checks | Low | High | None | Low |

---

## 🔴 Priority 0: Critical Issues (Week 1)

### Issue 1: Async/Sync Getter Inconsistency

**Problem**: Some singleton getters are async without actual async work:

```python
# ❌ Unnecessarily async (no await inside)
async def get_moderation_service() -> ModerationService:
    global _moderation_service
    if _moderation_service is None:
        from luka_bot.core.loader import redis_client
        _moderation_service = ModerationService(redis_client)
    return _moderation_service

# ✅ Should be sync
def get_moderation_service() -> ModerationService:
    global _moderation_service
    if _moderation_service is None:
        _moderation_service = ModerationService()
    return _moderation_service
```

**Impact**:
- Confusing API for developers
- Forces unnecessary `await` in handlers
- Inconsistent with other services

**Affected Files**:
- `moderation_service.py` (line 858)
- `group_service.py` (line 631)
- `elasticsearch_service.py` (line 690)

**Solution**:
1. Change getters to sync functions
2. Move Redis client import to lazy property or constructor
3. Update all handler imports (remove `await`)

**Estimated Effort**: 2-4 hours

**Migration Guide**:
```python
# Before
moderation = await get_moderation_service()

# After
moderation = get_moderation_service()
```

**Testing**:
- Run full test suite
- Verify no async warnings
- Check all handlers compile

---

### Issue 2: Incomplete `__init__.py` Exports

**Problem**: Only 2 of 16 services are exported, making discovery difficult

**Current State**:
```python
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.services.message_state_service import get_message_state_service

__all__ = [
    "get_elasticsearch_service",
    "get_message_state_service",
]
```

**Impact**:
- Developers don't know what services exist
- Must explore directory to find services
- No single source of truth

**Solution**: Export all public service getters

**New Structure**:
```python
"""
luka_bot services - Service layer for business logic.

Architecture:
- Singleton pattern for stateful services
- Factory functions for stateless utilities
- Redis-first storage with Elasticsearch for search
- Async I/O operations
- i18n support

Usage:
    from luka_bot.services import get_thread_service, get_user_profile_service
    
    thread_service = get_thread_service()
    profile_service = get_user_profile_service()
"""

# Core services
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.group_service import get_group_service

# LLM services
from luka_bot.services.llm_service import get_llm_service
from luka_bot.services.llm_provider_fallback import get_llm_provider_fallback
from luka_bot.services.llm_model_factory import create_llm_model_with_fallback

# KB services
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.services.rag_service import (
    build_rag_answer_prompt,
    build_rag_summary_prompt,
    rag_search_and_answer,
)

# Moderation services
from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.services.reply_tracker_service import get_reply_tracker_service

# UI/UX services
from luka_bot.services.message_state_service import get_message_state_service
from luka_bot.services.divider_service import send_thread_divider
from luka_bot.services.thread_name_generator import generate_thread_name
from luka_bot.services.welcome_prompts import (
    get_random_welcome_prompt,
    get_welcome_message,
)

# Utility services
from luka_bot.services.messaging_service import (
    split_long_message,
    edit_and_send_parts,
)

__all__ = [
    # Core services
    "get_thread_service",
    "get_user_profile_service",
    "get_group_service",
    
    # LLM services
    "get_llm_service",
    "get_llm_provider_fallback",
    "create_llm_model_with_fallback",
    
    # KB services
    "get_elasticsearch_service",
    "build_rag_answer_prompt",
    "build_rag_summary_prompt",
    "rag_search_and_answer",
    
    # Moderation services
    "get_moderation_service",
    "get_reply_tracker_service",
    
    # UI/UX services
    "get_message_state_service",
    "send_thread_divider",
    "generate_thread_name",
    "get_random_welcome_prompt",
    "get_welcome_message",
    
    # Utility services
    "split_long_message",
    "edit_and_send_parts",
]
```

**Estimated Effort**: 30 minutes

**Testing**:
```python
# Verify all imports work
from luka_bot.services import *
```

---

## 🔴 Priority 1: High Impact Issues (Week 1-2)

### Issue 3: Inconsistent Dependency Injection

**Problem**: Services handle Redis client differently

**Patterns Found**:
1. **Constructor parameter** (3 services):
   ```python
   def __init__(self, redis_client):
       self.redis = redis_client
   ```
   - `moderation_service.py`
   - `group_service.py`
   - `reply_tracker_service.py`

2. **Global import** (5 services):
   ```python
   def __init__(self):
       self.redis = redis_client  # from luka_bot.core.loader
   ```
   - `thread_service.py`
   - `user_profile_service.py`

3. **Lazy property** (1 service):
   ```python
   def __init__(self):
       self._redis = None
   
   @property
   def redis(self):
       if self._redis is None:
           self._redis = redis_client
       return self._redis
   ```
   - `message_state_service.py`

4. **Optional injection** (1 service):
   ```python
   def __init__(self, redis_client=None):
       self.redis = redis_client if redis_client else globals()['redis_client']
   ```
   - `llm_provider_fallback.py`

**Impact**:
- Hard to test (can't inject mock Redis)
- Inconsistent patterns confusing to maintain
- Tight coupling to global state

**Solution**: Create `BaseService` class with consistent DI

**Implementation**:

```python
# luka_bot/services/base.py
"""Base service class with dependency injection support."""
from abc import ABC
from typing import Optional, Dict, Any
from redis.asyncio import Redis
from loguru import logger


class BaseService(ABC):
    """
    Base service with dependency injection support.
    
    Provides:
    - Consistent Redis client injection
    - Health check interface
    - Logging utilities
    
    Usage:
        class MyService(BaseService):
            def __init__(self, redis_client: Optional[Redis] = None):
                super().__init__(redis_client)
                # Service-specific initialization
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize service with optional Redis client.
        
        Args:
            redis_client: Redis client instance (uses default if None)
        """
        # Lazy import to avoid circular dependency
        if redis_client is None:
            from luka_bot.core.loader import redis_client as default_redis
            redis_client = default_redis
        
        self._redis = redis_client
    
    @property
    def redis(self) -> Redis:
        """Get Redis client instance."""
        return self._redis
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health.
        
        Returns:
            Dictionary with health status
        """
        return {
            "healthy": True,
            "service": self.__class__.__name__,
            "timestamp": None  # Will be set by implementation
        }
```

**Migration Example**:

```python
# Before
class ThreadService:
    def __init__(self):
        self.redis = redis_client

# After
from luka_bot.services.base import BaseService

class ThreadService(BaseService):
    def __init__(self, redis_client: Optional[Redis] = None):
        super().__init__(redis_client)
        # Service-specific init
```

**Migration Plan**:
1. Create `base.py` with `BaseService` class
2. Migrate one service as proof of concept
3. Update tests to verify DI works
4. Migrate remaining services
5. Update all getter functions

**Estimated Effort**: 1-2 days

**Testing Strategy**:
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_thread_service_with_mock_redis():
    # Create mock Redis
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    # Inject mock
    service = ThreadService(redis_client=mock_redis)
    
    # Test
    result = await service.get_thread("test_id")
    mock_redis.get.assert_called_once()
```

**Breaking Changes**: None (backward compatible)

---

### Issue 4: No Standard Error Handling

**Problem**: Services handle errors inconsistently

**Current Patterns**:
1. Return `None` on error (silent failure)
2. Log and re-raise
3. Log and return fallback value
4. Raise generic `Exception`

**Examples**:
```python
# Pattern 1: Silent failure
async def get_thread(self, thread_id: str):
    try:
        # ... 
        return thread
    except Exception:
        return None  # Consumer doesn't know why it failed

# Pattern 2: Generic exception
async def get_thread(self, thread_id: str):
    if not thread:
        raise Exception("Thread not found")  # Not specific

# Pattern 3: Mixed
async def get_thread(self, thread_id: str):
    try:
        # ...
        return thread
    except RedisError:
        logger.error("Redis error")
        return None
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
```

**Impact**:
- Hard to debug (silent failures)
- Can't distinguish error types
- No standard error messages
- Difficult error recovery

**Solution**: Create exception hierarchy and standard patterns

**Implementation**:

```python
# luka_bot/services/exceptions.py
"""Service layer exceptions."""


class ServiceError(Exception):
    """
    Base exception for all service errors.
    
    All service exceptions should inherit from this.
    """
    pass


class ServiceNotFoundError(ServiceError):
    """
    Resource not found in service.
    
    Raised when:
    - Thread doesn't exist
    - User profile not found
    - Group not found
    
    Example:
        raise ServiceNotFoundError(f"Thread {thread_id} not found")
    """
    pass


class ServiceConnectionError(ServiceError):
    """
    Failed to connect to external service.
    
    Raised when:
    - Redis unavailable
    - Elasticsearch down
    - LLM provider timeout
    
    Example:
        raise ServiceConnectionError(f"Redis unavailable: {error}")
    """
    pass


class ServiceTimeoutError(ServiceError):
    """
    Service operation timed out.
    
    Raised when:
    - LLM request timeout
    - Elasticsearch query timeout
    - Background task timeout
    
    Example:
        raise ServiceTimeoutError(f"LLM request timed out after {timeout}s")
    """
    pass


class ServiceValidationError(ServiceError):
    """
    Invalid input to service method.
    
    Raised when:
    - Empty required parameter
    - Invalid format
    - Out of range value
    
    Example:
        raise ServiceValidationError("thread_id cannot be empty")
    """
    pass


class ServiceConfigurationError(ServiceError):
    """
    Service misconfiguration.
    
    Raised when:
    - Missing API key
    - Invalid settings
    - Dependency not available
    
    Example:
        raise ServiceConfigurationError("OPENAI_API_KEY not set")
    """
    pass
```

**Standard Error Handling Pattern**:

```python
from luka_bot.services.exceptions import (
    ServiceNotFoundError,
    ServiceConnectionError,
    ServiceValidationError,
    ServiceError
)

class ThreadService(BaseService):
    async def get_thread(self, thread_id: str) -> Thread:
        """
        Get thread by ID.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread instance
            
        Raises:
            ServiceValidationError: If thread_id is empty
            ServiceNotFoundError: If thread doesn't exist
            ServiceConnectionError: If Redis is unavailable
        """
        # Step 1: Validate input
        if not thread_id:
            raise ServiceValidationError("thread_id cannot be empty")
        
        if not isinstance(thread_id, str):
            raise ServiceValidationError(f"thread_id must be str, got {type(thread_id)}")
        
        try:
            # Step 2: Perform operation
            thread = await self._load_thread(thread_id)
            
            # Step 3: Validate result
            if not thread:
                raise ServiceNotFoundError(
                    f"Thread {thread_id} not found"
                )
            
            return thread
            
        except ServiceError:
            # Re-raise our own exceptions
            raise
            
        except RedisError as e:
            # Wrap infrastructure errors
            logger.error(f"Redis error loading thread {thread_id}: {e}")
            raise ServiceConnectionError(
                f"Failed to load thread: Redis unavailable"
            ) from e
            
        except Exception as e:
            # Catch unexpected errors
            logger.error(
                f"Unexpected error loading thread {thread_id}: {e}",
                exc_info=True
            )
            raise ServiceError(
                f"Failed to load thread: {type(e).__name__}"
            ) from e
```

**Handler Error Handling**:

```python
from luka_bot.services.exceptions import (
    ServiceNotFoundError,
    ServiceConnectionError
)

async def handle_message(message: Message):
    try:
        thread = await thread_service.get_thread(thread_id)
        
    except ServiceNotFoundError:
        await message.answer("Thread not found. Use /chat to see your threads.")
        
    except ServiceConnectionError:
        await message.answer("Service temporarily unavailable. Please try again.")
        
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        await message.answer("An error occurred. Please try again.")
```

**Migration Plan**:
1. Create `exceptions.py` with hierarchy
2. Update one service (proof of concept)
3. Update tests for new exceptions
4. Migrate remaining services
5. Update handlers to catch specific exceptions
6. Add exception documentation

**Estimated Effort**: 2-3 days

**Breaking Changes**: 
- Services may now raise exceptions instead of returning `None`
- Handlers need to catch specific exceptions

**Migration Guide**:
```python
# Before
thread = await thread_service.get_thread(thread_id)
if not thread:
    await message.answer("Thread not found")

# After
from luka_bot.services.exceptions import ServiceNotFoundError

try:
    thread = await thread_service.get_thread(thread_id)
except ServiceNotFoundError:
    await message.answer("Thread not found")
```

---

## 🟡 Priority 2: Quality Improvements (Week 2-3)

### Issue 5: Singleton Boilerplate Duplication

**Problem**: Every service repeats 8-10 lines of singleton code

**Current Pattern** (repeated 9 times):
```python
_service: Optional[ServiceClass] = None

def get_service() -> ServiceClass:
    global _service
    if _service is None:
        _service = ServiceClass()
        logger.info("✅ ServiceClass singleton created")
    return _service
```

**Total Lines**: ~90 lines of identical code across 9 files

**Solution**: Decorator pattern

**Implementation**:

```python
# luka_bot/services/registry.py
"""Service registry for singleton management."""
from typing import TypeVar, Callable, Dict, Any, Optional
from loguru import logger

T = TypeVar('T')
_service_registry: Dict[str, Any] = {}


def singleton_service(cls: type[T]) -> type[T]:
    """
    Decorator to make service a singleton with auto-generated getter.
    
    Usage:
        @singleton_service
        class MyService(BaseService):
            ...
        
        # Auto-generates: get_my_service()
        service = get_my_service()
    
    Args:
        cls: Service class to make singleton
        
    Returns:
        Original class with singleton behavior
    """
    service_name = cls.__name__
    
    def getter() -> T:
        """Get or create singleton instance."""
        if service_name not in _service_registry:
            _service_registry[service_name] = cls()
            logger.info(f"✅ {service_name} singleton created")
        return _service_registry[service_name]
    
    # Generate getter function name
    # ThreadService -> get_thread_service
    getter_name = f"get_{cls.__name__.replace('Service', '').lower()}_service"
    getter.__name__ = getter_name
    getter.__doc__ = f"Get or create {service_name} singleton."
    
    # Attach getter to class for easy access
    cls.__singleton_getter__ = getter
    
    return cls


def get_service_registry() -> Dict[str, Any]:
    """
    Get all registered singleton services.
    
    Returns:
        Dictionary mapping service names to instances
    """
    return _service_registry.copy()


def clear_service_registry() -> None:
    """
    Clear all singleton services (for testing).
    
    Warning:
        This will destroy all service instances.
        Use only in test teardown.
    """
    global _service_registry
    _service_registry.clear()
    logger.warning("🧹 Service registry cleared")
```

**Usage Example**:

```python
# Before (12 lines)
class ThreadService:
    def __init__(self):
        self.redis = redis_client

_thread_service: Optional[ThreadService] = None

def get_thread_service() -> ThreadService:
    global _thread_service
    if _thread_service is None:
        _thread_service = ThreadService()
        logger.info("✅ ThreadService singleton created")
    return _thread_service


# After (5 lines)
from luka_bot.services.base import BaseService
from luka_bot.services.registry import singleton_service

@singleton_service
class ThreadService(BaseService):
    pass

# Getter auto-generated
get_thread_service = ThreadService.__singleton_getter__
```

**Benefits**:
- Eliminates ~90 lines of boilerplate
- Consistent singleton behavior
- Easy to test (can clear registry)
- Registry for debugging/monitoring

**Migration Plan**:
1. Create `registry.py` with decorator
2. Migrate one service (proof of concept)
3. Verify tests pass
4. Migrate remaining services
5. Update documentation

**Estimated Effort**: 1 day

**Testing**:
```python
import pytest
from luka_bot.services.registry import clear_service_registry

@pytest.fixture(autouse=True)
def clear_services():
    """Clear service registry after each test."""
    yield
    clear_service_registry()

def test_singleton_behavior():
    service1 = get_thread_service()
    service2 = get_thread_service()
    assert service1 is service2  # Same instance
```

---

### Issue 6: Missing Service Interfaces

**Problem**: No formal contracts between services and consumers

**Impact**:
- Hard to mock in tests
- No IDE autocomplete for protocols
- Can't enforce interface compliance
- Difficult to create alternative implementations

**Solution**: Define Protocol classes

**Implementation**:

```python
# luka_bot/services/protocols.py
"""Protocol interfaces for services (PEP 544)."""
from typing import Protocol, Optional, List, Dict, Any
from datetime import datetime

from luka_bot.models.thread import Thread
from luka_bot.models.user_profile import UserProfile


class ThreadServiceProtocol(Protocol):
    """
    Interface for thread management services.
    
    Any class implementing these methods can be used as a thread service.
    """
    
    async def create_thread(
        self,
        user_id: int,
        name: Optional[str] = None
    ) -> Thread:
        """Create new thread."""
        ...
    
    async def get_thread(self, thread_id: str) -> Thread:
        """Get thread by ID."""
        ...
    
    async def list_threads(self, user_id: int) -> List[Thread]:
        """List user's threads."""
        ...
    
    async def set_active_thread(self, user_id: int, thread_id: str) -> None:
        """Set active thread."""
        ...


class UserProfileServiceProtocol(Protocol):
    """Interface for user profile services."""
    
    async def get_or_create_profile(
        self,
        user_id: int,
        telegram_user: Optional[Any] = None
    ) -> UserProfile:
        """Get or create user profile."""
        ...
    
    async def get_language(self, user_id: int) -> str:
        """Get user language."""
        ...
    
    async def update_language(self, user_id: int, language: str) -> bool:
        """Update user language."""
        ...


class LLMServiceProtocol(Protocol):
    """Interface for LLM services."""
    
    async def stream_response(
        self,
        user_message: str,
        user_id: int,
        thread_id: Optional[str] = None,
        thread: Optional[Thread] = None,
        system_prompt: Optional[str] = None,
        save_history: bool = True
    ):
        """Stream LLM response."""
        ...
```

**Usage in Handlers**:

```python
# Before (implicit dependency)
async def handle_message(message: Message):
    thread_service = get_thread_service()  # What's the interface?
    thread = await thread_service.get_thread(thread_id)

# After (explicit contract)
from luka_bot.services.protocols import ThreadServiceProtocol

async def handle_message(
    message: Message,
    thread_service: Optional[ThreadServiceProtocol] = None
):
    # Use default if not provided
    if thread_service is None:
        thread_service = get_thread_service()
    
    thread = await thread_service.get_thread(thread_id)
    # IDE knows thread_service has get_thread method
```

**Testing Benefits**:

```python
# Easy mocking with protocols
class MockThreadService:
    """Mock implementing ThreadServiceProtocol."""
    
    async def create_thread(self, user_id: int, name: Optional[str] = None):
        return Thread(thread_id="test", owner_id=user_id, name=name or "Test")
    
    async def get_thread(self, thread_id: str):
        return Thread(thread_id=thread_id, owner_id=123, name="Test")
    
    # ... implement other protocol methods

# Use in tests
mock_service = MockThreadService()
await handle_message(message, thread_service=mock_service)
```

**Migration Plan**:
1. Create `protocols.py` with key service protocols
2. Update one handler to use protocol (proof of concept)
3. Verify type checking works
4. Add protocols for remaining services
5. Update tests to use protocols
6. Document protocol usage

**Estimated Effort**: 2 days

**Breaking Changes**: None (backward compatible)

---

### Issue 7: Tight Service Dependencies

**Problem**: Services import each other directly, creating tight coupling

**Example**:
```python
# divider_service.py
from luka_bot.services.thread_service import get_thread_service
from luka_bot.services.user_profile_service import get_user_profile_service

async def send_thread_divider(message, old_thread_id, new_thread):
    thread_service = get_thread_service()  # Hard dependency
    profile_service = get_user_profile_service()
    # ...
```

**Issues**:
- Circular dependency risk
- Hard to test
- Can't use alternative implementations
- Tight coupling

**Solution**: Dependency injection pattern

**Implementation**:

```python
# Before (tight coupling)
from luka_bot.services.thread_service import get_thread_service

async def send_thread_divider(message, old_thread_id, new_thread):
    thread_service = get_thread_service()
    # ...


# After (loose coupling)
from luka_bot.services.protocols import ThreadServiceProtocol

async def send_thread_divider(
    message,
    old_thread_id,
    new_thread,
    thread_service: Optional[ThreadServiceProtocol] = None
):
    # Use default if not provided (backward compatible)
    if thread_service is None:
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
    
    # Use injected service
    # ...
```

**Benefits**:
- No circular dependencies
- Easy to test (inject mocks)
- Can swap implementations
- Loose coupling

**Migration Plan**:
1. Identify services with cross-dependencies
2. Add optional parameters with defaults
3. Update tests to inject mocks
4. Document DI pattern

**Estimated Effort**: 1 day

**Breaking Changes**: None (backward compatible with defaults)

---

## 🟢 Priority 4: Nice to Have (Future)

### Issue 8: Missing Health Checks

**Problem**: No way to check if services are healthy (except LLM provider)

**Solution**: Add health check interface to `BaseService`

**Implementation**:

```python
# luka_bot/services/base.py
class BaseService(ABC):
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health.
        
        Returns:
            {
                "healthy": bool,
                "service": str,
                "details": dict,
                "timestamp": str
            }
        """
        return {
            "healthy": True,
            "service": self.__class__.__name__,
            "details": {},
            "timestamp": datetime.utcnow().isoformat()
        }


# Implementation in services
class ThreadService(BaseService):
    async def health_check(self) -> Dict[str, Any]:
        base = await super().health_check()
        try:
            # Test Redis connection
            await self.redis.ping()
            base["details"]["redis"] = "connected"
        except Exception as e:
            base["healthy"] = False
            base["details"]["redis"] = f"error: {str(e)}"
        return base
```

**Health Endpoint**:

```python
# luka_bot/handlers/health.py
@router.get("/health")
async def health_check():
    """Service health check endpoint."""
    checks = {
        "thread_service": await get_thread_service().health_check(),
        "llm_service": await get_llm_provider_fallback().get_provider_stats(),
        "elasticsearch": await get_elasticsearch_service().health_check(),
    }
    
    all_healthy = all(c.get("healthy", False) for c in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": checks
    }
```

**Estimated Effort**: 2-3 days

---

## 📋 Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
**Goal**: Low-risk improvements with immediate benefits

- [ ] Fix async/sync getter inconsistency (4 hours)
- [ ] Update `__init__.py` with all exports (30 minutes)
- [ ] Add comprehensive docstrings to all services (4 hours)

**Deliverables**:
- All getters are sync
- Complete service catalog in `__init__.py`
- Better documentation

**Success Metrics**:
- All tests pass
- No async warnings
- Developer satisfaction survey

---

### Phase 2: Architecture Improvements (Week 2)
**Goal**: Improve maintainability and testability

- [ ] Create `BaseService` class with DI (1 day)
- [ ] Create exception hierarchy (1 day)
- [ ] Define Protocol interfaces (2 days)
- [ ] Migrate 2-3 services to new patterns (2 days)

**Deliverables**:
- `base.py` with `BaseService`
- `exceptions.py` with hierarchy
- `protocols.py` with interfaces
- Proof of concept migrations

**Success Metrics**:
- Services can be mocked in tests
- Consistent error messages
- Type checking works

---

### Phase 3: Cleanup (Week 3)
**Goal**: Reduce boilerplate and technical debt

- [ ] Create singleton decorator (1 day)
- [ ] Migrate all services to decorator (2 days)
- [ ] Standardize error handling (2 days)
- [ ] Update all tests (2 days)

**Deliverables**:
- `registry.py` with decorator
- All services use new patterns
- Updated test suite

**Success Metrics**:
- ~90 lines of code eliminated
- Test coverage maintained
- No regressions

---

### Phase 4: Documentation & Polish (Optional)
**Goal**: Complete documentation and observability

- [ ] Add health checks to all services
- [ ] Create service integration guide
- [ ] Add telemetry/metrics
- [ ] Performance benchmarking

**Deliverables**:
- Health check endpoint
- Developer documentation
- Metrics dashboard

---

## 🧪 Testing Strategy

### Unit Tests
```python
# Test singleton behavior
def test_singleton():
    s1 = get_thread_service()
    s2 = get_thread_service()
    assert s1 is s2

# Test DI
@pytest.mark.asyncio
async def test_dependency_injection():
    mock_redis = AsyncMock()
    service = ThreadService(redis_client=mock_redis)
    await service.get_thread("test")
    mock_redis.get.assert_called()

# Test error handling
@pytest.mark.asyncio
async def test_error_handling():
    service = get_thread_service()
    with pytest.raises(ServiceValidationError):
        await service.get_thread("")
```

### Integration Tests
```python
@pytest.mark.integration
async def test_service_integration():
    # Test real Redis connection
    service = get_thread_service()
    thread = await service.create_thread(123, "Test")
    assert thread.thread_id is not None
```

### Performance Tests
```python
@pytest.mark.performance
async def test_singleton_performance():
    # Measure getter performance
    import time
    start = time.time()
    for _ in range(1000):
        get_thread_service()
    elapsed = time.time() - start
    assert elapsed < 0.1  # Should be fast
```

---

## 📊 Success Metrics

### Code Quality
- [ ] Lines of code: -100 lines (boilerplate removed)
- [ ] Test coverage: Maintain >80%
- [ ] Type checking: 0 errors
- [ ] Linter warnings: 0

### Developer Experience
- [ ] Service discovery time: <1 minute (via `__init__.py`)
- [ ] Test writing time: -50% (easier mocking)
- [ ] Debugging time: -30% (clear exceptions)

### System Reliability
- [ ] No regressions in existing features
- [ ] All tests pass
- [ ] No new bugs introduced

---

## 🚨 Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- Maintain backward compatibility
- Use optional parameters with defaults
- Deprecation warnings before removal
- Comprehensive testing

### Risk 2: Performance Impact
**Mitigation**:
- Benchmark before/after
- Profile critical paths
- No additional overhead in hot paths

### Risk 3: Incomplete Migration
**Mitigation**:
- Migrate incrementally
- One service at a time
- Roll back if issues arise
- Clear migration checklist

---

## 📚 References

- [PEP 544 – Protocols](https://peps.python.org/pep-0544/)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)

---

## 📞 Questions & Support

**For refactoring questions**:
1. Review this document
2. Check `README.md` in services directory
3. Ask in team chat
4. Create GitHub issue

**For reviewing changes**:
1. Check PR description
2. Review test coverage
3. Verify backward compatibility
4. Test locally

---

**Maintained by**: Luka Bot Team  
**Status**: Planning Phase  
**Next Review**: After Phase 1 completion  
**Last Updated**: 2025-10-13

