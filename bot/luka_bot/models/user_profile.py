"""
UserProfile model - Phase 4.

Stores user preferences and onboarding state.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserProfile:
    """
    User profile model.
    
    Phase 4: Basic profile with language and onboarding state.
    Future phases: bot preferences, balances, etc.
    """
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: str = "en"  # "en" or "ru"
    is_blocked: bool = False  # False = needs onboarding, True = onboarding complete
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Phase 5: Knowledge Base
    kb_index: Optional[str] = None  # Elasticsearch KB index name (e.g., "tg-kb-user-922705")
    
    # Phase 5+: Additional preferences (placeholders)
    default_model: Optional[str] = None
    default_provider: Optional[str] = None
    system_prompt_override: Optional[str] = None
    
    # Camunda credentials (fetched from flow API on login)
    camunda_user_id: Optional[str] = None
    camunda_key: Optional[str] = None  # Camunda password/API key
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        return {
            "user_id": str(self.user_id),
            "username": self.username or "",
            "first_name": self.first_name or "",
            "last_name": self.last_name or "",
            "language": self.language,
            "is_blocked": "true" if self.is_blocked else "false",
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "kb_index": self.kb_index or "",
            "default_model": self.default_model or "",
            "default_provider": self.default_provider or "",
            "system_prompt_override": self.system_prompt_override or "",
            "camunda_user_id": self.camunda_user_id or "",
            "camunda_key": self.camunda_key or "",
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create from dictionary (Redis data)."""
        return cls(
            user_id=int(data["user_id"]),
            username=data.get("username") or None,
            first_name=data.get("first_name") or None,
            last_name=data.get("last_name") or None,
            language=data.get("language", "en"),
            is_blocked=data.get("is_blocked", "false").lower() == "true",
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            kb_index=data.get("kb_index") or None,
            default_model=data.get("default_model") or None,
            default_provider=data.get("default_provider") or None,
            system_prompt_override=data.get("system_prompt_override") or None,
            camunda_user_id=data.get("camunda_user_id") or None,
            camunda_key=data.get("camunda_key") or None,
        )
    
    def needs_onboarding(self) -> bool:
        """Check if user needs onboarding."""
        return not self.is_blocked
    
    def mark_onboarding_complete(self) -> None:
        """Mark onboarding as complete."""
        self.is_blocked = True
        self.updated_at = datetime.utcnow()
    
    def get_display_name(self) -> str:
        """Get user's display name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.user_id}"

