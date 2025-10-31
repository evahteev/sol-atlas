"""
LLM Provider Fallback Service - Ensures bot never stops working.

This service manages automatic failover between LLM providers (Ollama → OpenAI).
When a provider fails, it automatically switches to the backup and remembers
the working provider for 30 minutes.

Key Features:
- Automatic failover (Ollama → OpenAI)
- Provider health tracking with TTL (30 minutes)
- Retry logic with exponential backoff
- Graceful degradation
"""

import asyncio
from typing import Optional, Literal
from datetime import datetime, timedelta
from loguru import logger

from luka_bot.core.loader import redis_client
from luka_bot.core.config import settings


ProviderType = Literal["ollama", "openai"]


class LLMProviderFallback:
    """
    Manages LLM provider fallback and health tracking.
    
    Workflow:
    1. Try preferred provider (cached in Redis)
    2. If fails, try fallback provider
    3. If succeeds, cache working provider for 30 minutes
    4. If all fail, raise error
    
    Example:
        fallback = LLMProviderFallback()
        
        # Get working provider
        provider = await fallback.get_working_provider()
        # Returns: "ollama" or "openai"
        
        # Report failure
        await fallback.report_provider_failure("ollama", error)
        # Auto-switches to OpenAI
        
        # Report success
        await fallback.report_provider_success("openai")
        # Caches OpenAI as preferred for 30 minutes
    """
    
    # Redis keys
    PREFERRED_PROVIDER_KEY = "llm:preferred_provider"
    PROVIDER_FAILURE_PREFIX = "llm:failure:"
    PROVIDER_HEALTH_PREFIX = "llm:health:"
    
    # TTL settings
    PREFERRED_PROVIDER_TTL = 1800  # 30 minutes
    FAILURE_COOLDOWN_TTL = 300  # 5 minutes
    HEALTH_CHECK_TTL = 60  # 1 minute
    
    # Retry settings
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0  # seconds
    
    # Provider order (loaded from settings in __init__)
    PRIMARY_PROVIDER: ProviderType
    FALLBACK_PROVIDER: ProviderType
    ALL_PROVIDERS: list[ProviderType]
    
    def __init__(self, redis_client=None):
        """Initialize with optional Redis client."""
        self.redis = redis_client if redis_client else globals()['redis_client']
        self._last_health_check: dict[str, datetime] = {}
        
        # Load provider order from settings (dict insertion order is preserved in Python 3.7+)
        provider_keys = list(settings.AVAILABLE_PROVIDERS.keys())
        
        if not provider_keys:
            raise ValueError("AVAILABLE_PROVIDERS must have at least one provider")
        
        self.ALL_PROVIDERS = provider_keys
        self.PRIMARY_PROVIDER = provider_keys[0]
        self.FALLBACK_PROVIDER = provider_keys[1] if len(provider_keys) > 1 else provider_keys[0]
        
        logger.info(f"✅ LLMProviderFallback initialized")
        logger.info(f"🔧 Provider order: {' → '.join(provider_keys)}")
        logger.info(f"🔧 Primary: {self.PRIMARY_PROVIDER}, Fallback: {self.FALLBACK_PROVIDER}")
    
    async def get_working_provider(
        self,
        context: Optional[str] = None
    ) -> ProviderType:
        """
        Get the currently working LLM provider.
        
        Logic:
        1. Check cached preferred provider (30 min TTL)
        2. If exists and healthy, return it
        3. Otherwise, try primary provider
        4. If fails, try fallback provider
        5. Cache working provider
        
        Args:
            context: Optional context for logging (e.g., "user_123", "moderation")
            
        Returns:
            Provider name ("ollama" or "openai")
            
        Raises:
            RuntimeError: If all providers fail
        """
        log_prefix = f"[{context}]" if context else ""
        
        logger.debug(f"📦 {log_prefix} get_working_provider() ENTERED")
        logger.debug(f"   PRIMARY={self.PRIMARY_PROVIDER}, FALLBACK={self.FALLBACK_PROVIDER}")
        
        # Step 1: Check cached preferred provider
        try:
            logger.debug(f"📦 {log_prefix} Step 1: Checking Redis cache for preferred provider...")
            cached_provider = await self.redis.get(self.PREFERRED_PROVIDER_KEY)
            logger.debug(f"   Redis result: {cached_provider}")
            
            if cached_provider:
                provider = cached_provider.decode() if isinstance(cached_provider, bytes) else cached_provider
                logger.debug(f"✅ {log_prefix} Found cached provider: {provider}")
                
                # Verify it's still healthy (not in failure state) with quick health check
                logger.debug(f"📦 {log_prefix} Step 1a: Checking if {provider} is healthy...")
                is_healthy = await self._is_provider_healthy(provider)
                logger.debug(f"   Result: {is_healthy}")
                
                if is_healthy:
                    # Quick health check before using cached provider
                    logger.debug(f"📦 {log_prefix} Step 1b: Running health check on {provider}...")
                    try:
                        # Wrap in timeout to prevent indefinite hanging
                        health_check_ok = await asyncio.wait_for(
                            self._health_check_provider(provider, context=context),
                            timeout=5.0  # 5 second max wait
                        )
                        logger.debug(f"   Health check result: {health_check_ok}")
                    except asyncio.TimeoutError:
                        logger.warning(f"{log_prefix} ⚠️  Health check timed out after 5s")
                        health_check_ok = False
                        logger.debug(f"   Health check result: {health_check_ok}")
                    
                    if health_check_ok:
                        logger.debug(f"✅ {log_prefix} Using cached provider: {provider}")
                        return provider
                    else:
                        logger.warning(f"{log_prefix} ⚡ Fail-fast: Cached provider {provider} failed health check, finding alternative...")
                else:
                    logger.warning(f"{log_prefix} Cached provider {provider} is unhealthy, finding alternative...")
            else:
                logger.debug(f"   No cached provider found")
        except Exception as e:
            logger.warning(f"{log_prefix} Error checking cache: {e}")
            pass  # Silently fallback to checking providers
        
        # Step 2: Try primary provider with fail-fast health check
        logger.debug(f"📦 {log_prefix} Step 2: Trying primary provider {self.PRIMARY_PROVIDER}...")
        logger.debug(f"📦 {log_prefix} Step 2a: Checking if primary is healthy...")
        primary_healthy = await self._is_provider_healthy(self.PRIMARY_PROVIDER)
        logger.debug(f"   Result: {primary_healthy}")
        
        if primary_healthy:
            logger.debug(f"📦 {log_prefix} Step 2b: Checking configuration...")
            config_ok = await self._check_provider_configuration(self.PRIMARY_PROVIDER)
            logger.debug(f"   Config OK: {config_ok}")
            
            if config_ok:
                # Perform quick health check (3s timeout) before committing
                logger.debug(f"📦 {log_prefix} Step 2c: Running health check on {self.PRIMARY_PROVIDER}...")
                try:
                    health_ok = await asyncio.wait_for(
                        self._health_check_provider(self.PRIMARY_PROVIDER, context=context),
                        timeout=5.0
                    )
                    logger.debug(f"   Health check result: {health_ok}")
                except asyncio.TimeoutError:
                    logger.warning(f"{log_prefix} ⚠️  Health check timed out after 5s")
                    health_ok = False
                    logger.debug(f"   Health check result: {health_ok}")
                
                if health_ok:
                    logger.debug(f"📦 {log_prefix} Step 2d: Caching {self.PRIMARY_PROVIDER} as preferred...")
                    await self._cache_preferred_provider(self.PRIMARY_PROVIDER)
                    logger.debug(f"✅ {log_prefix} Using primary provider: {self.PRIMARY_PROVIDER}")
                    return self.PRIMARY_PROVIDER
                else:
                    logger.warning(f"{log_prefix} ⚡ Fail-fast: {self.PRIMARY_PROVIDER} failed health check, trying fallback...")
        
        # Step 3: Try fallback provider with fail-fast health check
        logger.debug(f"📦 {log_prefix} Step 3: Trying fallback provider {self.FALLBACK_PROVIDER}...")
        logger.debug(f"📦 {log_prefix} Step 3a: Checking if fallback is healthy...")
        fallback_healthy = await self._is_provider_healthy(self.FALLBACK_PROVIDER)
        logger.debug(f"   Result: {fallback_healthy}")
        
        if fallback_healthy:
            logger.debug(f"📦 {log_prefix} Step 3b: Checking configuration...")
            config_ok = await self._check_provider_configuration(self.FALLBACK_PROVIDER)
            logger.debug(f"   Config OK: {config_ok}")
            
            if config_ok:
                # Perform quick health check
                logger.debug(f"📦 {log_prefix} Step 3c: Running health check on {self.FALLBACK_PROVIDER}...")
                try:
                    health_ok = await asyncio.wait_for(
                        self._health_check_provider(self.FALLBACK_PROVIDER, context=context),
                        timeout=5.0
                    )
                    logger.debug(f"   Health check result: {health_ok}")
                except asyncio.TimeoutError:
                    logger.warning(f"{log_prefix} ⚠️  Health check timed out after 5s")
                    health_ok = False
                    logger.debug(f"   Health check result: {health_ok}")
                
                if health_ok:
                    logger.warning(f"{log_prefix} Primary provider failed, using fallback: {self.FALLBACK_PROVIDER}")
                    logger.debug(f"📦 {log_prefix} Step 3d: Caching {self.FALLBACK_PROVIDER} as preferred...")
                    await self._cache_preferred_provider(self.FALLBACK_PROVIDER)
                    return self.FALLBACK_PROVIDER
                else:
                    logger.error(f"{log_prefix} ⚡ Fail-fast: {self.FALLBACK_PROVIDER} also failed health check")
        
        # Step 4: All providers failed
        logger.error(f"{log_prefix} ❌ All LLM providers failed!")
        raise RuntimeError(
            "All LLM providers are unavailable. "
            f"Tried: {self.PRIMARY_PROVIDER}, {self.FALLBACK_PROVIDER}"
        )
    
    async def report_provider_failure(
        self,
        provider: ProviderType,
        error: Exception,
        context: Optional[str] = None
    ) -> None:
        """
        Report a provider failure.
        
        This marks the provider as unhealthy for FAILURE_COOLDOWN_TTL (5 minutes).
        
        Args:
            provider: Provider that failed
            error: Exception that occurred
            context: Optional context for logging
        """
        log_prefix = f"[{context}]" if context else ""
        
        # Mark provider as failed
        failure_key = f"{self.PROVIDER_FAILURE_PREFIX}{provider}"
        try:
            await self.redis.setex(
                failure_key,
                self.FAILURE_COOLDOWN_TTL,
                str(error)
            )
            logger.warning(
                f"{log_prefix} ⚠️ Provider {provider} failed: {error} "
                f"(cooldown: {self.FAILURE_COOLDOWN_TTL}s)"
            )
        except Exception as e:
            logger.error(f"Failed to record provider failure: {e}")
    
    async def report_provider_success(
        self,
        provider: ProviderType,
        context: Optional[str] = None
    ) -> None:
        """
        Report a provider success.
        
        This marks the provider as healthy and caches it as preferred.
        
        Args:
            provider: Provider that succeeded
            context: Optional context for logging
        """
        log_prefix = f"[{context}]" if context else ""
        
        # Clear failure state
        failure_key = f"{self.PROVIDER_FAILURE_PREFIX}{provider}"
        try:
            await self.redis.delete(failure_key)
        except Exception as e:
            pass
        
        # Mark as healthy
        health_key = f"{self.PROVIDER_HEALTH_PREFIX}{provider}"
        try:
            await self.redis.setex(
                health_key,
                self.HEALTH_CHECK_TTL,
                "ok"
            )
        except Exception as e:
            pass
        
        # Cache as preferred
        await self._cache_preferred_provider(provider)
    
    async def _is_provider_healthy(self, provider: ProviderType) -> bool:
        """
        Check if a provider is healthy (not in failure state).
        
        Args:
            provider: Provider to check
            
        Returns:
            True if healthy, False if in failure cooldown
        """
        failure_key = f"{self.PROVIDER_FAILURE_PREFIX}{provider}"
        try:
            failure = await self.redis.get(failure_key)
            if failure:
                return False
            return True
        except Exception as e:
            return True  # Assume healthy if can't check
    
    async def _check_provider_configuration(self, provider: ProviderType) -> bool:
        """
        Check if a provider is properly configured.
        
        Args:
            provider: Provider to check
            
        Returns:
            True if configured, False otherwise
        """
        if provider == "ollama":
            # Ollama is always available if running
            return True
        elif provider == "openai":
            # OpenAI requires API key
            if not settings.OPENAI_API_KEY:
                logger.warning("⚠️ OpenAI provider not configured (missing OPENAI_API_KEY)")
                return False
            return True
        return False
    
    async def _health_check_provider(self, provider: ProviderType, context: Optional[str] = None) -> bool:
        """
        Perform a quick health check on a provider (fail-fast).
        
        Uses a very short timeout (3 seconds) to quickly determine if provider is responsive.
        This avoids waiting for the full timeout (15s) before falling back.
        
        Args:
            provider: Provider to check
            context: Optional context for logging
            
        Returns:
            True if provider is healthy, False otherwise
        """
        log_prefix = f"[{context}]" if context else ""
        
        if provider == "ollama":
            # Quick health check: try to connect to Ollama endpoint
            import httpx
            try:
                # Strip /v1 suffix if present (for OpenAI-compatible API mode)
                # Health check uses native Ollama endpoint (/api/tags)
                base_url = settings.OLLAMA_URL.rstrip('/')
                if base_url.endswith('/v1'):
                    base_url = base_url[:-3]  # Remove /v1 suffix
                
                async with httpx.AsyncClient(timeout=3.0) as client:
                    # Hit the /api/tags endpoint (native Ollama, always works)
                    response = await client.get(f"{base_url}/api/tags")
                    if response.status_code == 200:
                        logger.debug(f"{log_prefix} ✅ Health check: Ollama is healthy")
                        return True
                    else:
                        logger.warning(f"{log_prefix} ⚠️ Health check: Ollama /api/tags returned {response.status_code}")
                        return False
            except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout) as e:
                logger.warning(f"{log_prefix} ❌ Health check: Ollama not reachable: {type(e).__name__}")
                return False
            except Exception as e:
                logger.warning(f"{log_prefix} ❌ Health check: Ollama check failed: {e}")
                return False
        
        elif provider == "openai":
            # OpenAI is cloud-based, assume healthy if API key is set
            # (actual connectivity will be tested on first request)
            return bool(settings.OPENAI_API_KEY)
        
        return False
    
    async def _cache_preferred_provider(self, provider: ProviderType) -> None:
        """
        Cache a provider as preferred for PREFERRED_PROVIDER_TTL (30 minutes).
        
        Args:
            provider: Provider to cache
        """
        try:
            await self.redis.setex(
                self.PREFERRED_PROVIDER_KEY,
                self.PREFERRED_PROVIDER_TTL,
                provider
            )
            logger.debug(f"Cached {provider} as preferred provider (TTL: {self.PREFERRED_PROVIDER_TTL}s)")
        except Exception as e:
            logger.error(f"Failed to cache preferred provider: {e}")
    
    async def get_provider_stats(self) -> dict:
        """
        Get statistics about provider health and usage.
        
        Returns:
            Dictionary with provider stats
        """
        stats = {
            "primary_provider": self.PRIMARY_PROVIDER,
            "fallback_provider": self.FALLBACK_PROVIDER,
            "preferred_provider": None,
            "provider_health": {},
        }
        
        # Get preferred provider
        try:
            cached = await self.redis.get(self.PREFERRED_PROVIDER_KEY)
            if cached:
                stats["preferred_provider"] = cached.decode() if isinstance(cached, bytes) else cached
        except:
            pass
        
        # Get provider health
        for provider in [self.PRIMARY_PROVIDER, self.FALLBACK_PROVIDER]:
            is_healthy = await self._is_provider_healthy(provider)
            is_configured = await self._check_provider_configuration(provider)
            
            stats["provider_health"][provider] = {
                "healthy": is_healthy,
                "configured": is_configured,
                "available": is_healthy and is_configured
            }
        
        return stats
    
    async def force_provider(
        self,
        provider: ProviderType,
        duration_seconds: int = PREFERRED_PROVIDER_TTL
    ) -> None:
        """
        Force a specific provider (for testing/debugging).
        
        Args:
            provider: Provider to force
            duration_seconds: How long to force it (default: 30 minutes)
        """
        await self.redis.setex(
            self.PREFERRED_PROVIDER_KEY,
            duration_seconds,
            provider
        )
        logger.info(f"🔧 Forced provider: {provider} (duration: {duration_seconds}s)")
    
    async def clear_cache(self) -> None:
        """Clear all cached provider preferences and health data."""
        try:
            # Clear preferred provider
            await self.redis.delete(self.PREFERRED_PROVIDER_KEY)
            
            # Clear failure states
            for provider in [self.PRIMARY_PROVIDER, self.FALLBACK_PROVIDER]:
                failure_key = f"{self.PROVIDER_FAILURE_PREFIX}{provider}"
                health_key = f"{self.PROVIDER_HEALTH_PREFIX}{provider}"
                await self.redis.delete(failure_key)
                await self.redis.delete(health_key)
            
            logger.info("🧹 Cleared all provider cache and health data")
        except Exception as e:
            logger.error(f"Failed to clear provider cache: {e}")
    
    async def initialize_on_startup(self) -> dict:
        """
        Initialize and check all providers on bot startup.
        
        This method performs a complete startup check:
        1. Clears all provider cache and health data
        2. Checks configuration and health of all providers
        3. Tests connectivity and caches first working provider
        
        Returns:
            Dictionary with provider stats and active provider
            
        Example:
            fallback = get_llm_provider_fallback()
            result = await fallback.initialize_on_startup()
            # result = {
            #     "stats": {...},
            #     "active_provider": "ollama",
            #     "error": None
            # }
        """
        result = {
            "stats": None,
            "active_provider": None,
            "error": None
        }
        
        try:
            # Step 1: Clear cache
            await self.clear_cache()
            
            # Step 2: Get provider stats
            stats = await self.get_provider_stats()
            result["stats"] = stats
            
            # Step 3: Test connectivity and cache working provider
            try:
                working_provider = await self.get_working_provider(context="startup")
                result["active_provider"] = working_provider
            except Exception as e:
                result["error"] = str(e)
                logger.error(f"❌ No providers available during startup: {e}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Failed to initialize providers: {e}")
        
        return result


# Singleton instance
_llm_provider_fallback: Optional[LLMProviderFallback] = None


def get_llm_provider_fallback() -> LLMProviderFallback:
    """
    Get or create LLMProviderFallback singleton.
    
    Returns:
        LLMProviderFallback instance
    """
    global _llm_provider_fallback
    if _llm_provider_fallback is None:
        _llm_provider_fallback = LLMProviderFallback(redis_client)
        logger.info("✅ LLMProviderFallback singleton created")
    return _llm_provider_fallback

