"""
Group Settings Model - Configuration for group moderation and behavior.

Stores per-group/topic settings for:
- Pre-processing filters (stoplist, regex, service messages)
- Background moderation rules (moderation_prompt)
- Reputation system configuration
- Auto-moderation thresholds

Can also be used as USER DEFAULTS with special ID pattern:
- group_id = user_id (positive)
- topic_id = None
- is_user_default = True
- Redis key: "user_default_group_settings:{user_id}"

When used as user defaults, these are TEMPLATE settings applied to new groups.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class GroupSettings:
    """
    Settings for group/topic moderation and behavior.
    
    Separate from Thread (conversation config) - this handles:
    - Message filtering (before LLM)
    - Background moderation (all messages)
    - Reputation system rules
    
    Can also serve as user's default template for new groups.
    """
    
    # ============================================================================
    # Identity
    # ============================================================================
    
    group_id: int  # Telegram group ID (negative) OR user_id (positive for defaults)
    topic_id: Optional[int] = None  # None = group-wide, set for specific topic
    
    # Flag to identify if this is a user default template
    is_user_default: bool = False  # True if this is user's default template
    
    # ============================================================================
    # BOT BEHAVIOR SETTINGS (New: Group-level bot control)
    # ============================================================================
    
    # Silent mode - suppress bot's service/system messages in GROUP
    # This is a GROUP setting - it only affects messages sent TO THE GROUP, not DMs
    # When ON: No bot messages in GROUP (silent), but DM sent to admin with welcome + controls
    # When OFF: Bot sends system messages in GROUP (welcome, topic greetings, etc.), no DM
    silent_mode: bool = True  # Changed from False to match factory defaults
    
    # AI Assistant toggle - enable/disable AI responses to @mentions
    ai_assistant_enabled: bool = False  # Changed from True to match factory defaults
    
    # Knowledge Base indexation - enable/disable message indexing for search
    kb_indexation_enabled: bool = True
    
    # Default language for new groups (used in user defaults)
    # When user adds bot to a group, this language is applied to the group
    language: str = "en"  # "en" or "ru"
    
    # ============================================================================
    # GROUP PROFILE (for /help display)
    # ============================================================================
    
    # Custom group description/tagline for /help display
    # If None, will be auto-generated from group metadata or LLM
    custom_description: Optional[str] = None
    
    # Custom group avatar file_id (override Telegram's default)
    # If None, uses Telegram's group photo from metadata
    custom_avatar_file_id: Optional[str] = None
    
    # Auto-generated tagline (cached LLM output)
    # Regenerated periodically or when group changes significantly
    generated_tagline: Optional[str] = None
    generated_tagline_updated: Optional[datetime] = None
    
    # ============================================================================
    # MODERATION SETTINGS
    # ============================================================================
    
    # Moderate admins - whether moderation rules apply to group admins
    moderate_admins_enabled: bool = False
    
    # ============================================================================
    # PRE-PROCESSING FILTERS (Fast, rule-based)
    # ============================================================================
    
    # Auto-delete service messages
    delete_service_messages: bool = False
    service_message_types: list[str] = field(default_factory=list)
    # Examples: ["new_chat_members", "left_chat_member", "pinned_message", 
    #            "voice_chat_started", "voice_chat_ended", "new_chat_title"]
    
    # Stoplist (word/phrase blocking)
    stoplist_enabled: bool = False
    stoplist_words: list[str] = field(default_factory=list)
    stoplist_case_sensitive: bool = False
    stoplist_auto_delete: bool = True  # Auto-delete messages matching stoplist
    
    # Content type filtering
    delete_links: bool = False
    delete_images: bool = False
    delete_videos: bool = False
    delete_stickers: bool = False
    delete_forwarded: bool = False
    
    # Pattern matching (regex)
    pattern_filters: list[dict] = field(default_factory=list)
    # Format: [{"pattern": "regex", "action": "delete"|"warn", "description": "..."}]
    # Example: {"pattern": "http://bit\\.ly/.*", "action": "delete", "description": "Bit.ly links"}
    
    # ============================================================================
    # BACKGROUND MODERATION (LLM-based, for ALL messages)
    # ============================================================================
    
    moderation_enabled: bool = True
    moderation_prompt: Optional[str] = None  # ⭐ KEY FIELD - Used for ALL messages
    
    # Default behavior if moderation_prompt is None:
    # Use a general-purpose moderation template
    
    # Moderation thresholds (0-10 scale from LLM)
    auto_delete_threshold: float = 8.0  # If violation_score >= 8, auto-delete
    auto_warn_threshold: float = 5.0    # If violation_score >= 5, warn user
    quality_threshold: float = 7.0      # If quality_score >= 7, award points
    
    # ============================================================================
    # REPUTATION SYSTEM
    # ============================================================================
    
    reputation_enabled: bool = True
    
    # Point rewards
    points_per_helpful_message: int = 5
    points_per_quality_reply: int = 10
    points_per_achievement: int = 50
    
    # Penalties
    violation_penalty: int = -10
    spam_penalty: int = -25
    toxic_penalty: int = -50
    
    # Banning rules
    auto_ban_enabled: bool = False
    violations_before_ban: int = 3
    ban_duration_hours: int = 24  # 0 = permanent
    
    # Achievements
    achievements_enabled: bool = True
    achievement_rules: list[dict] = field(default_factory=list)
    # Format: [{"id": "helper_10", "name": "Helper", "condition": "helpful_messages >= 10", 
    #           "description": "Helped 10 times", "points": 50, "icon": "🌟"}]
    
    # ============================================================================
    # NOTIFICATIONS
    # ============================================================================
    
    notify_violations: bool = True  # Send DM to user on violation
    notify_achievements: bool = True  # Send message on achievement
    notify_bans: bool = True  # Announce bans in group
    
    public_warnings: bool = False  # Show warnings publicly in group
    public_achievements: bool = True  # Announce achievements in group
    
    # ============================================================================
    # METADATA
    # ============================================================================
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: int = 0  # Admin user_id who created/configured
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "group_id": str(self.group_id),
            "topic_id": str(self.topic_id) if self.topic_id is not None else "",
            
            # Identity flags
            "is_user_default": str(self.is_user_default),
            
            # Bot behavior settings
            # Note: silent_addition was removed - silent_mode now handles both cases
            "silent_mode": str(self.silent_mode),
            "ai_assistant_enabled": str(self.ai_assistant_enabled),
            "kb_indexation_enabled": str(self.kb_indexation_enabled),
            "language": self.language,
            
            # Group profile
            "custom_description": self.custom_description or "",
            "custom_avatar_file_id": self.custom_avatar_file_id or "",
            "generated_tagline": self.generated_tagline or "",
            "generated_tagline_updated": self.generated_tagline_updated.isoformat() if self.generated_tagline_updated else "",
            
            # Moderation settings
            "moderate_admins_enabled": str(self.moderate_admins_enabled),
            
            # Pre-processing filters
            "delete_service_messages": str(self.delete_service_messages),
            "service_message_types": json.dumps(self.service_message_types),
            "stoplist_enabled": str(self.stoplist_enabled),
            "stoplist_words": json.dumps(self.stoplist_words),
            "stoplist_case_sensitive": str(self.stoplist_case_sensitive),
            "stoplist_auto_delete": str(self.stoplist_auto_delete),
            "delete_links": str(self.delete_links),
            "delete_images": str(self.delete_images),
            "delete_videos": str(self.delete_videos),
            "delete_stickers": str(self.delete_stickers),
            "delete_forwarded": str(self.delete_forwarded),
            "pattern_filters": json.dumps(self.pattern_filters),
            
            # Background moderation
            "moderation_enabled": str(self.moderation_enabled),
            "moderation_prompt": self.moderation_prompt or "",
            "auto_delete_threshold": str(self.auto_delete_threshold),
            "auto_warn_threshold": str(self.auto_warn_threshold),
            "quality_threshold": str(self.quality_threshold),
            
            # Reputation system
            "reputation_enabled": str(self.reputation_enabled),
            "points_per_helpful_message": str(self.points_per_helpful_message),
            "points_per_quality_reply": str(self.points_per_quality_reply),
            "points_per_achievement": str(self.points_per_achievement),
            "violation_penalty": str(self.violation_penalty),
            "spam_penalty": str(self.spam_penalty),
            "toxic_penalty": str(self.toxic_penalty),
            "auto_ban_enabled": str(self.auto_ban_enabled),
            "violations_before_ban": str(self.violations_before_ban),
            "ban_duration_hours": str(self.ban_duration_hours),
            "achievements_enabled": str(self.achievements_enabled),
            "achievement_rules": json.dumps(self.achievement_rules),
            
            # Notifications
            "notify_violations": str(self.notify_violations),
            "notify_achievements": str(self.notify_achievements),
            "notify_bans": str(self.notify_bans),
            "public_warnings": str(self.public_warnings),
            "public_achievements": str(self.public_achievements),
            
            # Metadata
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": str(self.created_by),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GroupSettings":
        """Create from dictionary (Redis data)."""
        
        def parse_bool(value: str) -> bool:
            """Parse boolean from string."""
            return value.lower() == "true" if isinstance(value, str) else bool(value)
        
        def parse_json_list(value: str) -> list:
            """Parse JSON list from string."""
            try:
                return json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                return []
        
        # Parse topic_id (can be empty string or None)
        topic_id_raw = data.get("topic_id", "")
        topic_id = int(topic_id_raw) if topic_id_raw and topic_id_raw != "" else None
        
        return cls(
            group_id=int(data["group_id"]),
            topic_id=topic_id,
            
            # Identity flags
            is_user_default=parse_bool(data.get("is_user_default", "False")),
            
            # Bot behavior settings
            # Note: silent_addition was removed - it's now handled only via silent_mode
            silent_mode=parse_bool(data.get("silent_mode", "False")),
            ai_assistant_enabled=parse_bool(data.get("ai_assistant_enabled", "True")),
            kb_indexation_enabled=parse_bool(data.get("kb_indexation_enabled", "True")),
            language=data.get("language", "en"),
            
            # Group profile
            custom_description=data.get("custom_description") or None,
            custom_avatar_file_id=data.get("custom_avatar_file_id") or None,
            generated_tagline=data.get("generated_tagline") or None,
            generated_tagline_updated=datetime.fromisoformat(data["generated_tagline_updated"]) if data.get("generated_tagline_updated") else None,
            
            # Moderation settings
            moderate_admins_enabled=parse_bool(data.get("moderate_admins_enabled", "False")),
            
            # Pre-processing filters
            delete_service_messages=parse_bool(data.get("delete_service_messages", "False")),
            service_message_types=parse_json_list(data.get("service_message_types", "[]")),
            stoplist_enabled=parse_bool(data.get("stoplist_enabled", "False")),
            stoplist_words=parse_json_list(data.get("stoplist_words", "[]")),
            stoplist_case_sensitive=parse_bool(data.get("stoplist_case_sensitive", "False")),
            stoplist_auto_delete=parse_bool(data.get("stoplist_auto_delete", "True")),
            delete_links=parse_bool(data.get("delete_links", "False")),
            delete_images=parse_bool(data.get("delete_images", "False")),
            delete_videos=parse_bool(data.get("delete_videos", "False")),
            delete_stickers=parse_bool(data.get("delete_stickers", "False")),
            delete_forwarded=parse_bool(data.get("delete_forwarded", "False")),
            pattern_filters=parse_json_list(data.get("pattern_filters", "[]")),
            
            # Background moderation
            moderation_enabled=parse_bool(data.get("moderation_enabled", "True")),
            moderation_prompt=data.get("moderation_prompt") or None,
            auto_delete_threshold=float(data.get("auto_delete_threshold", "8.0")),
            auto_warn_threshold=float(data.get("auto_warn_threshold", "5.0")),
            quality_threshold=float(data.get("quality_threshold", "7.0")),
            
            # Reputation system
            reputation_enabled=parse_bool(data.get("reputation_enabled", "True")),
            points_per_helpful_message=int(data.get("points_per_helpful_message", "5")),
            points_per_quality_reply=int(data.get("points_per_quality_reply", "10")),
            points_per_achievement=int(data.get("points_per_achievement", "50")),
            violation_penalty=int(data.get("violation_penalty", "-10")),
            spam_penalty=int(data.get("spam_penalty", "-25")),
            toxic_penalty=int(data.get("toxic_penalty", "-50")),
            auto_ban_enabled=parse_bool(data.get("auto_ban_enabled", "False")),
            violations_before_ban=int(data.get("violations_before_ban", "3")),
            ban_duration_hours=int(data.get("ban_duration_hours", "24")),
            achievements_enabled=parse_bool(data.get("achievements_enabled", "True")),
            achievement_rules=parse_json_list(data.get("achievement_rules", "[]")),
            
            # Notifications
            notify_violations=parse_bool(data.get("notify_violations", "True")),
            notify_achievements=parse_bool(data.get("notify_achievements", "True")),
            notify_bans=parse_bool(data.get("notify_bans", "True")),
            public_warnings=parse_bool(data.get("public_warnings", "False")),
            public_achievements=parse_bool(data.get("public_achievements", "True")),
            
            # Metadata
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            created_by=int(data.get("created_by", "0")),
        )
    
    def get_redis_key(self) -> str:
        """Get Redis key for this settings object."""
        if self.is_user_default:
            # User default template
            return f"user_default_group_settings:{self.group_id}"
        elif self.topic_id:
            # Topic settings
            return f"group_settings:{self.group_id}:topic_{self.topic_id}"
        else:
            # Group settings
            return f"group_settings:{self.group_id}"
    
    @staticmethod
    def get_group_settings_key(group_id: int, topic_id: Optional[int] = None) -> str:
        """Get Redis key for group/topic settings."""
        if topic_id:
            return f"group_settings:{group_id}:topic_{topic_id}"
        return f"group_settings:{group_id}"
    
    @staticmethod
    def get_user_default_key(user_id: int) -> str:
        """Get Redis key for user's default template settings."""
        return f"user_default_group_settings:{user_id}"

