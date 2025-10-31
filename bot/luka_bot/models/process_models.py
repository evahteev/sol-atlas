"""
Data models for Camunda process and task management.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class ProcessContext:
    """Context for active process"""
    process_id: str
    process_key: str
    business_key: str
    user_id: int
    started_at: datetime
    current_task_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    tracked_messages: List[int] = field(default_factory=list)


@dataclass
class TaskContext:
    """Context for active task"""
    task_id: str
    task_name: str
    process_id: str
    user_id: int
    variables: List[Dict[str, Any]] = field(default_factory=list)
    action_variables: List[Dict[str, Any]] = field(default_factory=list)
    form_variables: List[Dict[str, Any]] = field(default_factory=list)
    s3_variables: List[Dict[str, Any]] = field(default_factory=list)  # NEW
    current_dialog_index: int = 0
    collected_values: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskVariables:
    """Categorized task variables"""
    text_vars: List[Dict[str, Any]] = field(default_factory=list)
    action_vars: List[Dict[str, Any]] = field(default_factory=list)
    form_vars: List[Dict[str, Any]] = field(default_factory=list)
    s3_vars: List[Dict[str, Any]] = field(default_factory=list)  # NEW

