"""
Content Detection Utilities - Helper functions for content filtering.

Provides fast pre-processing checks for:
- Links/URLs
- Pattern matching (regex)
- Stoplist words
"""
import re
from typing import List, Optional


def contains_links(text: str) -> bool:
    """
    Check if text contains URLs/links.
    
    Args:
        text: Message text
    
    Returns:
        True if contains links
    """
    # Common URL patterns
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    return bool(re.search(url_pattern, text, re.IGNORECASE))


def extract_links(text: str) -> List[str]:
    """
    Extract all links from text.
    
    Args:
        text: Message text
    
    Returns:
        List of URLs found
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    return re.findall(url_pattern, text, re.IGNORECASE)


def check_stoplist(text: str, stoplist_words: List[str], case_sensitive: bool = False) -> Optional[str]:
    """
    Check if text contains any stoplist words.
    
    Args:
        text: Message text
        stoplist_words: List of forbidden words/phrases
        case_sensitive: Whether to match case-sensitively
    
    Returns:
        First matched word or None
    """
    if not stoplist_words:
        return None
    
    search_text = text if case_sensitive else text.lower()
    
    for word in stoplist_words:
        search_word = word if case_sensitive else word.lower()
        if search_word in search_text:
            return word
    
    return None


def match_patterns(text: str, patterns: List[dict]) -> Optional[dict]:
    """
    Check if text matches any regex patterns.
    
    Args:
        text: Message text
        patterns: List of pattern dicts with format:
            {"pattern": "regex", "action": "delete"|"warn", "description": "..."}
    
    Returns:
        First matched pattern dict or None
    """
    if not patterns:
        return None
    
    for pattern_dict in patterns:
        pattern = pattern_dict.get("pattern")
        if not pattern:
            continue
        
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return pattern_dict
        except re.error:
            # Invalid regex, skip
            continue
    
    return None


def contains_media_type(content_type: str, media_types: List[str]) -> bool:
    """
    Check if message content type is in forbidden list.
    
    Args:
        content_type: Telegram content_type (e.g., "photo", "video", "sticker")
        media_types: List of forbidden media types
    
    Returns:
        True if forbidden
    """
    if not media_types:
        return False
    
    return content_type in media_types


def is_service_message(content_type: str, service_types: List[str]) -> bool:
    """
    Check if message is a service message type.
    
    Args:
        content_type: Telegram content_type
        service_types: List of service message types to filter
    
    Returns:
        True if is service message
    """
    service_message_types = [
        "new_chat_members",
        "left_chat_member",
        "new_chat_title",
        "new_chat_photo",
        "delete_chat_photo",
        "group_chat_created",
        "supergroup_chat_created",
        "channel_chat_created",
        "migrate_to_chat_id",
        "migrate_from_chat_id",
        "pinned_message",
        "invoice",
        "successful_payment",
        "connected_website",
        "voice_chat_started",
        "voice_chat_ended",
        "voice_chat_participants_invited",
        "proximity_alert_triggered",
        "video_chat_scheduled",
        "video_chat_started",
        "video_chat_ended",
        "video_chat_participants_invited",
    ]
    
    # Check if content type matches any service type in filter
    if content_type in service_message_types and content_type in service_types:
        return True
    
    return False


def sanitize_text(text: str) -> str:
    """
    Sanitize text for safe processing.
    
    Args:
        text: Input text
    
    Returns:
        Sanitized text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    text = text.strip()
    
    return text


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text.
    
    Args:
        text: Message text
    
    Returns:
        List of mentioned usernames (without @)
    """
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, text)


def extract_hashtags(text: str) -> List[str]:
    """
    Extract #hashtags from text.
    
    Args:
        text: Message text
    
    Returns:
        List of hashtags (without #)
    """
    hashtag_pattern = r'#(\w+)'
    return re.findall(hashtag_pattern, text)


def is_spam_pattern(text: str) -> bool:
    """
    Check for common spam patterns.
    
    Args:
        text: Message text
    
    Returns:
        True if likely spam
    """
    spam_indicators = [
        r'🚀.*join.*now',  # Pump group spam
        r'click.*here.*link',  # Clickbait
        r'earn\s+\$\d+',  # Money spam
        r'free.*money',  # Money spam
        r'limited.*time.*offer',  # Urgency spam
        r'act.*now.*before',  # Urgency spam
        r'(buy|sell).*signals?.*group',  # Trading signals spam
    ]
    
    for pattern in spam_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def count_caps(text: str) -> float:
    """
    Calculate percentage of capital letters.
    
    Args:
        text: Message text
    
    Returns:
        Percentage (0-100) of caps
    """
    if not text:
        return 0.0
    
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    
    caps = [c for c in letters if c.isupper()]
    return (len(caps) / len(letters)) * 100


def is_excessive_caps(text: str, threshold: float = 70.0) -> bool:
    """
    Check if message has excessive capital letters (shouting).
    
    Args:
        text: Message text
        threshold: Percentage threshold for caps
    
    Returns:
        True if excessive caps
    """
    return count_caps(text) > threshold


def contains_phone_number(text: str) -> bool:
    """
    Check if text contains phone numbers.
    
    Args:
        text: Message text
    
    Returns:
        True if contains phone number
    """
    # Simple phone number patterns
    phone_patterns = [
        r'\+\d{1,3}\s?\d{6,14}',  # International format
        r'\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4}',  # US format
        r'\(\d{3}\)\s?\d{3}[-\.\s]?\d{4}',  # (123) 456-7890
    ]
    
    for pattern in phone_patterns:
        if re.search(pattern, text):
            return True
    
    return False


def count_emojis(text: str) -> int:
    """
    Count number of emojis in text.
    
    Args:
        text: Message text
    
    Returns:
        Number of emojis
    """
    # Simple emoji detection (basic emoji ranges)
    emoji_pattern = r'[\U0001F300-\U0001F9FF]'
    return len(re.findall(emoji_pattern, text))


def is_excessive_emojis(text: str, threshold: int = 10) -> bool:
    """
    Check if message has excessive emojis.
    
    Args:
        text: Message text
        threshold: Number of emojis threshold
    
    Returns:
        True if excessive emojis
    """
    return count_emojis(text) > threshold

