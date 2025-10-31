"""
Form models for unified start form and task rendering.

Provides common data structures for both Camunda start forms and tasks.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class FormType(str, Enum):
    """Type of form being rendered"""
    START_FORM = "start_form"
    TASK = "task"


@dataclass
class FormData:
    """
    Unified data structure for start forms and tasks.
    
    This model contains all information needed to render and complete
    a form, whether it's a Camunda process start form or a task form.
    """
    # Identity
    id: str  # process_key for start forms, task_id for tasks
    name: str  # Process name or task name
    description: str  # Process/task description
    
    # Type
    form_type: FormType
    
    # Context (form-type specific)
    process_key: Optional[str] = None  # For start forms
    task_id: Optional[str] = None  # For tasks
    business_key: Optional[str] = None  # For start forms
    process_instance_id: Optional[str] = None  # For tasks
    process_definition_name: Optional[str] = None  # Process definition name (for tasks)
    
    # Variables (categorized)
    text_vars: List[Dict[str, Any]] = field(default_factory=list)  # Read-only display
    form_vars: List[Dict[str, Any]] = field(default_factory=list)  # Text inputs
    s3_vars: List[Dict[str, Any]] = field(default_factory=list)  # File uploads
    action_vars: List[Dict[str, Any]] = field(default_factory=list)  # Action buttons (tasks only)
    
    # Metadata
    group_id: Optional[int] = None
    telegram_user_id: int = 0
    
    @property
    def editable_vars(self) -> List[Dict[str, Any]]:
        """Get all editable variables (form + s3)"""
        return self.form_vars + self.s3_vars
    
    @property
    def total_editable(self) -> int:
        """Total number of editable variables"""
        return len(self.editable_vars)
    
    @property
    def has_action_buttons(self) -> bool:
        """Check if form has action buttons (tasks only)"""
        return len(self.action_vars) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for FSM storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "form_type": self.form_type.value,
            "process_key": self.process_key,
            "task_id": self.task_id,
            "business_key": self.business_key,
            "process_instance_id": self.process_instance_id,
            "process_definition_name": self.process_definition_name,
            "text_vars": self.text_vars,
            "form_vars": self.form_vars,
            "s3_vars": self.s3_vars,
            "action_vars": self.action_vars,
            "group_id": self.group_id,
            "telegram_user_id": self.telegram_user_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormData':
        """Create from dict (from FSM storage)"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            form_type=FormType(data.get("form_type", "start_form")),
            process_key=data.get("process_key"),
            task_id=data.get("task_id"),
            business_key=data.get("business_key"),
            process_instance_id=data.get("process_instance_id"),
            process_definition_name=data.get("process_definition_name"),
            text_vars=data.get("text_vars", []),
            form_vars=data.get("form_vars", []),
            s3_vars=data.get("s3_vars", []),
            action_vars=data.get("action_vars", []),
            group_id=data.get("group_id"),
            telegram_user_id=data.get("telegram_user_id", 0)
        )


@dataclass
class FormContext:
    """
    Context stored in FSM state during form flow.
    
    Tracks the current state of form completion including:
    - Which form is being processed
    - Which variable we're currently collecting
    - What values have been collected so far
    - Message IDs for cleanup
    """
    # Form being processed
    form_data: FormData
    
    # Message tracking
    intro_message_id: int
    intro_message_text: str = ""  # Store original text for editing later
    dialog_message_ids: List[int] = field(default_factory=list)
    confirmation_message_id: Optional[int] = None
    
    # Collection state
    current_index: int = 0  # Index in editable_vars
    collected_values: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for FSM storage"""
        return {
            "form_data": self.form_data.to_dict(),
            "intro_message_id": self.intro_message_id,
            "intro_message_text": self.intro_message_text,
            "dialog_message_ids": self.dialog_message_ids,
            "confirmation_message_id": self.confirmation_message_id,
            "current_index": self.current_index,
            "collected_values": self.collected_values
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FormContext':
        """Create from dict (from FSM storage)"""
        return cls(
            form_data=FormData.from_dict(data.get("form_data", {})),
            intro_message_id=data.get("intro_message_id", 0),
            intro_message_text=data.get("intro_message_text", ""),
            dialog_message_ids=data.get("dialog_message_ids", []),
            confirmation_message_id=data.get("confirmation_message_id"),
            current_index=data.get("current_index", 0),
            collected_values=data.get("collected_values", {})
        )

