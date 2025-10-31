"""
Group link model for Luka bot.

Simplified many-to-many mapping between users and groups.
All group configuration (KB, language, settings) is stored in the Thread model.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GroupLink:
    """
    Lightweight link between a user and a Telegram group.
    
    This is a simple many-to-many relationship tracker:
    - Which groups a user has access to
    - The thread_id for the group's conversation
    - The user's role/permissions in the group
    
    All group configuration (KB, language, agent settings) is stored in the Thread.
    """
    
    # Primary identifiers
    user_id: int
    group_id: int
    
    # Reference to group thread (where all config lives)
    thread_id: str  # e.g., "group_{group_id}"
    
    # User role in group (for permission checks)
    user_role: str = "member"  # member, admin, owner
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Status
    is_active: bool = True  # False if bot was removed from group or user left
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "user_id": str(self.user_id),
            "group_id": str(self.group_id),
            "thread_id": self.thread_id,
            "user_role": self.user_role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": str(self.is_active),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GroupLink":
        """Create from dictionary (Redis data)."""
        return cls(
            user_id=int(data["user_id"]),
            group_id=int(data["group_id"]),
            thread_id=data["thread_id"],
            user_role=data.get("user_role", "member"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data.get("updated_at", data["created_at"])),
            is_active=data.get("is_active", "True") == "True",
        )
    
    def get_redis_key(self) -> str:
        """Get Redis key for this group link."""
        return f"group_link:{self.user_id}:{self.group_id}"
    
    @staticmethod
    def get_user_groups_key(user_id: int) -> str:
        """Get Redis set key for all groups linked to a user."""
        return f"user_groups:{user_id}"
    
    @staticmethod
    def get_group_users_key(group_id: int) -> str:
        """Get Redis set key for all users who linked this group."""
        return f"group_users:{group_id}"
