"""
LLM Model Factory - Creates LLM models with automatic provider fallback.

This module provides a centralized way to create LLM models that automatically
fall back from Ollama to OpenAI when the primary provider fails.

Key Features:
- Automatic provider selection (Ollama → OpenAI)
- Provider health tracking
- Failure reporting and recovery
- Consistent model settings
"""

from typing import Optional, Literal
from loguru import logger
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.settings import ModelSettings

from luka_bot.core.config import settings
from luka_bot.services.llm_provider_fallback import get_llm_provider_fallback, ProviderType


async def create_llm_model_with_fallback(
    context: Optional[str] = None,
    model_settings: Optional[ModelSettings] = None,
    force_provider: Optional[ProviderType] = None
) -> OpenAIModel:
    """
    Create an LLM model with automatic provider fallback.
    
    Workflow:
    1. Get working provider from fallback service (Ollama or OpenAI)
    2. Create provider-specific model
    3. Return model ready for use
    
    Args:
        context: Optional context for logging (e.g., "user_123", "moderation")
        model_settings: Optional custom model settings (temperature, max_tokens, etc.)
        force_provider: Optional forced provider (for testing/debugging)
        
    Returns:
        OpenAIModel configured for the selected provider
        
    Example:
        # Basic usage
        model = await create_llm_model_with_fallback(context="user_123")
        
        # With custom settings
        custom_settings = ModelSettings(temperature=0.1, max_tokens=500)
        model = await create_llm_model_with_fallback(
            context="moderation",
            model_settings=custom_settings
        )
        
        # Force specific provider (testing)
        model = await create_llm_model_with_fallback(
            force_provider="openai"
        )
    """
    log_prefix = f"[{context}]" if context else ""
    
    logger.debug(f"📦 {log_prefix} create_llm_model_with_fallback() ENTERED")
    logger.debug(f"   force_provider={force_provider}, has_custom_settings={model_settings is not None}")
    
    try:
        # Get fallback service
        logger.debug(f"📦 {log_prefix} Step 1: Getting fallback service...")
        fallback = get_llm_provider_fallback()
        logger.debug(f"✅ {log_prefix} Fallback service obtained: {type(fallback).__name__}")
        
        # Determine which provider to use
        if force_provider:
            provider_name = force_provider
            logger.info(f"{log_prefix} Using forced provider: {provider_name}")
        else:
            logger.debug(f"📦 {log_prefix} Step 2: Calling fallback.get_working_provider()...")
            logger.debug(f"   This will health check Ollama first...")
            provider_name = await fallback.get_working_provider(context=context)
            logger.debug(f"✅ {log_prefix} Got working provider: {provider_name}")
        
        # Create provider-specific model
        logger.debug(f"📦 {log_prefix} Step 3: Creating {provider_name} model...")
        try:
            if provider_name == "ollama":
                logger.debug(f"   Calling _create_ollama_model()...")
                model = await _create_ollama_model(model_settings)
                logger.debug(f"✅ Ollama model created")
            elif provider_name == "openai":
                logger.debug(f"   Calling _create_openai_model()...")
                model = await _create_openai_model(model_settings)
                logger.debug(f"✅ OpenAI model created")
            else:
                raise ValueError(f"Unknown provider: {provider_name}")
            
            logger.debug(f"📦 {log_prefix} Step 4: Reporting success...")
            await fallback.report_provider_success(provider_name, context=context)
            logger.info(f"✅ {log_prefix} Created {provider_name.upper()} model")
            return model
            
        except Exception as e:
            # Report failure to fallback service
            logger.error(f"{log_prefix} ❌ Failed to create {provider_name} model: {e}")
            await fallback.report_provider_failure(provider_name, e, context=context)
            raise
    
    except Exception as outer_error:
        logger.error(f"❌ {log_prefix} FATAL: create_llm_model_with_fallback() failed: {outer_error}", exc_info=True)
        raise


async def _create_ollama_model(
    custom_settings: Optional[ModelSettings] = None
) -> OpenAIModel:
    """
    Create Ollama model.
    
    Args:
        custom_settings: Optional custom model settings
        
    Returns:
        OpenAIModel configured for Ollama
    """
    # Create Ollama provider with /v1 suffix for OpenAI-compatible API
    # Health check uses base URL without /v1 (native Ollama endpoint)
    ollama_base_url = settings.OLLAMA_URL.rstrip('/')
    if not ollama_base_url.endswith('/v1'):
        ollama_base_url = f"{ollama_base_url}/v1"
    
    ollama_provider = OllamaProvider(base_url=ollama_base_url)
    
    # Use custom settings or defaults
    if custom_settings:
        model_settings = custom_settings
    else:
        model_settings = ModelSettings(
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            frequency_penalty=settings.LLM_FREQUENCY_PENALTY,
            presence_penalty=settings.LLM_PRESENCE_PENALTY,
            stop_sequences=["\n\n\n", "User:", "Assistant:"],
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    # Create model
    model = OpenAIModel(
        model_name=settings.OLLAMA_MODEL_NAME,
        provider=ollama_provider,
        settings=model_settings
    )
    
    return model


async def _create_openai_model(
    custom_settings: Optional[ModelSettings] = None
) -> OpenAIModel:
    """
    Create OpenAI model.
    
    Args:
        custom_settings: Optional custom model settings
        
    Returns:
        OpenAIModel configured for OpenAI
        
    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    # Verify API key is configured
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OpenAI provider requires OPENAI_API_KEY. "
            "Set it in .env: OPENAI_API_KEY=sk-..."
        )
    
    # Use custom settings or defaults
    if custom_settings:
        model_settings = custom_settings
    else:
        model_settings = ModelSettings(
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            frequency_penalty=settings.LLM_FREQUENCY_PENALTY,
            presence_penalty=settings.LLM_PRESENCE_PENALTY,
            stop_sequences=["\n\n\n", "User:", "Assistant:"],
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.OPENAI_TIMEOUT
        )
    
    # Create OpenAI provider
    from pydantic_ai.providers.openai import OpenAIProvider
    
    # Configure OpenAI provider with API key
    openai_provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL if settings.OPENAI_BASE_URL else None
    )
    
    # Create model using the provider
    model = OpenAIModel(
        model_name=settings.OPENAI_MODEL_NAME,
        provider=openai_provider,
        settings=model_settings
    )
    
    return model


async def create_moderation_model(
    context: Optional[str] = None
) -> OpenAIModel:
    """
    Create a model optimized for moderation (low temperature, JSON mode).
    
    Args:
        context: Optional context for logging
        
    Returns:
        OpenAIModel optimized for moderation tasks
    """
    # Moderation-specific settings
    moderation_settings = ModelSettings(
        temperature=0.1,  # Low temp for consistent moderation
        max_tokens=500,  # Shorter responses for moderation
        timeout=30.0  # Shorter timeout for moderation
    )
    
    return await create_llm_model_with_fallback(
        context=context or "moderation",
        model_settings=moderation_settings
    )


async def create_name_generator_model(
    language: str = "en",
    max_length: int = 20,
    context: Optional[str] = None
) -> tuple[OpenAIModel, str]:
    """
    Create a model optimized for thread name generation.
    
    Args:
        language: Language for name generation
        max_length: Maximum length for generated names
        context: Optional context for logging
        
    Returns:
        Tuple of (OpenAIModel, system_prompt)
    """
    # Name generation-specific settings
    name_gen_settings = ModelSettings(
        temperature=0.7,  # Some creativity for names
        max_tokens=50,  # Very short responses
        timeout=15.0  # Quick timeout
    )
    
    # System prompts by language
    system_prompts = {
        "en": f"Generate a concise thread title (max {max_length} chars, 3-5 words). Return ONLY the title with no quotes, punctuation, or explanation. Use title case.",
        "ru": f"Создайте краткий заголовок темы (макс {max_length} символов, 3-5 слов). Верните ТОЛЬКО заголовок без кавычек, знаков препинания и пояснений.",
    }
    
    system_prompt = system_prompts.get(language, system_prompts["en"])
    
    model = await create_llm_model_with_fallback(
        context=context or "name_generator",
        model_settings=name_gen_settings
    )
    
    return model, system_prompt


async def get_provider_status() -> dict:
    """
    Get status of all LLM providers.
    
    Returns:
        Dictionary with provider status information
    """
    fallback = get_llm_provider_fallback()
    return await fallback.get_provider_stats()

