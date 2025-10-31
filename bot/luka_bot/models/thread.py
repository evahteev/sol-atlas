"""
Thread model - Unified model for DM, Group, and Topic conversations.

Thread management with Redis persistence and settings support.
Supports DM threads, group threads, and topic threads with full configuration.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Thread:
    """
    Universal conversation thread model.
    
    Supports three types of conversations:
    - DM threads: thread_id = "user_{user_id}"
    - Group threads: thread_id = "group_{group_id}"
    - Topic threads: thread_id = "group_{group_id}_topic_{topic_id}"
    
    All conversation configuration (LLM settings, tools, KB) stored here.
    """
    thread_id: str
    owner_id: int  # User who owns/created (user_id for DM, first admin for groups)
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    is_active: bool = True
    
    # Thread type identification
    thread_type: str = "dm"  # "dm", "group", "topic"
    
    # Group/topic references (only for thread_type="group"/"topic")
    group_id: Optional[int] = None  # Telegram group ID
    topic_id: Optional[int] = None  # Telegram message_thread_id for topics
    
    # Language setting (affects LLM responses, UI messages)
    language: str = "en"  # "en", "ru", etc.
    
    # Agent customization
    agent_name: Optional[str] = None  # Custom agent name (e.g., "CryptoGuru")
    agent_description: Optional[str] = None  # Optional agent description
    
    # LLM Settings (per-thread overrides)
    llm_provider: Optional[str] = None  # "ollama", "openai", etc.
    model_name: Optional[str] = None  # Model name within provider
    system_prompt: Optional[str] = None  # Per-thread personality override
    
    # Tool configuration
    enabled_tools: list[str] = field(default_factory=list)  # Whitelist of tools (empty = all enabled)
    disabled_tools: list[str] = field(default_factory=list)  # Blacklist of tools
    
    # Knowledge Base configuration
    knowledge_bases: list[str] = field(default_factory=list)  # KB indices to search
    
    # Camunda workflow integration
    process_instance_id: Optional[str] = None  # Thread IS a workflow
    active_workflows: list[str] = field(default_factory=list)  # Thread LAUNCHES workflows
    
    # Conversation summary for context-aware responses
    conversation_summary: Optional[str] = None  # Compact summary of conversation (~200-500 tokens)
    summary_updated_at: Optional[datetime] = None  # When summary was last generated
    summary_message_count: int = 0  # Messages processed in current summary
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Redis storage."""
        import json
        return {
            "thread_id": self.thread_id,
            "owner_id": str(self.owner_id),
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": str(self.message_count),
            "is_active": "true" if self.is_active else "false",
            # Thread type
            "thread_type": self.thread_type,
            # Group/topic references
            "group_id": str(self.group_id) if self.group_id is not None else "",
            "topic_id": str(self.topic_id) if self.topic_id is not None else "",
            # Language
            "language": self.language,
            # Agent customization
            "agent_name": self.agent_name or "",
            "agent_description": self.agent_description or "",
            # LLM Settings
            "llm_provider": self.llm_provider or "",
            "model_name": self.model_name or "",
            "system_prompt": self.system_prompt or "",
            # Tool configuration
            "enabled_tools": json.dumps(self.enabled_tools),
            "disabled_tools": json.dumps(self.disabled_tools),
            # Knowledge Bases
            "knowledge_bases": json.dumps(self.knowledge_bases),
            # Camunda
            "process_instance_id": self.process_instance_id or "",
            "active_workflows": json.dumps(self.active_workflows),
            # Conversation summary
            "conversation_summary": self.conversation_summary or "",
            "summary_updated_at": self.summary_updated_at.isoformat() if self.summary_updated_at else "",
            "summary_message_count": str(self.summary_message_count),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        """Create from dictionary (Redis data)."""
        import json
        
        # Parse JSON fields
        def parse_json_list(raw: str) -> list:
            try:
                return json.loads(raw) if raw else []
            except (json.JSONDecodeError, TypeError):
                return []
        
        active_workflows = parse_json_list(data.get("active_workflows", "[]"))
        knowledge_bases = parse_json_list(data.get("knowledge_bases", "[]"))
        enabled_tools = parse_json_list(data.get("enabled_tools", "[]"))
        disabled_tools = parse_json_list(data.get("disabled_tools", "[]"))
        
        # Parse group_id and topic_id (handle empty strings)
        group_id_raw = data.get("group_id", "")
        group_id = int(group_id_raw) if group_id_raw and group_id_raw != "" else None
        
        topic_id_raw = data.get("topic_id", "")
        topic_id = int(topic_id_raw) if topic_id_raw and topic_id_raw != "" else None
        
        # Support legacy user_id field (for backward compatibility during transition)
        owner_id_raw = data.get("owner_id") or data.get("user_id")
        
        return cls(
            thread_id=data["thread_id"],
            owner_id=int(owner_id_raw),
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=int(data.get("message_count", 0)),
            is_active=data.get("is_active", "true").lower() == "true",
            # Thread type
            thread_type=data.get("thread_type", "dm"),
            # Group/topic references
            group_id=group_id,
            topic_id=topic_id,
            # Language
            language=data.get("language", "en"),
            # Agent customization
            agent_name=data.get("agent_name") or None,
            agent_description=data.get("agent_description") or None,
            # LLM Settings
            llm_provider=data.get("llm_provider") or None,
            model_name=data.get("model_name") or None,
            system_prompt=data.get("system_prompt") or None,
            # Tool configuration
            enabled_tools=enabled_tools,
            disabled_tools=disabled_tools,
            # Knowledge Bases
            knowledge_bases=knowledge_bases,
            # Camunda
            process_instance_id=data.get("process_instance_id") or None,
            active_workflows=active_workflows,
            # Conversation summary
            conversation_summary=data.get("conversation_summary") or None,
            summary_updated_at=datetime.fromisoformat(data["summary_updated_at"]) if data.get("summary_updated_at") else None,
            summary_message_count=int(data.get("summary_message_count", 0)),
        )
    
    def update_activity(self) -> None:
        """Update last activity timestamp and increment message count."""
        self.updated_at = datetime.utcnow()
        self.message_count += 1

