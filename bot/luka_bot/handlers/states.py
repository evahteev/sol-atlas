"""
FSM States for Luka Bot.

Defines all finite state machine states used throughout the bot for:
- Navigation mode tracking
- Thread management workflows
- User input collection
- Dialog workflows
"""
from aiogram.fsm.state import State, StatesGroup


class NavigationStates(StatesGroup):
    """
    Track which mode/menu the user is currently in.
    
    Each command switches to its corresponding mode and shows
    the appropriate reply keyboard.
    """
    start_mode = State()     # /start - Actions hub navigation
    chat_mode = State()      # /chat - Thread management (default)
    tasks_mode = State()     # /tasks - GTD task categories
    profile_mode = State()   # /profile - User settings
    groups_mode = State()    # /groups - Group management (Phase 6)
    stats_mode = State()     # /stats - Statistics and metrics (Phase 7)


class ThreadStates(StatesGroup):
    """
    States for thread management operations.
    
    Used for multi-step thread operations like renaming,
    creating custom threads, etc.
    """
    waiting_for_thread_name = State()    # User is typing a new thread name
    waiting_for_first_message = State()  # Lazy thread creation - waiting for first message
    editing_thread_prompt = State()      # User is editing thread system prompt (Phase 5)


class WorkflowStates(StatesGroup):
    """
    States for dialog workflow execution.
    
    Tracks user progress through conversational workflows.
    """
    executing_workflow = State()         # User is in the middle of a workflow
    waiting_for_workflow_input = State() # Waiting for user input for current workflow step


class ThreadSettingsStates(StatesGroup):
    """
    States for thread settings configuration (Phase 5).
    
    Used when user is configuring thread-specific LLM settings.
    """
    editing_system_prompt = State()      # User is typing custom system prompt
    selecting_provider = State()         # User is selecting LLM provider
    selecting_model = State()            # User is selecting LLM model


class ProcessStates(StatesGroup):
    """
    States for Camunda BPMN process execution.
    
    Tracks user progress through process-driven workflows.
    """
    idle = State()                       # No active process
    process_active = State()             # Process running
    task_waiting = State()               # Waiting for task completion
    dialog_active = State()              # Dialog form active
    waiting_for_input = State()          # Waiting for ForceReply response
    file_upload_pending = State()        # Waiting for file upload
    processing_file = State()            # File being processed (upload to R2)


# Export all state groups
__all__ = [
    'NavigationStates',
    'ThreadStates',
    'WorkflowStates',
    'ThreadSettingsStates',
    'ProcessStates',
]

