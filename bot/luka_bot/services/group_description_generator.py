"""
Group description generator - LLM-based tagline creation.

Generates compelling group descriptions for /help display.
Similar to thread_name_generator but for group profiles.
"""
import re
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime


FALLBACK_DESCRIPTIONS = {
    "en": [
        "A Telegram community powered by AI",
        "Your friendly neighborhood group chat",
        "Where great conversations happen",
        "Community discussions and knowledge sharing"
    ],
    "ru": [
        "Telegram сообщество с AI поддержкой",
        "Ваш дружелюбный групповой чат",
        "Где происходят отличные беседы",
        "Обсуждения и обмен знаниями"
    ],
}


async def generate_group_description(
    group_title: str,
    group_metadata: Dict[str, Any],
    language: str = "en",
    max_length: int = 120
) -> str:
    """
    Generate compelling group description/tagline.
    
    Uses:
    - Existing Telegram description (if available)
    - Group statistics (member count, activity)
    - LLM generation (creates engaging tagline)
    
    Args:
        group_title: Group name
        group_metadata: Dict with group info (description, member_count, etc.)
        language: Language code
        max_length: Maximum description length
        
    Returns:
        Engaging group description
    """
    # 1. Try existing Telegram description
    if group_metadata.get("description"):
        desc = group_metadata["description"].strip()
        if desc and len(desc) >= 10:
            if len(desc) > max_length:
                desc = desc[:max_length-3] + "..."
            logger.info(f"✅ Using Telegram description for '{group_title}'")
            return desc
    
    # 2. Try LLM generation
    try:
        llm_desc = await _generate_with_llm(
            group_title, 
            group_metadata, 
            language, 
            max_length
        )
        if llm_desc:
            logger.info(f"✅ LLM generated description for '{group_title}'")
            return llm_desc
    except Exception as e:
        logger.warning(f"⚠️  LLM description generation failed: {e}")
    
    # 3. Fallback to generic description
    fallback = _get_fallback_description(language, group_metadata)
    logger.info(f"🔄 Using fallback description for '{group_title}'")
    return fallback


async def _generate_with_llm(
    group_title: str,
    group_metadata: Dict[str, Any],
    language: str,
    max_length: int
) -> Optional[str]:
    """Generate group description using LLM."""
    try:
        from pydantic_ai import Agent
        from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
        
        # Create model with automatic fallback
        model = await create_llm_model_with_fallback(
            context="group_description_generator"
        )
        
        # Build context
        member_count = group_metadata.get("member_count", "?")
        message_count = group_metadata.get("message_count", 0)
        group_type = group_metadata.get("group_type", "group")
        
        # System prompt
        if language == "ru":
            system_prompt = f"""Ты копирайтер. Создай короткое (до {max_length} символов) привлекательное описание для Telegram группы.

Правила:
- Одно предложение
- Без цитат и кавычек  
- Профессионально и дружелюбно
- Подчеркни community aspect
- Будь креативным и запоминающимся"""
            user_prompt = f"Группа: {group_title} ({member_count} участников, {message_count} сообщений в базе знаний)"
        else:
            system_prompt = f"""You are a copywriter. Create a short (max {max_length} chars) compelling description for a Telegram group.

Rules:
- One sentence only
- No quotes or quotation marks
- Professional yet friendly tone
- Emphasize community aspect
- Be creative and memorable"""
            user_prompt = f"Group: {group_title} ({member_count} members, {message_count} messages in knowledge base)"
        
        # Create agent
        agent: Agent[None, str] = Agent(
            model,
            system_prompt=system_prompt,
            retries=1
        )
        
        # Generate with timeout
        result = await agent.run(user_prompt)
        
        # Clean response
        description = _clean_llm_response(result.output, max_length)
        return description
        
    except Exception as e:
        logger.warning(f"⚠️  LLM description error: {e}")
        return None


def _clean_llm_response(response: str, max_length: int) -> Optional[str]:
    """
    Clean LLM response to extract just the description.
    
    Removes:
    - Quotes
    - Extra punctuation at end
    - Markdown
    - Extra whitespace
    """
    if not response:
        return None
    
    # Take first line only
    desc = response.split('\n')[0].strip()
    
    # Remove quotes
    desc = desc.strip('"\'`')
    
    # Remove markdown
    desc = re.sub(r'\*\*?|__|~~', '', desc)
    
    # Remove trailing punctuation (but keep internal punctuation and emoji)
    desc = desc.rstrip('.!?;:')
    
    # Truncate if needed
    if len(desc) > max_length:
        desc = desc[:max_length-3] + "..."
    
    return desc if len(desc) >= 10 else None


def _get_fallback_description(language: str, group_metadata: Dict[str, Any]) -> str:
    """
    Get fallback description with some personalization.
    
    Personalizes based on group size and activity.
    """
    lang = language if language in FALLBACK_DESCRIPTIONS else "en"
    base_descriptions = FALLBACK_DESCRIPTIONS[lang]
    
    # Personalize based on size
    member_count = group_metadata.get("member_count", 0)
    
    # Try to convert to int if it's a string
    if isinstance(member_count, str):
        try:
            member_count = int(member_count)
        except (ValueError, TypeError):
            member_count = 0
    
    if isinstance(member_count, int):
        if member_count > 100:
            # Large group - emphasize community
            desc = base_descriptions[0]
        elif member_count > 10:
            # Medium group - emphasize friendliness
            desc = base_descriptions[1]
        else:
            # Small group - emphasize conversations
            desc = base_descriptions[2]
    else:
        desc = base_descriptions[0]
    
    return desc

