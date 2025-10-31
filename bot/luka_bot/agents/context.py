"""
Conversation context for Luka Bot agents - Phase 4.

Adapted from bot_server/agents/context.py with Luka-specific enhancements.

Key differences from bot_server:
- Removed Camunda-specific fields (camunda_user_id, camunda_key, webapp_user_id)
- Added thread-specific fields (thread_id, enabled_tools, llm_provider)
- Simplified for standalone operation
- Added per-thread configuration support

Context is passed to all agent tools and provides:
- User identification
- Thread settings (KB groups, enabled tools, LLM config)
- Metadata for special message types (voice, etc.)
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ConversationContext(BaseModel):
    """
    Context for pydantic-ai agent tools in Luka Bot.
    
    This context is passed to every tool execution, providing:
    - User and thread identification
    - Thread-specific knowledge bases
    - Enabled tools list
    - LLM provider and model configuration
    - Message metadata (voice, attachments, etc.)
    """
    
    # Core identifiers
    user_id: int = Field(..., description="Telegram user ID")
    thread_id: Optional[str] = Field(None, description="Conversation thread ID")
    
    # Thread-specific knowledge base configuration
    thread_knowledge_bases: List[str] = Field(
        default_factory=list,
        description="KB group_ids associated with this thread (for RAG tools)"
    )
    
    # KB scope preferences
    kb_scope: Optional[Dict[str, Any]] = Field(
        None,
        description="User's KB scope preferences (source, group_ids, etc.)"
    )
    
    # Thread-specific tool configuration
    enabled_tools: List[str] = Field(
        default_factory=list,
        description="List of tool names enabled for this thread"
    )
    
    # LLM configuration (per-thread overrides)
    llm_provider: Optional[str] = Field(
        None,
        description="LLM provider for this thread (ollama, openai, etc.)"
    )
    model_name: Optional[str] = Field(
        None,
        description="Model name for this thread (gpt-oss, gpt-4, etc.)"
    )
    system_prompt_override: Optional[str] = Field(
        None,
        description="Thread-specific system prompt override"
    )
    
    # Conversation summary for context-aware responses
    conversation_summary: Optional[str] = Field(
        None,
        description="Compact summary of conversation history for context-aware responses"
    )
    
    # Message metadata (voice, attachments, etc.)
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Message metadata (voice duration, language, confidence, etc.)"
    )
    
    # Future: Camunda integration (Phase 5)
    process_instance_id: Optional[str] = Field(
        None,
        description="Active Camunda process instance ID (Phase 5+)"
    )
    process_definition_key: Optional[str] = Field(
        None,
        description="Camunda process definition key (Phase 5+)"
    )
    source_thread_id: Optional[str] = Field(
        None,
        description="Source thread for workflow results (Phase 5+)"
    )
    
    # Camunda user identification (Phase 5)
    camunda_user_id: Optional[str] = Field(
        None,
        description="Camunda assignee ID for task operations (Phase 5+)"
    )
    camunda_key: Optional[str] = Field(
        None,
        description="Camunda user identification key (Phase 5+)"
    )
    
    @classmethod
    def from_thread(
        cls,
        user_id: int,
        thread_id: str,
        thread_knowledge_bases: Optional[List[str]] = None,
        enabled_tools: Optional[List[str]] = None,
        llm_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
        conversation_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConversationContext":
        """
        Create context from thread information.
        
        This is the primary way to create context in Luka Bot.
        
        Args:
            user_id: Telegram user ID
            thread_id: Thread ID from Thread model
            thread_knowledge_bases: KB groups for this thread
            enabled_tools: Tools enabled for this thread
            llm_provider: Provider override (ollama, openai)
            model_name: Model override (gpt-oss, gpt-4)
            system_prompt_override: Custom system prompt
            metadata: Message metadata
        
        Returns:
            ConversationContext instance
        
        Example:
            >>> from luka_bot.models.thread import Thread
            >>> thread = await thread_service.get_thread(thread_id)
            >>> ctx = ConversationContext.from_thread(
            ...     user_id=user.user_id,
            ...     thread_id=thread.thread_id,
            ...     thread_knowledge_bases=thread.thread_knowledge_bases,
            ...     enabled_tools=thread.enabled_tools
            ... )
        """
        return cls(
            user_id=user_id,
            thread_id=thread_id,
            thread_knowledge_bases=thread_knowledge_bases or [],
            enabled_tools=enabled_tools or [],
            llm_provider=llm_provider,
            model_name=model_name,
            system_prompt_override=system_prompt_override,
            conversation_summary=conversation_summary,
            metadata=metadata or {}
        )
    
    @classmethod
    def from_user(
        cls,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConversationContext":
        """
        Create minimal context with just user ID.
        
        Use this for operations outside of a thread context.
        
        Args:
            user_id: Telegram user ID
            metadata: Optional message metadata
        
        Returns:
            ConversationContext instance
        """
        return cls(
            user_id=user_id,
            thread_knowledge_bases=[],
            enabled_tools=[],
            metadata=metadata or {}
        )
    
    def has_tool_enabled(self, tool_name: str) -> bool:
        """
        Check if a specific tool is enabled for this context.
        
        Args:
            tool_name: Name of the tool to check
        
        Returns:
            True if tool is enabled or no tools restriction, False otherwise
        """
        # If no tools specified, allow all
        if not self.enabled_tools:
            return True
        return tool_name in self.enabled_tools
    
    def get_kb_groups(self) -> List[str]:
        """
        Get knowledge base groups for this context.
        
        Returns:
            List of KB group IDs, empty list if none configured
        """
        return self.thread_knowledge_bases or []


class TaskContext(BaseModel):
    """
    Context for task-specific operations (Phase 5: Camunda integration).
    
    Used for Camunda task execution and workflow management.
    """
    task_id: str = Field(..., description="Camunda task ID")
    task_name: str = Field(..., description="Human-readable task name")
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task variables"
    )
    dialog_state: Optional[Dict[str, Any]] = Field(
        None,
        description="Dialog state for conversational tasks"
    )


__all__ = [
    'ConversationContext',
    'TaskContext',
]

