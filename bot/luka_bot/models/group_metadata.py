"""
Group Metadata Model for Luka Bot.

Stores rich information about Telegram groups collected via Bot API.
Used to display comprehensive group information and track bot capabilities.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class GroupMetadata:
    """
    Rich metadata about a Telegram group.
    
    Collected at bot addition and cached for fast access.
    Includes admin list, member count, bot permissions, and group details.
    """
    
    # ============================================================================
    # IDENTITY
    # ============================================================================
    group_id: int
    group_title: str = ""
    group_username: Optional[str] = None  # @groupname if public
    group_type: str = "group"  # "group" or "supergroup"
    
    # ============================================================================
    # TELEGRAM CHAT INFO (from bot.get_chat)
    # ============================================================================
    description: Optional[str] = None
    invite_link: Optional[str] = None  # If bot has can_invite_users permission
    photo_small_file_id: Optional[str] = None
    photo_big_file_id: Optional[str] = None
    
    permissions: dict = field(default_factory=dict)  # ChatPermissions object
    # Examples: can_send_messages, can_send_media_messages, can_send_polls, etc.
    
    pinned_message_id: Optional[int] = None
    pinned_message_text: Optional[str] = None
    
    slow_mode_delay: int = 0  # Seconds between messages (0 = disabled)
    
    # ============================================================================
    # MEMBER STATISTICS (from bot.get_chat_member_count)
    # ============================================================================
    total_member_count: int = 0
    last_member_count_update: datetime = field(default_factory=datetime.utcnow)
    
    # ============================================================================
    # ADMINISTRATORS (from bot.get_chat_administrators)
    # ============================================================================
    admin_list: list = field(default_factory=list)
    # Format: [{"user_id": 123, "username": "@user", "full_name": "John Doe", 
    #           "status": "creator"|"administrator", "custom_title": "...", 
    #           "is_bot": false, "permissions": {...}}]
    
    admin_count: int = 0
    bot_admin_permissions: dict = field(default_factory=dict)  # Bot's own permissions
    
    # ============================================================================
    # BOT SETUP INFO
    # ============================================================================
    added_at: datetime = field(default_factory=datetime.utcnow)
    added_by_user_id: int = 0
    added_by_username: Optional[str] = None
    added_by_full_name: str = "Unknown"
    
    # Bot configuration at time of addition
    bot_username: str = ""
    bot_name: str = ""
    kb_index: str = ""
    thread_id: str = ""
    initial_language: str = "en"
    
    # ============================================================================
    # TRACKING & UPDATES
    # ============================================================================
    last_metadata_update: datetime = field(default_factory=datetime.utcnow)
    metadata_update_count: int = 0
    
    # Status
    is_active: bool = True
    bot_is_admin: bool = False
    
    # ============================================================================
    # DERIVED INSIGHTS (updated over time)
    # ============================================================================
    first_message_timestamp: Optional[datetime] = None
    total_messages_received: int = 0  # From bot join onwards
    active_members_list: list = field(default_factory=list)  # User IDs who've sent messages
    
    # Topics/threads info (for supergroups with topics enabled)
    has_topics: bool = False
    topic_ids: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "group_id": str(self.group_id),
            "group_title": self.group_title,
            "group_username": self.group_username or "",
            "group_type": self.group_type,
            "description": self.description or "",
            "invite_link": self.invite_link or "",
            "photo_small_file_id": self.photo_small_file_id or "",
            "photo_big_file_id": self.photo_big_file_id or "",
            "permissions": json.dumps(self.permissions),
            "pinned_message_id": str(self.pinned_message_id) if self.pinned_message_id else "",
            "pinned_message_text": self.pinned_message_text or "",
            "slow_mode_delay": str(self.slow_mode_delay),
            "total_member_count": str(self.total_member_count),
            "last_member_count_update": self.last_member_count_update.isoformat(),
            "admin_list": json.dumps(self.admin_list),
            "admin_count": str(self.admin_count),
            "bot_admin_permissions": json.dumps(self.bot_admin_permissions),
            "added_at": self.added_at.isoformat(),
            "added_by_user_id": str(self.added_by_user_id),
            "added_by_username": self.added_by_username or "",
            "added_by_full_name": self.added_by_full_name,
            "bot_username": self.bot_username,
            "bot_name": self.bot_name,
            "kb_index": self.kb_index,
            "thread_id": self.thread_id,
            "initial_language": self.initial_language,
            "last_metadata_update": self.last_metadata_update.isoformat(),
            "metadata_update_count": str(self.metadata_update_count),
            "is_active": str(self.is_active),
            "bot_is_admin": str(self.bot_is_admin),
            "first_message_timestamp": self.first_message_timestamp.isoformat() if self.first_message_timestamp else "",
            "total_messages_received": str(self.total_messages_received),
            "active_members_list": json.dumps(self.active_members_list),
            "has_topics": str(self.has_topics),
            "topic_ids": json.dumps(self.topic_ids),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GroupMetadata":
        """Create from dictionary (Redis data)."""
        
        def parse_bool(value: str) -> bool:
            """Parse boolean from string."""
            if isinstance(value, bool):
                return value
            return str(value).lower() == "true"
        
        def parse_json(value: str, default=None):
            """Parse JSON from string."""
            if not value:
                return default or ([] if isinstance(default, list) else {})
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return default or ([] if isinstance(default, list) else {})
        
        def parse_datetime(value: str) -> Optional[datetime]:
            """Parse datetime from ISO format string."""
            if not value:
                return None
            try:
                return datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                return None
        
        def parse_int(value: str, default: int = 0) -> int:
            """Parse integer from string, handling 'None' strings."""
            if not value or value == "None" or value == "null":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        # Parse optional int
        pinned_id = data.get("pinned_message_id", "")
        pinned_message_id = parse_int(pinned_id) if pinned_id and pinned_id != "" else None
        
        first_msg_ts = parse_datetime(data.get("first_message_timestamp", ""))
        
        return cls(
            group_id=parse_int(data["group_id"]),
            group_title=data.get("group_title", ""),
            group_username=data.get("group_username") or None,
            group_type=data.get("group_type", "group"),
            description=data.get("description") or None,
            invite_link=data.get("invite_link") or None,
            photo_small_file_id=data.get("photo_small_file_id") or None,
            photo_big_file_id=data.get("photo_big_file_id") or None,
            permissions=parse_json(data.get("permissions", "{}"), {}),
            pinned_message_id=pinned_message_id,
            pinned_message_text=data.get("pinned_message_text") or None,
            slow_mode_delay=parse_int(data.get("slow_mode_delay", "0")),
            total_member_count=parse_int(data.get("total_member_count", "0")),
            last_member_count_update=parse_datetime(data.get("last_member_count_update")) or datetime.utcnow(),
            admin_list=parse_json(data.get("admin_list", "[]"), []),
            admin_count=parse_int(data.get("admin_count", "0")),
            bot_admin_permissions=parse_json(data.get("bot_admin_permissions", "{}"), {}),
            added_at=parse_datetime(data.get("added_at")) or datetime.utcnow(),
            added_by_user_id=parse_int(data.get("added_by_user_id", "0")),
            added_by_username=data.get("added_by_username") or None,
            added_by_full_name=data.get("added_by_full_name", "Unknown"),
            bot_username=data.get("bot_username", ""),
            bot_name=data.get("bot_name", ""),
            kb_index=data.get("kb_index", ""),
            thread_id=data.get("thread_id", ""),
            initial_language=data.get("initial_language", "en"),
            last_metadata_update=parse_datetime(data.get("last_metadata_update")) or datetime.utcnow(),
            metadata_update_count=parse_int(data.get("metadata_update_count", "0")),
            is_active=parse_bool(data.get("is_active", "True")),
            bot_is_admin=parse_bool(data.get("bot_is_admin", "False")),
            first_message_timestamp=first_msg_ts,
            total_messages_received=parse_int(data.get("total_messages_received", "0")),
            active_members_list=parse_json(data.get("active_members_list", "[]"), []),
            has_topics=parse_bool(data.get("has_topics", "False")),
            topic_ids=parse_json(data.get("topic_ids", "[]"), []),
        )
    
    def get_redis_key(self) -> str:
        """Get Redis key for this metadata object."""
        return f"group_metadata:{self.group_id}"
    
    @staticmethod
    def get_metadata_key(group_id: int) -> str:
        """Get Redis key for group metadata."""
        return f"group_metadata:{group_id}"

