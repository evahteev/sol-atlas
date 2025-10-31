"""
Default values for GroupSettings (user default templates).

These defaults define the initial state when:
1. User creates their default template (/groups -> Default Settings)
2. User resets their defaults to factory settings

Used by:
- moderation_service.get_or_create_user_default_settings()
- handlers.group_admin.handle_user_defaults_reset()
"""

# ============================================================================
# Factory Defaults Dictionary
# ============================================================================

DEFAULT_GROUP_SETTINGS = {
    # Bot Behavior
    "silent_mode": True,  # Suppress bot service/system messages (no group messages, no DMs)
    "ai_assistant_enabled": False,  # Enable AI responses to mentions/replies
    "kb_indexation_enabled": True,  # Enable knowledge base indexation
    "language": "en",  # Default language for new groups (will be set from app locale on first creation)
    
    # Moderation
    "moderate_admins_enabled": False,  # Don't moderate admins by default
    "moderation_enabled": False,  # Conservative: off for new groups
    "reputation_enabled": False,  # Opt-in feature
    "auto_ban_enabled": False,  # Opt-in feature
    
    # Content Filters
    "delete_service_messages": False,  # Don't delete service messages
    "delete_links": False,  # Allow links
    "delete_images": False,  # Allow images
    "delete_videos": False,  # Allow videos
    "delete_stickers": False,  # Allow stickers
    "delete_forwarded": False,  # Allow forwarded messages
    
    # Stoplist
    "stoplist_enabled": False,  # Off until user enables
    "stoplist_words": [
        "spam",
        "scam",
        "phishing",
        "buy now",
        "click here",
        "limited offer",
        "congratulations you won"
    ],
    "stoplist_case_sensitive": False,
    "stoplist_auto_delete": True,  # Auto-delete messages matching stoplist
    
    # Moderation Prompt
    "moderation_prompt": """Evaluate messages for spam, advertising, offensive content, and rule violations.

Key rules:
- Spam and advertising: High severity
- Offensive language or personal attacks: High severity
- Off-topic or low-quality content: Medium severity
- Friendly discussions and questions: Allow

Be fair and consider context.""",
    
    # Thresholds
    "auto_delete_threshold": 8.0,  # Auto-delete score (0-10)
    "auto_warn_threshold": 5.0,  # Auto-warn score (0-10)
    "quality_threshold": 7.0,  # Quality reward score (0-10)
}

