"""
User Reputation Model - Per-user reputation tracking in groups.

Tracks:
- Points and violations
- Achievements
- Ban status
- Activity metrics
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class UserReputation:
    """
    Per-user reputation tracking in a specific group.
    
    Tracks behavior, contributions, violations, and achievements.
    """
    
    # ============================================================================
    # Identity
    # ============================================================================
    
    user_id: int  # Telegram user ID
    group_id: int  # Telegram group ID
    
    # ============================================================================
    # REPUTATION SCORE
    # ============================================================================
    
    points: int = 0  # Total reputation points (can be negative)
    
    # Activity counters
    message_count: int = 0  # Total messages sent
    helpful_messages: int = 0  # Messages rated helpful by LLM
    quality_replies: int = 0  # High-quality replies (>= quality_threshold)
    
    # ============================================================================
    # VIOLATIONS
    # ============================================================================
    
    warnings: int = 0  # Yellow cards (minor violations)
    violations: int = 0  # Red cards (serious violations)
    
    # Violation history (for transparency)
    violation_history: list[dict] = field(default_factory=list)
    # Format: [{"date": "2025-10-11T10:30:00", "type": "spam", "reason": "...", "penalty": -10}]
    
    # Last violation timestamp (for rate limiting)
    last_violation_at: Optional[datetime] = None
    
    # ============================================================================
    # BAN STATUS
    # ============================================================================
    
    is_banned: bool = False
    ban_reason: Optional[str] = None
    ban_until: Optional[datetime] = None  # None = permanent
    banned_at: Optional[datetime] = None
    banned_by: Optional[int] = None  # Admin user_id who banned
    
    # ============================================================================
    # ACHIEVEMENTS
    # ============================================================================
    
    achievements: list[str] = field(default_factory=list)
    # Format: List of achievement IDs, e.g., ["helper_10", "quality_contributor_50"]
    
    achievement_history: list[dict] = field(default_factory=list)
    # Format: [{"id": "helper_10", "name": "Helper", "awarded_at": "2025-10-11T10:30:00", "points": 50}]
    
    # ============================================================================
    # ACTIVITY TRACKING
    # ============================================================================
    
    first_message_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    
    # Engagement metrics
    replies_count: int = 0  # Messages that are replies
    mentions_count: int = 0  # Times mentioned bot
    
    # ============================================================================
    # METADATA
    # ============================================================================
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "user_id": str(self.user_id),
            "group_id": str(self.group_id),
            
            # Reputation
            "points": str(self.points),
            "message_count": str(self.message_count),
            "helpful_messages": str(self.helpful_messages),
            "quality_replies": str(self.quality_replies),
            
            # Violations
            "warnings": str(self.warnings),
            "violations": str(self.violations),
            "violation_history": json.dumps(self.violation_history),
            "last_violation_at": self.last_violation_at.isoformat() if self.last_violation_at else "",
            
            # Ban status
            "is_banned": str(self.is_banned),
            "ban_reason": self.ban_reason or "",
            "ban_until": self.ban_until.isoformat() if self.ban_until else "",
            "banned_at": self.banned_at.isoformat() if self.banned_at else "",
            "banned_by": str(self.banned_by) if self.banned_by else "",
            
            # Achievements
            "achievements": json.dumps(self.achievements),
            "achievement_history": json.dumps(self.achievement_history),
            
            # Activity
            "first_message_at": self.first_message_at.isoformat() if self.first_message_at else "",
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else "",
            "replies_count": str(self.replies_count),
            "mentions_count": str(self.mentions_count),
            
            # Metadata
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserReputation":
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
        
        def parse_datetime(value: str) -> Optional[datetime]:
            """Parse datetime from string."""
            try:
                return datetime.fromisoformat(value) if value else None
            except (ValueError, TypeError):
                return None
        
        def parse_int_optional(value: str) -> Optional[int]:
            """Parse optional int from string."""
            try:
                return int(value) if value else None
            except (ValueError, TypeError):
                return None
        
        return cls(
            user_id=int(data["user_id"]),
            group_id=int(data["group_id"]),
            
            # Reputation
            points=int(data.get("points", "0")),
            message_count=int(data.get("message_count", "0")),
            helpful_messages=int(data.get("helpful_messages", "0")),
            quality_replies=int(data.get("quality_replies", "0")),
            
            # Violations
            warnings=int(data.get("warnings", "0")),
            violations=int(data.get("violations", "0")),
            violation_history=parse_json_list(data.get("violation_history", "[]")),
            last_violation_at=parse_datetime(data.get("last_violation_at", "")),
            
            # Ban status
            is_banned=parse_bool(data.get("is_banned", "False")),
            ban_reason=data.get("ban_reason") or None,
            ban_until=parse_datetime(data.get("ban_until", "")),
            banned_at=parse_datetime(data.get("banned_at", "")),
            banned_by=parse_int_optional(data.get("banned_by", "")),
            
            # Achievements
            achievements=parse_json_list(data.get("achievements", "[]")),
            achievement_history=parse_json_list(data.get("achievement_history", "[]")),
            
            # Activity
            first_message_at=parse_datetime(data.get("first_message_at", "")),
            last_message_at=parse_datetime(data.get("last_message_at", "")),
            replies_count=int(data.get("replies_count", "0")),
            mentions_count=int(data.get("mentions_count", "0")),
            
            # Metadata
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
        )
    
    def get_redis_key(self) -> str:
        """Get Redis key for this reputation object."""
        return f"user_reputation:{self.user_id}:{self.group_id}"
    
    @staticmethod
    def get_user_reputation_key(user_id: int, group_id: int) -> str:
        """Get Redis key for user reputation."""
        return f"user_reputation:{user_id}:{group_id}"
    
    @staticmethod
    def get_group_leaderboard_key(group_id: int) -> str:
        """Get Redis sorted set key for group leaderboard."""
        return f"group_leaderboard:{group_id}"
    
    @staticmethod
    def get_group_users_reputation_key(group_id: int) -> str:
        """Get Redis set key for all users with reputation in this group."""
        return f"group_users_reputation:{group_id}"
    
    def update_activity(self, is_reply: bool = False, is_mention: bool = False):
        """Update activity counters."""
        self.message_count += 1
        self.last_message_at = datetime.utcnow()
        
        if not self.first_message_at:
            self.first_message_at = datetime.utcnow()
        
        if is_reply:
            self.replies_count += 1
        
        if is_mention:
            self.mentions_count += 1
        
        self.updated_at = datetime.utcnow()
    
    def add_violation(self, violation_type: str, reason: str, penalty: int):
        """Record a violation."""
        self.violations += 1
        self.points += penalty  # Penalty is negative
        self.last_violation_at = datetime.utcnow()
        
        # Add to history
        self.violation_history.append({
            "date": datetime.utcnow().isoformat(),
            "type": violation_type,
            "reason": reason,
            "penalty": penalty
        })
        
        self.updated_at = datetime.utcnow()
    
    def add_warning(self):
        """Add a warning (yellow card)."""
        self.warnings += 1
        self.updated_at = datetime.utcnow()
    
    def add_achievement(self, achievement_id: str, achievement_name: str, points: int):
        """Award an achievement."""
        if achievement_id not in self.achievements:
            self.achievements.append(achievement_id)
            self.points += points
            
            self.achievement_history.append({
                "id": achievement_id,
                "name": achievement_name,
                "awarded_at": datetime.utcnow().isoformat(),
                "points": points
            })
            
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def ban(self, reason: str, duration_hours: int = 0, banned_by: Optional[int] = None):
        """Ban user."""
        self.is_banned = True
        self.ban_reason = reason
        self.banned_at = datetime.utcnow()
        self.banned_by = banned_by
        
        if duration_hours > 0:
            from datetime import timedelta
            self.ban_until = datetime.utcnow() + timedelta(hours=duration_hours)
        else:
            self.ban_until = None  # Permanent
        
        self.updated_at = datetime.utcnow()
    
    def unban(self):
        """Unban user."""
        self.is_banned = False
        self.ban_reason = None
        self.ban_until = None
        self.updated_at = datetime.utcnow()
    
    def is_ban_expired(self) -> bool:
        """Check if temporary ban has expired."""
        if not self.is_banned:
            return True
        
        if self.ban_until and datetime.utcnow() > self.ban_until:
            return True
        
        return False

