"""
Thread name generator service - Lazy thread creation.

Generates meaningful thread names from user's first message.
Uses LLM with fallbacks for reliability.
"""
import re
from datetime import datetime
from typing import Optional

from loguru import logger


# Fallback names by language
FALLBACK_NAMES = {
    "en": ["General Chat", "Quick Question", "New Conversation", "Discussion"],
    "ru": ["Общий чат", "Быстрый вопрос", "Новый разговор", "Обсуждение"],
}


async def generate_thread_name(
    message: str,
    language: str = "en",
    max_length: int = 20
) -> str:
    """
    Generate a meaningful thread name from user's first message.
    
    Strategy:
    1. Try LLM-based generation (fast summarization)
    2. Fallback to smart truncation
    3. Fallback to generic name
    
    Args:
        message: User's first message
        language: Language code (en, ru)
        max_length: Maximum name length
        
    Returns:
        Thread name (3-20 characters, title case)
    """
    # Clean message
    message = message.strip()
    
    # Handle empty/very short messages
    if len(message) < 3:
        return _get_fallback_name(language)
    
    # Try LLM generation
    try:
        llm_name = await _generate_with_llm(message, language, max_length)
        if llm_name and len(llm_name) >= 3:
            logger.info(f"✅ LLM generated name: '{llm_name}' from '{message[:30]}...'")
            return llm_name
    except Exception as e:
        logger.warning(f"⚠️  LLM name generation failed: {e}")
    
    # Fallback to smart truncation
    truncated = _smart_truncate(message, max_length)
    if truncated and len(truncated) >= 3:
        logger.info(f"📝 Truncated name: '{truncated}' from '{message[:30]}...'")
        return truncated
    
    # Final fallback
    fallback = _get_fallback_name(language)
    logger.info(f"🔄 Using fallback name: '{fallback}'")
    return fallback


async def _generate_with_llm(
    message: str,
    language: str,
    max_length: int
) -> Optional[str]:
    """
    Generate thread name using LLM with direct API call.
    
    FIX 10: Use pydantic-ai directly instead of going through llm_service
    to avoid history pollution and user_id=0 issues.
    """
    try:
        from pydantic_ai import Agent
        from luka_bot.services.llm_model_factory import create_name_generator_model
        
        # Create model with automatic fallback (Ollama → OpenAI)
        model, system_prompt = await create_name_generator_model(
            language=language,
            max_length=max_length,
            context="name_generator"
        )
        
        # Create simple agent
        agent: Agent[None, str] = Agent(
            model,
            system_prompt=system_prompt,
            retries=1
        )
        
        # Run synchronously (no streaming to avoid interruption issues)
        result = await agent.run(f"Message: {message[:100]}")
        
        # FIX 16: Clean up response - use result.output (not result.data)
        name = _clean_llm_response(result.output, max_length)
        return name
        
    except Exception as e:
        logger.warning(f"⚠️  LLM name generation error: {e}")
        return None


def _clean_llm_response(response: str, max_length: int) -> Optional[str]:
    """
    Clean LLM response to extract just the name.
    
    Removes:
    - Quotes
    - Extra punctuation
    - Markdown
    - Extra whitespace
    """
    if not response:
        return None
    
    # Take first line only
    name = response.split('\n')[0].strip()
    
    # Remove quotes
    name = name.strip('"\'`')
    
    # Remove markdown
    name = re.sub(r'\*\*?|__|~~', '', name)
    
    # Remove trailing punctuation (but keep internal punctuation)
    name = name.rstrip('.,!?;:')
    
    # Truncate if needed
    if len(name) > max_length:
        name = name[:max_length].rsplit(' ', 1)[0]  # Break at word boundary
    
    # Title case
    name = _to_title_case(name)
    
    return name if len(name) >= 3 else None


def _smart_truncate(message: str, max_length: int) -> Optional[str]:
    """
    Smart truncation with word boundaries.
    
    Extracts key words and creates a sensible name.
    """
    # Remove common question words
    stop_words = {
        'en': ['what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 'the', 'a', 'an', 'can', 'could', 'would', 'should', 'do', 'does'],
        'ru': ['что', 'как', 'почему', 'когда', 'где', 'кто', 'это', 'в', 'на'],
    }
    
    # Split into words
    words = message.lower().split()
    
    # Filter stop words (keep first few meaningful words)
    meaningful_words = []
    for word in words:
        # Remove punctuation
        clean_word = re.sub(r'[^\w\s-]', '', word)
        if not clean_word:
            continue
        
        # Skip stop words (but keep if we have too few words)
        is_stop = any(clean_word in stops for stops in stop_words.values())
        if not is_stop or len(meaningful_words) < 2:
            meaningful_words.append(clean_word)
        
        # Stop when we have enough
        if len(' '.join(meaningful_words)) >= max_length:
            break
    
    if not meaningful_words:
        return None
    
    # Join and truncate
    name = ' '.join(meaningful_words[:4])  # Max 4 words
    if len(name) > max_length:
        name = name[:max_length].rsplit(' ', 1)[0]
    
    # Title case
    name = _to_title_case(name)
    
    return name if len(name) >= 3 else None


def _to_title_case(text: str) -> str:
    """Convert to title case properly."""
    # Special handling for acronyms
    words = text.split()
    titled = []
    
    for word in words:
        # Keep acronyms uppercase
        if word.isupper() and len(word) <= 4:
            titled.append(word)
        else:
            titled.append(word.capitalize())
    
    return ' '.join(titled)


def _get_fallback_name(language: str) -> str:
    """
    Get a fallback name when all else fails.
    
    Returns a generic name with timestamp to ensure uniqueness.
    """
    lang = language if language in FALLBACK_NAMES else "en"
    base_names = FALLBACK_NAMES[lang]
    
    # Use first fallback name (most generic)
    base_name = base_names[0]
    
    # Add hour for some uniqueness without being too verbose
    hour = datetime.now().strftime("%H:%M")
    
    return f"{base_name} {hour}"

