"""
Message parsing utilities for extracting structured data from messages.

These helpers extract:
- @mentions
- #hashtags
- URLs
- Media info (future)
- Reply context (future)
"""
import re
from typing import List


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text.
    
    Args:
        text: Message text
    
    Returns:
        List of mentioned usernames (without @)
    
    Examples:
        >>> extract_mentions("Hello @john and @jane!")
        ['john', 'jane']
    """
    if not text:
        return []
    
    # Match @username (alphanumeric + underscore)
    mentions = re.findall(r'@(\w+)', text)
    return list(set(mentions))  # Remove duplicates


def extract_hashtags(text: str) -> List[str]:
    """
    Extract #hashtags from text.
    
    Args:
        text: Message text
    
    Returns:
        List of hashtags (without #)
    
    Examples:
        >>> extract_hashtags("Check out #python and #ai!")
        ['python', 'ai']
    """
    if not text:
        return []
    
    # Match #hashtag (alphanumeric + underscore)
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))  # Remove duplicates


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Message text
    
    Returns:
        List of URLs
    
    Examples:
        >>> extract_urls("Visit https://example.com and http://test.org")
        ['https://example.com', 'http://test.org']
    """
    if not text:
        return []
    
    # Match http/https URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates


def extract_all_metadata(text: str) -> dict:
    """
    Extract all metadata from text in one pass.
    
    Args:
        text: Message text
    
    Returns:
        Dict with mentions, hashtags, urls
    
    Examples:
        >>> extract_all_metadata("Hey @john! Check #python at https://python.org")
        {'mentions': ['john'], 'hashtags': ['python'], 'urls': ['https://python.org']}
    """
    return {
        "mentions": extract_mentions(text),
        "hashtags": extract_hashtags(text),
        "urls": extract_urls(text)
    }
