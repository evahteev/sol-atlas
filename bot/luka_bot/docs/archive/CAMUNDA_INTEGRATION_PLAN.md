# Camunda BPMN Integration Implementation Plan for Luka Bot

**Version:** 1.0  
**Date:** October 14, 2025  
**Status:** Ready for Implementation

---

## 📋 Executive Summary

This document outlines the complete implementation plan for integrating Camunda BPMN workflows into `luka_bot`. The integration will enable process-driven features like history import through BPMN workflows, with tasks rendered as inline Telegram messages with action buttons.

### Key Features
- ✅ BPMN process execution from Telegram
- ✅ Multi-step dialog forms with ForceReply
- ✅ Action button-based task completion
- ✅ **S3 file upload variables with Cloudflare R2**
- ✅ Auto-cleanup of task messages
- ✅ Real-time task updates (future)

---

## 🎯 Task Variable Types

The system supports **FOUR** types of task variables:

### 1. **Text Variables** (Read-Only)
- **Pattern:** Any non-writable variable
- **Behavior:** Displayed in task description
- **Example:** `group_name`, `total_members`

### 2. **Action Variables** (Button Actions)
- **Pattern:** `action_*` (e.g., `action_approve`, `action_reject`)
- **Behavior:** Rendered as inline buttons; clicking completes task immediately
- **Example:** `action_approve`, `action_back`, `action_cancel`

### 3. **Form Variables** (Dialog Input)
- **Pattern:** Writable variables not matching other patterns
- **Behavior:** Multi-step dialog using ForceReply
- **Example:** `user_name`, `email`, `comments`

### 4. **S3 File Upload Variables** ⭐ NEW
- **Pattern:** `s3_*` (e.g., `s3_chatHistory`, `s3_document`)
- **Behavior:** Prompts user to upload file → uploads to Cloudflare R2 → completes task with S3 URL
- **Example:** `s3_chatHistory`, `s3_avatar`, `s3_report`
- **Upload:** Uses boto3 with Cloudflare R2 (S3-compatible)

---

## 📦 Phase 1: Core Services Implementation

### 1.1 Camunda Service

**File:** `luka_bot/services/camunda_service.py`

**Purpose:** Singleton wrapper around `CamundaEngineClient` for all Camunda operations.

**Key Methods:**
```python
async def start_process(user_id: int, process_key: str, variables: dict) -> ProcessInstance
async def get_user_tasks(user_id: int) -> List[TaskSchema]
async def get_task(user_id: int, task_id: str) -> TaskSchema
async def get_task_variables(user_id: int, task_id: str) -> List[ProcessVariablesSchema]
async def complete_task(user_id: int, task_id: str, variables: dict) -> None
```

**Dependencies:**
- `camunda_client.clients.engine.client.CamundaEngineClient`
- `luka_bot.core.config.settings` (for `ENGINE_URL`)

**User Mapping Strategy:**
- Maps Telegram user ID → Camunda user ID
- Format: `tg_user_{telegram_id}`
- Creates Camunda user on first access
- Stores mapping in memory (future: Redis)

**Implementation:**
```python
"""
Camunda Engine integration service for luka_bot.
Manages Camunda connections, process instances, and tasks.
"""
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from camunda_client.clients.engine.client import CamundaEngineClient
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas.response import (
    TaskSchema,
    ProcessInstanceSchema,
    ProcessVariablesSchema
)
from luka_bot.core.config import settings
import httpx


@dataclass
class CamundaUserMapping:
    """Maps Telegram user to Camunda credentials"""
    telegram_id: int
    camunda_user_id: str
    camunda_password: str


class CamundaService:
    """Singleton service for Camunda operations"""
    
    _instance: Optional['CamundaService'] = None
    
    def __init__(self):
        self._client: Optional[CamundaEngineClient] = None
        self._transport = httpx.AsyncHTTPTransport(
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self._user_mappings: Dict[int, CamundaUserMapping] = {}
        
    @classmethod
    def get_instance(cls) -> 'CamundaService':
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def _get_client(self, telegram_user_id: int) -> CamundaEngineClient:
        """Get Camunda client for user"""
        # Get or create user mapping
        mapping = await self._get_or_create_user_mapping(telegram_user_id)
        
        auth_data = AuthData(
            username=mapping.camunda_user_id,
            password=mapping.camunda_password
        )
        
        return CamundaEngineClient(
            base_url=settings.ENGINE_URL,
            auth_data=auth_data,
            transport=self._transport
        )
    
    async def _get_or_create_user_mapping(self, telegram_user_id: int) -> CamundaUserMapping:
        """Get or create Camunda user for Telegram user"""
        if telegram_user_id in self._user_mappings:
            return self._user_mappings[telegram_user_id]
        
        # Create new Camunda user
        camunda_user_id = f"tg_user_{telegram_user_id}"
        camunda_password = f"pwd_{telegram_user_id}"  # TODO: Generate secure password
        
        # Store mapping
        mapping = CamundaUserMapping(
            telegram_id=telegram_user_id,
            camunda_user_id=camunda_user_id,
            camunda_password=camunda_password
        )
        self._user_mappings[telegram_user_id] = mapping
        
        logger.info(f"Created Camunda user mapping for Telegram user {telegram_user_id}")
        return mapping
    
    async def start_process(
        self,
        telegram_user_id: int,
        process_key: str,
        business_key: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> ProcessInstanceSchema:
        """Start a BPMN process for user"""
        client = await self._get_client(telegram_user_id)
        
        # Convert variables to Camunda format
        camunda_vars = self._format_variables(variables or {})
        
        try:
            process_instance = await client.start_process(
                process_key=process_key,
                business_key=business_key,
                variables=camunda_vars
            )
            logger.info(f"Started process {process_key} for user {telegram_user_id}: {process_instance.id}")
            return process_instance
        except Exception as e:
            logger.error(f"Failed to start process {process_key}: {e}")
            raise
    
    async def get_user_tasks(self, telegram_user_id: int) -> List[TaskSchema]:
        """Get all tasks assigned to user"""
        client = await self._get_client(telegram_user_id)
        mapping = self._user_mappings[telegram_user_id]
        
        from camunda_client.clients.engine.schemas import GetTasksFilterSchema
        
        filter_schema = GetTasksFilterSchema(
            assignee=mapping.camunda_user_id
        )
        
        tasks = await client.get_tasks(schema=filter_schema)
        return list(tasks)
    
    async def get_task(self, telegram_user_id: int, task_id: str) -> Optional[TaskSchema]:
        """Get specific task by ID"""
        client = await self._get_client(telegram_user_id)
        return await client.get_task(task_id)
    
    async def get_task_variables(
        self,
        telegram_user_id: int,
        task_id: str
    ) -> List[ProcessVariablesSchema]:
        """Get form variables for task"""
        client = await self._get_client(telegram_user_id)
        return await client.get_task_form_variables(task_id)
    
    async def complete_task(
        self,
        telegram_user_id: int,
        task_id: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """Complete a task with variables"""
        client = await self._get_client(telegram_user_id)
        camunda_vars = self._format_variables(variables or {})
        
        await client.complete_task(task_id, variables=camunda_vars)
        logger.info(f"Completed task {task_id} for user {telegram_user_id}")
    
    def _format_variables(self, variables: Dict[str, Any]) -> Dict:
        """Format variables for Camunda"""
        from camunda_client.types_ import Variable
        
        formatted = {}
        for key, value in variables.items():
            if isinstance(value, bool):
                formatted[key] = Variable(value=value, type="Boolean")
            elif isinstance(value, int):
                formatted[key] = Variable(value=value, type="Long")
            elif isinstance(value, float):
                formatted[key] = Variable(value=value, type="Double")
            else:
                formatted[key] = Variable(value=str(value), type="String")
        
        return formatted


# Singleton accessor
def get_camunda_service() -> CamundaService:
    """Get CamundaService singleton"""
    return CamundaService.get_instance()
```

---

### 1.2 S3 Upload Service ⭐ NEW

**File:** `luka_bot/services/s3_upload_service.py`

**Purpose:** Handle file uploads to Cloudflare R2 using boto3.

**Configuration Required:**
```python
# In luka_bot/core/config.py
class LukaSettings(BaseSettings):
    # ... existing settings ...
    
    # Cloudflare R2 (S3-compatible)
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_ENDPOINT_URL: str = ""  # e.g., https://<account-id>.r2.cloudflarestorage.com
    R2_BUCKET_NAME: str = "luka-bot-uploads"
    R2_PUBLIC_URL: str = ""  # e.g., https://files.yourdomain.com
```

**Implementation:**
```python
"""
S3-compatible file upload service for Cloudflare R2.
Handles Telegram file uploads and S3 storage.
"""
import boto3
import asyncio
from typing import Optional
from pathlib import Path
from datetime import datetime
from aiogram.types import Document, Message
from loguru import logger

from luka_bot.core.config import settings


class S3UploadService:
    """Service for uploading files to Cloudflare R2"""
    
    _instance: Optional['S3UploadService'] = None
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name='auto'  # Cloudflare R2 uses 'auto'
        )
        self.bucket_name = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL
    
    @classmethod
    def get_instance(cls) -> 'S3UploadService':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def upload_telegram_file(
        self,
        message: Message,
        document: Document,
        task_id: str,
        user_id: int,
        variable_name: str
    ) -> str:
        """
        Upload Telegram document to R2 and return public URL.
        
        Args:
            message: Telegram message containing the document
            document: Document object from Telegram
            task_id: Camunda task ID (for organizing files)
            user_id: Telegram user ID
            variable_name: Variable name (e.g., "s3_chatHistory")
            
        Returns:
            Public URL of uploaded file
        """
        try:
            # Download file from Telegram
            file = await message.bot.get_file(document.file_id)
            temp_path = f"/tmp/{user_id}_{task_id}_{document.file_name}"
            await message.bot.download_file(file.file_path, temp_path)
            
            # Generate S3 key
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"tasks/{user_id}/{task_id}/{variable_name}/{timestamp}_{document.file_name}"
            
            # Upload to R2 (async wrapper)
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._sync_upload,
                temp_path,
                s3_key,
                document.mime_type
            )
            
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
            # Return public URL
            public_url = f"{self.public_url}/{s3_key}"
            logger.info(f"Uploaded file to R2: {public_url}")
            return public_url
        
        except Exception as e:
            logger.error(f"Failed to upload file to R2: {e}")
            raise
    
    def _sync_upload(self, local_path: str, s3_key: str, content_type: str):
        """Synchronous upload for executor"""
        self.s3_client.upload_file(
            local_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'  # Or use signed URLs for private files
            }
        )


def get_s3_upload_service() -> S3UploadService:
    """Get S3UploadService singleton"""
    return S3UploadService.get_instance()
```

---

### 1.3 Task Service

**File:** `luka_bot/services/task_service.py`

**Purpose:** Task rendering, variable categorization, and lifecycle management.

**Key Methods:**
```python
async def render_task(task_id: str, message: Message, user_id: int, state: FSMContext) -> bool
async def complete_task_with_action(task_id: str, action: str, user_id: int, state: FSMContext) -> bool
def _categorize_variables(raw_vars: List) -> TaskVariables
def _build_action_keyboard(task_id: str, action_vars: List) -> InlineKeyboardMarkup
```

**Variable Categorization Logic:**
```python
def _categorize_variables(self, raw_variables: List) -> TaskVariables:
    """Categorize variables into text, action, form, and S3 types"""
    text_vars = []
    action_vars = []
    form_vars = []
    s3_vars = []
    
    for var in raw_variables:
        var_dict = var.model_dump() if hasattr(var, 'model_dump') else var
        var_name = var_dict.get("name", "")
        var_writable = var_dict.get("writable", False)
        
        # S3 file upload variables (highest priority)
        if var_name.startswith("s3_") and var_writable:
            s3_vars.append(var_dict)
        # Action variables
        elif var_name.startswith("action_") and var_writable:
            action_vars.append(var_dict)
        # Form variables (writable, not action or s3)
        elif var_writable:
            form_vars.append(var_dict)
        # Text variables (read-only)
        else:
            text_vars.append(var_dict)
    
    return TaskVariables(
        text_vars=text_vars,
        action_vars=action_vars,
        form_vars=form_vars,
        s3_vars=s3_vars
    )
```

**See full implementation in appendix section below.**

---

### 1.4 Dialog Service

**File:** `luka_bot/services/dialog_service.py`

**Purpose:** Multi-step dialog form handling with ForceReply.

**Key Methods:**
```python
async def start_task_dialog(task_id: str, variables: List, message: Message, user_id: int, state: FSMContext) -> bool
async def handle_dialog_response(message: Message, state: FSMContext) -> bool
async def _ask_next_variable(message: Message, state: FSMContext) -> None
async def _complete_task_with_variables(message: Message, state: FSMContext) -> bool
```

**State Storage:**
```python
await state.update_data({
    "task_dialog": {
        "task_id": task_id,
        "variables": variables,
        "current_index": 0,
        "collected_values": [],
        "user_id": user_id
    }
})
```

**Port from:** `bot_server/services/dialog_service.py`

---

### 1.5 Message Cleanup Service

**File:** `luka_bot/services/message_cleanup_service.py`

**Purpose:** Track and auto-delete task-related messages.

**Message Types:**
- `task_content` - Task description message
- `action_buttons` - Action button keyboard message
- `dialog_prompt` - ForceReply prompt message
- `file_upload_prompt` - File upload instruction message ⭐ NEW

**Key Methods:**
```python
async def track_task_message(task_id: str, message: Message, state: FSMContext, message_type: str)
async def delete_task_messages(task_id: str, bot: Bot, state: FSMContext, delete_types: Set[str] = None) -> int
```

**Implementation:**
```python
"""
Message cleanup service for task-related messages.
Tracks and auto-deletes messages when tasks complete.
"""
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from aiogram.types import Message, Bot
from aiogram.fsm.context import FSMContext
from loguru import logger


@dataclass
class TrackedMessage:
    """Info about tracked message"""
    message_id: int
    chat_id: int
    message_type: str
    original_content: Optional[str] = None


@dataclass
class TaskMessageTracking:
    """Tracking info for a task"""
    messages: List[TrackedMessage] = field(default_factory=list)
    task_id: str = ""
    created_at: float = 0.0


class MessageCleanupService:
    """Service for tracking and cleaning up task messages"""
    
    _instance: Optional['MessageCleanupService'] = None
    
    @classmethod
    def get_instance(cls) -> 'MessageCleanupService':
        """Get singleton"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def track_task_message(
        self,
        task_id: str,
        message: Message,
        state: FSMContext,
        message_type: str = "task_content",
        original_content: Optional[str] = None
    ) -> None:
        """Track a task-related message for later deletion"""
        try:
            data = await state.get_data()
            tracked = data.get("tracked_task_messages", {})
            
            if task_id not in tracked:
                tracked[task_id] = {
                    "messages": [],
                    "task_id": task_id,
                    "created_at": message.date.timestamp() if message.date else 0.0
                }
            
            tracked[task_id]["messages"].append({
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "message_type": message_type,
                "original_content": original_content or message.text or message.caption
            })
            
            await state.update_data({"tracked_task_messages": tracked})
            logger.debug(f"Tracking message {message.message_id} for task {task_id}")
        
        except Exception as e:
            logger.error(f"Failed to track message for task {task_id}: {e}")
    
    async def delete_task_messages(
        self,
        task_id: str,
        bot: Bot,
        state: FSMContext,
        delete_types: Optional[Set[str]] = None
    ) -> int:
        """Delete all tracked messages for a task"""
        try:
            data = await state.get_data()
            tracked = data.get("tracked_task_messages", {})
            
            if task_id not in tracked:
                return 0
            
            messages = tracked[task_id].get("messages", [])
            
            # Filter by type if specified
            if delete_types:
                messages = [m for m in messages if m.get("message_type") in delete_types]
            
            # Delete messages
            deleted_count = 0
            for msg_info in messages:
                try:
                    await bot.delete_message(
                        chat_id=msg_info["chat_id"],
                        message_id=msg_info["message_id"]
                    )
                    deleted_count += 1
                    await asyncio.sleep(0.1)  # Rate limit protection
                except Exception as e:
                    logger.debug(f"Could not delete message {msg_info['message_id']}: {e}")
            
            # Remove from tracking
            del tracked[task_id]
            await state.update_data({"tracked_task_messages": tracked})
            
            logger.info(f"Deleted {deleted_count} messages for task {task_id}")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Failed to delete task messages: {e}")
            return 0


def get_message_cleanup_service() -> MessageCleanupService:
    """Get MessageCleanupService singleton"""
    return MessageCleanupService.get_instance()
```

---

## 📊 Phase 2: FSM States & Data Models

### 2.1 FSM States

**File:** `luka_bot/handlers/states.py`

```python
from aiogram.fsm.state import State, StatesGroup

class ProcessStates(StatesGroup):
    """States for Camunda process execution"""
    idle = State()  # No active process
    process_active = State()  # Process running
    task_waiting = State()  # Waiting for task completion
    dialog_active = State()  # Dialog form active
    waiting_for_input = State()  # Waiting for ForceReply response
    file_upload_pending = State()  # Waiting for file upload ⭐ NEW
    processing_file = State()  # File being processed (upload to R2) ⭐ NEW
```

---

### 2.2 Data Models

**File:** `luka_bot/models/process_models.py`

```python
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
    s3_variables: List[Dict[str, Any]] = field(default_factory=list)  # ⭐ NEW
    current_dialog_index: int = 0
    collected_values: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TaskVariables:
    """Categorized task variables"""
    text_vars: List[Dict[str, Any]]
    action_vars: List[Dict[str, Any]]
    form_vars: List[Dict[str, Any]]
    s3_vars: List[Dict[str, Any]]  # ⭐ NEW
```

---

## 🎨 Phase 3: Keyboards & UI Components

### 3.1 Inline Keyboards

**File:** `luka_bot/keyboards/inline/task_keyboards.py`

```python
"""
Inline keyboards for Camunda task actions.
"""
from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from loguru import logger


class TaskActionCallback(CallbackData, prefix="act"):
    """Callback data for task actions (compact format for 64-byte limit)"""
    task_id: str  # First 8 chars of task ID
    action: str  # Action variable name


def build_action_keyboard(
    task_id: str,
    action_vars: List[Dict[str, Any]],
    show_cancel: bool = True
) -> InlineKeyboardMarkup:
    """
    Build inline keyboard for action variables.
    
    Args:
        task_id: Full task ID (will be truncated to 8 chars)
        action_vars: List of action variable dicts
        show_cancel: Whether to show cancel button
        
    Returns:
        InlineKeyboardMarkup with action buttons
    """
    buttons = []
    row = []
    
    for var in action_vars:
        var_name = var.get("name")
        
        # Skip action_back (rendered separately if needed)
        if var_name == "action_back":
            continue
        
        # Get label (remove action_ prefix and title case)
        var_label = var.get("label", var_name.replace("action_", "").replace("_", " ").title())
        
        # Create callback (use only first 8 chars of task ID to stay under 64 bytes)
        callback = TaskActionCallback(
            task_id=task_id[:8],
            action=var_name
        )
        
        row.append(InlineKeyboardButton(
            text=var_label,
            callback_data=callback.pack()
        ))
        
        # Max 2 buttons per row
        if len(row) >= 2:
            buttons.append(row)
            row = []
    
    # Add remaining buttons
    if row:
        buttons.append(row)
    
    # Add cancel button
    if show_cancel:
        buttons.append([InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=TaskActionCallback(task_id=task_id[:8], action="cancel").pack()
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_file_upload_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for file upload prompt.
    
    Args:
        task_id: Full task ID
        
    Returns:
        InlineKeyboardMarkup with cancel button
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Cancel Upload",
            callback_data=TaskActionCallback(task_id=task_id[:8], action="cancel_upload").pack()
        )]
    ])


def build_process_confirmation_keyboard(process_id: str) -> InlineKeyboardMarkup:
    """
    Build keyboard for process confirmation.
    
    Args:
        process_id: Process instance ID
        
    Returns:
        InlineKeyboardMarkup with start/cancel buttons
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Start", callback_data=f"process_start:{process_id[:8]}"),
            InlineKeyboardButton(text="❌ Cancel", callback_data=f"process_cancel:{process_id[:8]}")
        ]
    ])
```

---

## 🎮 Phase 4: Handlers & Callbacks

### 4.1 Process Start Handler

**File:** `luka_bot/handlers/processes/__init__.py`

```python
"""
Process handlers package.
"""
from aiogram import Router

from . import start_process
from . import task_actions
from . import file_upload
from . import dialog_form

# Create main processes router
router = Router(name="processes")

# Include sub-routers
router.include_router(start_process.router)
router.include_router(task_actions.router)
router.include_router(file_upload.router)
router.include_router(dialog_form.router)

__all__ = ["router"]
```

**File:** `luka_bot/handlers/processes/start_process.py`

```python
"""
Process start handler for initiating BPMN workflows.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.task_service import get_task_service
from luka_bot.handlers.states import ProcessStates
from luka_bot.utils.i18n_helper import get_message as _

router = Router(name="process_start")


@router.callback_query(F.data == "start_history_import")
async def handle_start_history_import(callback: CallbackQuery, state: FSMContext):
    """
    Start history import BPMN process.
    Triggered from group admin menu.
    """
    user_id = callback.from_user.id
    
    # Extract group_id from state
    data = await state.get_data()
    group_id = data.get("current_group_id")
    
    if not group_id:
        await callback.answer("⚠️ No group selected", show_alert=True)
        return
    
    # Get group name for business key
    from luka_bot.services.group_service import get_group_service
    group_service = get_group_service()
    group_link = await group_service.get_group_link(user_id, group_id)
    group_name = group_link.thread_name if group_link else f"Group {group_id}"
    
    # Start Camunda process
    camunda_service = get_camunda_service()
    
    try:
        process_instance = await camunda_service.start_process(
            telegram_user_id=user_id,
            process_key="community_audit",
            business_key=f"import_{group_id}_{user_id}",
            variables={
                "group_id": str(group_id),
                "telegram_user_id": str(user_id),
                "group_name": group_name
            }
        )
        
        # Set FSM state
        await state.set_state(ProcessStates.process_active)
        await state.update_data({
            "active_process": process_instance.id,
            "process_key": "community_audit",
            "group_id": group_id
        })
        
        await callback.answer("✅ Starting import process...")
        logger.info(f"Started process {process_instance.id} for user {user_id}, group {group_id}")
        
        # Poll for first task
        await poll_and_render_next_task(callback.message, user_id, process_instance.id, state)
    
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        await callback.answer("❌ Failed to start process", show_alert=True)


async def poll_and_render_next_task(
    message: Message,
    user_id: int,
    process_id: str,
    state: FSMContext
):
    """
    Poll for next task in process and render it.
    
    Args:
        message: Message to respond to
        user_id: Telegram user ID
        process_id: Camunda process instance ID
        state: FSM context
    """
    camunda_service = get_camunda_service()
    task_service = get_task_service()
    
    try:
        # Get user's tasks
        tasks = await camunda_service.get_user_tasks(user_id)
        
        # Filter by process
        process_tasks = [t for t in tasks if t.process_instance_id == process_id]
        
        if not process_tasks:
            # No tasks yet - either processing or complete
            logger.info(f"No tasks found for process {process_id}, checking if complete")
            
            # TODO: Check if process is complete or just waiting
            # For now, show waiting message
            await message.answer("⏳ Processing your request...")
            return
        
        # Render first task
        task = process_tasks[0]
        logger.info(f"Rendering task {task.id} for process {process_id}")
        
        await state.update_data({"current_task_id": task.id})
        await task_service.render_task(task.id, message, user_id, state)
    
    except Exception as e:
        logger.error(f"Failed to poll/render task for process {process_id}: {e}")
        await message.answer(f"❌ Error rendering task: {str(e)}")
```

---

### 4.2 Task Action Handler

**File:** `luka_bot/handlers/processes/task_actions.py`

```python
"""
Task action handler for button callbacks.
"""
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.keyboards.inline.task_keyboards import TaskActionCallback
from luka_bot.services.task_service import get_task_service
from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.message_cleanup_service import get_message_cleanup_service
from luka_bot.handlers.processes.start_process import poll_and_render_next_task

router = Router(name="task_actions")


@router.callback_query(TaskActionCallback.filter())
async def handle_task_action(
    callback: CallbackQuery,
    callback_data: TaskActionCallback,
    state: FSMContext
):
    """
    Handle task action button clicks.
    
    Args:
        callback: Callback query from button press
        callback_data: Parsed callback data
        state: FSM context
    """
    await callback.answer()
    
    user_id = callback.from_user.id
    task_service = get_task_service()
    
    # Get full task ID from state
    data = await state.get_data()
    current_task_id = data.get("current_task_id")
    
    if not current_task_id:
        await callback.answer("⚠️ Task not found", show_alert=True)
        logger.warning(f"Task action called but no current_task_id in state for user {user_id}")
        return
    
    # Handle different actions
    if callback_data.action == "cancel" or callback_data.action == "cancel_upload":
        await handle_task_cancel(callback, current_task_id, state)
    else:
        # Complete task with action
        logger.info(f"Completing task {current_task_id} with action {callback_data.action}")
        
        success = await task_service.complete_task_with_action(
            task_id=current_task_id,
            action_name=callback_data.action,
            user_id=user_id,
            state=state
        )
        
        if success:
            # Edit message to show completion
            await callback.message.edit_text(
                f"✅ Action completed: {callback_data.action.replace('action_', '').replace('_', ' ').title()}",
                reply_markup=None
            )
            
            # Clean up messages
            cleanup_service = get_message_cleanup_service()
            await cleanup_service.delete_task_messages(current_task_id, callback.bot, state)
            
            # Poll for next task
            process_id = data.get("active_process")
            if process_id:
                await poll_and_render_next_task(callback.message, user_id, process_id, state)
            else:
                await callback.message.answer("✅ Task completed successfully!")
        else:
            await callback.answer("❌ Failed to complete task", show_alert=True)


async def handle_task_cancel(callback: CallbackQuery, task_id: str, state: FSMContext):
    """
    Handle task/process cancellation.
    
    Args:
        callback: Callback query
        task_id: Task ID to cancel
        state: FSM context
    """
    # Delete messages
    cleanup_service = get_message_cleanup_service()
    await cleanup_service.delete_task_messages(task_id, callback.bot, state)
    
    # Clear process state
    await state.set_state(None)
    await state.update_data({
        "active_process": None,
        "current_task_id": None,
        "current_s3_variable": None,
        "expected_file_extension": None
    })
    
    await callback.message.answer("❌ Process cancelled")
    logger.info(f"User {callback.from_user.id} cancelled task {task_id}")
```

---

### 4.3 File Upload Handler ⭐ NEW

**File:** `luka_bot/handlers/processes/file_upload.py`

```python
"""
File upload handler for S3 variables.
Handles Telegram file uploads and uploads to Cloudflare R2.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.handlers.states import ProcessStates
from luka_bot.services.s3_upload_service import get_s3_upload_service
from luka_bot.services.camunda_service import get_camunda_service
from luka_bot.services.message_cleanup_service import get_message_cleanup_service
from luka_bot.handlers.processes.start_process import poll_and_render_next_task
from luka_bot.utils.i18n_helper import get_message as _

router = Router(name="file_upload")


@router.message(F.document, ProcessStates.file_upload_pending)
async def handle_file_upload(message: Message, state: FSMContext):
    """
    Handle file upload for S3 variables.
    Uploads to Cloudflare R2 and completes task with URL.
    """
    user_id = message.from_user.id
    
    try:
        # Get task context from state
        data = await state.get_data()
        task_id = data.get("current_task_id")
        s3_variable_name = data.get("current_s3_variable")
        expected_extension = data.get("expected_file_extension")
        
        if not task_id or not s3_variable_name:
            await message.answer("⚠️ Upload context lost. Please restart the process.")
            logger.warning(f"File upload without context for user {user_id}")
            return
        
        # Validate file extension if specified
        if expected_extension:
            file_name = message.document.file_name
            if not file_name.endswith(expected_extension):
                await message.answer(
                    f"⚠️ Please upload a {expected_extension} file.\n"
                    f"Received: {file_name}"
                )
                return
        
        # Validate file size (max 20MB for Telegram, but can set lower limit)
        max_size_mb = 20
        file_size_mb = message.document.file_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            await message.answer(
                f"⚠️ File too large. Maximum size: {max_size_mb}MB\n"
                f"Your file: {file_size_mb:.1f}MB"
            )
            return
        
        # Show processing message
        processing_msg = await message.answer("⏳ Uploading file to storage...")
        
        # Set processing state
        await state.set_state(ProcessStates.processing_file)
        
        # Upload to R2
        logger.info(f"Uploading file {message.document.file_name} for task {task_id}, user {user_id}")
        s3_service = get_s3_upload_service()
        file_url = await s3_service.upload_telegram_file(
            message=message,
            document=message.document,
            task_id=task_id,
            user_id=user_id,
            variable_name=s3_variable_name
        )
        
        logger.info(f"File uploaded to: {file_url}")
        
        # Complete task with file URL
        camunda_service = get_camunda_service()
        await camunda_service.complete_task(
            telegram_user_id=user_id,
            task_id=task_id,
            variables={s3_variable_name: file_url}
        )
        
        # Update message
        await processing_msg.edit_text(f"✅ File uploaded successfully!")
        
        # Clean up task messages
        cleanup_service = get_message_cleanup_service()
        await cleanup_service.delete_task_messages(task_id, message.bot, state)
        
        # Clear upload context
        await state.update_data({
            "current_s3_variable": None,
            "expected_file_extension": None
        })
        
        # Poll for next task
        process_id = data.get("active_process")
        await poll_and_render_next_task(message, user_id, process_id, state)
    
    except Exception as e:
        logger.error(f"File upload failed for user {user_id}: {e}")
        await message.answer(f"❌ File upload failed: {str(e)}")
        await state.set_state(ProcessStates.file_upload_pending)  # Allow retry


@router.message(ProcessStates.file_upload_pending)
async def handle_non_document_during_upload(message: Message, state: FSMContext):
    """Handle non-document messages during file upload state"""
    await message.answer(
        "⚠️ Please upload a file using the 📎 attachment button.\n"
        "Or use /cancel to cancel the upload."
    )
```

---

### 4.4 Dialog Form Handler

**File:** `luka_bot/handlers/processes/dialog_form.py`

```python
"""
Dialog form handler for multi-step form variables.
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.handlers.states import ProcessStates
from luka_bot.services.dialog_service import get_dialog_service

router = Router(name="dialog_form")


@router.message(F.reply_to_message, ProcessStates.waiting_for_input)
async def handle_dialog_input(message: Message, state: FSMContext):
    """
    Handle dialog form input (ForceReply responses).
    
    Args:
        message: User's response message
        state: FSM context
    """
    dialog_service = get_dialog_service()
    await dialog_service.handle_dialog_response(message, state)


@router.message(ProcessStates.waiting_for_input)
async def handle_dialog_fallback(message: Message, state: FSMContext):
    """
    Handle messages during dialog that aren't replies.
    Fallback for users who don't use reply mechanism.
    """
    dialog_service = get_dialog_service()
    await dialog_service.handle_dialog_input(message, state)
```

---

## 🔗 Phase 5: Integration with Existing Features

### 5.1 Update Group Admin Handler

**File:** `luka_bot/handlers/group_admin.py` (update)

**Location:** Around line 279-298 (current placeholder)

**Replace this:**
```python
@router.callback_query(F.data.startswith("group_import:"))
async def handle_group_import(callback: CallbackQuery, state: FSMContext):
    """Handle history import - Coming soon"""
    await callback.answer("📥 History import coming soon!", show_alert=True)
```

**With this:**
```python
@router.callback_query(F.data.startswith("group_import:"))
async def handle_group_import(callback: CallbackQuery, state: FSMContext):
    """
    Handle history import button - Start BPMN process.
    Initiates the community_audit workflow.
    """
    try:
        group_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Check admin permissions
        from luka_bot.utils.permissions import is_user_admin_in_group
        is_admin = await is_user_admin_in_group(callback.bot, group_id, user_id)
        
        if not is_admin:
            await callback.answer(
                _("group.import.admin_only", lang=user_id),
                show_alert=True
            )
            return
        
        # Store group context in state
        await state.update_data({"current_group_id": group_id})
        
        # Trigger process start
        from luka_bot.handlers.processes.start_process import handle_start_history_import
        await handle_start_history_import(callback, state)
        
        logger.info(f"User {user_id} started history import for group {group_id}")
    
    except Exception as e:
        logger.error(f"Failed to start import process: {e}")
        await callback.answer("❌ Error starting process", show_alert=True)
```

---

### 5.2 Register Process Handlers

**File:** `luka_bot/handlers/__init__.py` (update)

**Add import:**
```python
from luka_bot.handlers.processes import router as processes_router
```

**Register router:**
```python
# Include processes router
router.include_router(processes_router)
```

**Update logger message:**
```python
logger.info(
    f"📦 Phase 4 handlers registered: /start, /groups, /profile, /reset, "
    f"group commands, group admin, group settings, group messages, "
    f"reply keyboard, forwarded messages, streaming DM, processes"  # Added processes
)
```

---

## 🧪 Phase 6: Testing

### 6.1 Unit Tests

**File:** `tests/services/test_camunda_service.py`

```python
"""Unit tests for CamundaService"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from luka_bot.services.camunda_service import CamundaService, get_camunda_service


@pytest.fixture
def camunda_service():
    """Create CamundaService instance for testing"""
    service = CamundaService()
    return service


@pytest.mark.asyncio
async def test_start_process(camunda_service):
    """Test starting a process"""
    # Mock the client
    with patch.object(camunda_service, '_get_client') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.start_process.return_value = Mock(id="process-123")
        mock_client.return_value = mock_instance
        
        result = await camunda_service.start_process(
            telegram_user_id=12345,
            process_key="test_process",
            variables={"test_var": "test_value"}
        )
        
        assert result.id == "process-123"
        mock_instance.start_process.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_tasks(camunda_service):
    """Test getting user tasks"""
    # TODO: Implement test
    pass


@pytest.mark.asyncio
async def test_complete_task(camunda_service):
    """Test task completion"""
    # TODO: Implement test
    pass
```

**File:** `tests/services/test_s3_upload_service.py`

```python
"""Unit tests for S3UploadService"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from luka_bot.services.s3_upload_service import S3UploadService


@pytest.fixture
def s3_service():
    """Create S3UploadService instance for testing"""
    with patch('boto3.client'):
        service = S3UploadService()
        return service


@pytest.mark.asyncio
async def test_upload_telegram_file(s3_service):
    """Test file upload to R2"""
    # Mock Telegram message and document
    mock_message = Mock()
    mock_message.bot.get_file = AsyncMock(return_value=Mock(file_path="test/path"))
    mock_message.bot.download_file = AsyncMock()
    
    mock_document = Mock()
    mock_document.file_id = "file123"
    mock_document.file_name = "test.json"
    mock_document.mime_type = "application/json"
    
    # Mock S3 upload
    with patch.object(s3_service, '_sync_upload'):
        result = await s3_service.upload_telegram_file(
            message=mock_message,
            document=mock_document,
            task_id="task-123",
            user_id=12345,
            variable_name="s3_test"
        )
        
        assert result.startswith("https://")
        assert "test.json" in result


@pytest.mark.asyncio
async def test_upload_error_handling(s3_service):
    """Test error handling during upload"""
    # TODO: Implement test for upload failures
    pass
```

**File:** `tests/services/test_task_service.py`

```python
"""Unit tests for TaskService"""
import pytest
from unittest.mock import Mock, AsyncMock

from luka_bot.services.task_service import TaskService, TaskVariables


@pytest.fixture
def task_service():
    """Create TaskService instance for testing"""
    return TaskService()


def test_categorize_variables(task_service):
    """Test variable categorization"""
    raw_vars = [
        {"name": "group_name", "writable": False, "value": "Test Group"},
        {"name": "action_approve", "writable": True},
        {"name": "action_reject", "writable": True},
        {"name": "user_email", "writable": True},
        {"name": "s3_chatHistory", "writable": True},
    ]
    
    result = task_service._categorize_variables(raw_vars)
    
    assert len(result.text_vars) == 1
    assert len(result.action_vars) == 2
    assert len(result.form_vars) == 1
    assert len(result.s3_vars) == 1
    assert result.s3_vars[0]["name"] == "s3_chatHistory"


def test_build_action_keyboard(task_service):
    """Test action keyboard building"""
    action_vars = [
        {"name": "action_approve", "label": "Approve"},
        {"name": "action_reject", "label": "Reject"},
    ]
    
    keyboard = task_service._build_action_keyboard("task-123", action_vars)
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= 2  # Action rows + cancel


@pytest.mark.asyncio
async def test_render_task(task_service):
    """Test task rendering"""
    # TODO: Implement comprehensive render test
    pass
```

---

### 6.2 Integration Tests

**File:** `tests/integration/test_history_import_flow.py`

```python
"""Integration test for complete history import flow"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from luka_bot.handlers.processes.start_process import handle_start_history_import


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_history_import():
    """Test complete history import workflow end-to-end"""
    # Mock callback query
    mock_callback = Mock()
    mock_callback.from_user.id = 12345
    mock_callback.answer = AsyncMock()
    mock_callback.message = Mock()
    mock_callback.message.answer = AsyncMock()
    
    # Mock FSM state
    mock_state = AsyncMock()
    mock_state.get_data = AsyncMock(return_value={"current_group_id": -1001234567})
    mock_state.set_state = AsyncMock()
    mock_state.update_data = AsyncMock()
    
    # Mock services
    with patch('luka_bot.services.camunda_service.get_camunda_service') as mock_camunda, \
         patch('luka_bot.services.group_service.get_group_service') as mock_group:
        
        mock_camunda_instance = AsyncMock()
        mock_camunda_instance.start_process.return_value = Mock(id="process-123")
        mock_camunda.return_value = mock_camunda_instance
        
        mock_group_instance = AsyncMock()
        mock_group_instance.get_group_link.return_value = Mock(thread_name="Test Group")
        mock_group.return_value = mock_group_instance
        
        # Execute handler
        await handle_start_history_import(mock_callback, mock_state)
        
        # Verify process started
        mock_camunda_instance.start_process.assert_called_once()
        mock_state.set_state.assert_called()
        mock_callback.answer.assert_called()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_file_upload_and_processing():
    """Test file upload to R2 and task completion"""
    # TODO: Implement file upload integration test
    pass
```

---

## 📝 Phase 7: Configuration & Deployment

### 7.1 Environment Variables

Add to `.env`:

```bash
# Camunda Engine
ENGINE_URL=http://localhost:8080/engine-rest
ENGINE_USERNAME=demo
ENGINE_PASSWORD=demo
ENGINE_USERS_GROUP_ID=camunda-admin

# Cloudflare R2 (S3-compatible)
R2_ACCESS_KEY_ID=your_r2_access_key_here
R2_SECRET_ACCESS_KEY=your_r2_secret_key_here
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_BUCKET_NAME=luka-bot-uploads
R2_PUBLIC_URL=https://files.yourdomain.com
```

### 7.2 Configuration Update

**File:** `luka_bot/core/config.py`

Add to `LukaSettings`:

```python
    # Camunda BPMN Integration
    ENGINE_URL: str = Field(
        default="http://localhost:8080/engine-rest",
        description="Camunda Engine REST API URL"
    )
    ENGINE_USERNAME: str = Field(default="demo", description="Camunda username")
    ENGINE_PASSWORD: str = Field(default="demo", description="Camunda password")
    ENGINE_USERS_GROUP_ID: str = Field(default="camunda-admin", description="Camunda users group ID")

# Cloudflare R2 (S3-compatible storage)
R2_ACCESS_KEY_ID: str = Field(default="", description="R2 Access Key ID")
R2_SECRET_ACCESS_KEY: str = Field(default="", description="R2 Secret Access Key")
R2_ENDPOINT_URL: str = Field(default="", description="R2 Endpoint URL")
R2_BUCKET_NAME: str = Field(default="luka-bot-uploads", description="R2 Bucket Name")
R2_PUBLIC_URL: str = Field(default="", description="R2 Public URL for uploaded files")
```

### 7.3 Dependencies

**File:** `requirements.txt`

Add:

```txt
# Camunda integration (if not already present)
camunda-client>=0.1.0

# S3/R2 file upload
boto3>=1.28.0
```

---

### 7.4 BPMN Deployment

**Deploy community_audit process:**

```bash
curl -X POST http://localhost:8080/engine-rest/deployment/create \
  -F "deployment-name=community_audit" \
  -F "deployment-source=luka_bot" \
  -F "file=@luka_bot/docs/community_analytics.bpmn"
```

**Or use Camunda Modeler** to deploy the BPMN file.

---

### 7.5 R2 Bucket Configuration

1. **Create Bucket:**
   ```bash
   # Via Cloudflare Dashboard or CLI
   wrangler r2 bucket create luka-bot-uploads
   ```

2. **Configure CORS:**
   ```json
   [
     {
       "AllowedOrigins": ["*"],
       "AllowedMethods": ["GET", "PUT", "POST"],
       "AllowedHeaders": ["*"],
       "ExposeHeaders": ["ETag"],
       "MaxAgeSeconds": 3000
     }
   ]
   ```

3. **Set Up Public Access:**
   - Enable public read access via R2 settings
   - Or configure custom domain for public URL

---

## 📖 Phase 8: Documentation

### 8.1 User Documentation

**File:** `docs_user/en/features/workflows.md`

```markdown
# Workflows & Process Automation

Luka Bot supports automated workflows using BPMN (Business Process Model and Notation) for complex multi-step tasks.

## Starting a Workflow

1. Navigate to your group settings
2. Click **"📥 Import History"** button
3. Follow the step-by-step instructions
4. Upload requested files when prompted
5. Wait for completion confirmation

## Understanding Task Types

### Action Buttons
Quick one-click actions that complete tasks immediately.
Example: Approve/Reject buttons

### Form Inputs
Step-by-step forms where you provide information.
Bot will ask you questions one by one using ForceReply.

### File Uploads
Tasks that require file uploads (e.g., JSON history files).
Use the 📎 attachment button to upload files.

## Cancelling Workflows

Click the **"❌ Cancel"** button at any time to stop a workflow.
All related messages will be automatically cleaned up.

## Troubleshooting

**Problem:** File upload rejected  
**Solution:** Ensure file meets format requirements (e.g., .json for history)

**Problem:** Task seems stuck  
**Solution:** Use /cancel command and restart the workflow

**Problem:** "Task not found" error  
**Solution:** The task may have timed out. Restart the workflow.
```

---

### 8.2 Developer Documentation

**File:** `luka_bot/services/README.md` (add section)

```markdown
## Camunda BPMN Integration

### Architecture

The Camunda integration consists of 5 main services:

1. **CamundaService** - Camunda Engine API wrapper
2. **TaskService** - Task rendering and categorization
3. **DialogService** - Multi-step form handling
4. **S3UploadService** - File uploads to Cloudflare R2
5. **MessageCleanupService** - Auto-cleanup of task messages

### Creating a New BPMN Process

1. **Design BPMN** in Camunda Modeler
2. **Define Variables:**
   - Read-only: Display information
   - `action_*`: Action buttons
   - `s3_*`: File upload fields
   - Other writable: Form inputs
3. **Deploy Process:**
   ```bash
   curl -X POST http://localhost:8080/engine-rest/deployment/create \
     -F "deployment-name=my_process" \
     -F "file=@my_process.bpmn"
   ```
4. **Add Start Trigger** in bot handlers
5. **Test End-to-End**

### Variable Naming Conventions

- **Text Variables:** `group_name`, `total_count` (read-only)
- **Action Variables:** `action_approve`, `action_reject` (buttons)
- **Form Variables:** `user_email`, `description` (dialog)
- **S3 Variables:** `s3_chatHistory`, `s3_report` (file upload)

### External Workers

For long-running tasks (e.g., file processing), use external workers:

```python
from camunda_client.worker import ExternalTaskWorker

async def process_file(task):
    file_url = task.variables.get("s3_file")
    # Process file...
    return {"result": "success"}

worker = ExternalTaskWorker(worker_id="file_processor")
worker.subscribe("process_file_topic", process_file)
await worker.start()
```

### Error Handling

Always wrap process operations in try/except:

```python
try:
    await camunda_service.complete_task(user_id, task_id, variables)
except Exception as e:
    logger.error(f"Task completion failed: {e}")
    # Allow user to retry or cancel
```
```

---

## ⚠️ Critical Implementation Notes

### 1. Callback Data Limit (64 bytes)
Telegram inline buttons have a **64-byte limit**. Always use compact formats:

✅ **Good:** `act:12345678:approve`  
❌ **Bad:** `action_complete:long-task-id-123456789:action_approve`

### 2. Message Cleanup
Always track task messages for deletion to prevent chat clutter.

### 3. S3 File Security ⭐
- Use `public-read` ACL for public files (like history exports)
- Use signed URLs for private/sensitive files
- Consider adding virus scanning for uploaded files

### 4. File Size Limits
- Telegram: Max 20MB for files
- Cloudflare R2: No per-file limit (but consider costs)
- Add validation for max file size in upload handler

### 5. Error Recovery
- Handle task completion failures gracefully
- Tasks might be completed via external workers
- Implement retry logic with exponential backoff

### 6. Rate Limiting
- Add delays when deleting multiple messages: `await asyncio.sleep(0.1)`
- Implement request throttling for Camunda API calls

### 7. State Management
- Always check FSM state before processing
- Clear state properly on cancellation
- Handle state loss gracefully (e.g., restart prompt)

---

## 📋 Implementation Checklist

### Phase 1: Core Services ✅
- [ ] Create `luka_bot/services/camunda_service.py`
- [ ] Create `luka_bot/services/s3_upload_service.py`
- [ ] Create `luka_bot/services/task_service.py`
- [ ] Create `luka_bot/services/dialog_service.py`
- [ ] Create `luka_bot/services/message_cleanup_service.py`

### Phase 2: FSM & Models ✅
- [ ] Add ProcessStates to `luka_bot/handlers/states.py`
- [ ] Create `luka_bot/models/process_models.py`

### Phase 3: Keyboards ✅
- [ ] Create `luka_bot/keyboards/inline/task_keyboards.py`

### Phase 4: Handlers ✅
- [ ] Create `luka_bot/handlers/processes/__init__.py`
- [ ] Create `luka_bot/handlers/processes/start_process.py`
- [ ] Create `luka_bot/handlers/processes/task_actions.py`
- [ ] Create `luka_bot/handlers/processes/file_upload.py`
- [ ] Create `luka_bot/handlers/processes/dialog_form.py`

### Phase 5: Integration ✅
- [ ] Update `luka_bot/handlers/group_admin.py`
- [ ] Register processes router in `luka_bot/handlers/__init__.py`

### Phase 6: Configuration ✅
- [ ] Add R2 settings to `luka_bot/core/config.py`
- [ ] Add boto3 to requirements.txt
- [ ] Create .env configuration template

### Phase 7: Testing ✅
- [ ] Write unit tests for CamundaService
- [ ] Write unit tests for S3UploadService
- [ ] Write unit tests for TaskService
- [ ] Write integration tests for history import flow

### Phase 8: Deployment ✅
- [ ] Deploy BPMN process to Camunda
- [ ] Configure Cloudflare R2 bucket
- [ ] Test with real bot and engine

### Phase 9: Documentation ✅
- [ ] Write user guide
- [ ] Write developer guide
- [ ] Add inline code documentation

---

## 🚀 Deployment Steps

### Step 1: Install Dependencies
```bash
cd /Users/evgenyvakhteev/Documents/src/dexguru/bot
pip install boto3>=1.28.0
```

### Step 2: Configure Environment
```bash
# Add to .env
cat >> .env << EOF
ENGINE_URL=http://localhost:8080/engine-rest
ENGINE_USERNAME=demo
ENGINE_PASSWORD=demo
ENGINE_USERS_GROUP_ID=camunda-admin
R2_ACCESS_KEY_ID=your_key_here
R2_SECRET_ACCESS_KEY=your_secret_here
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
R2_BUCKET_NAME=luka-bot-uploads
R2_PUBLIC_URL=https://files.yourdomain.com
EOF
```

### Step 3: Deploy BPMN Process
```bash
curl -X POST http://localhost:8080/engine-rest/deployment/create \
  -F "deployment-name=community_audit" \
  -F "deployment-source=luka_bot" \
  -F "file=@luka_bot/docs/community_analytics.bpmn"
```

### Step 4: Create R2 Bucket
```bash
# Via Cloudflare Dashboard or CLI
wrangler r2 bucket create luka-bot-uploads
```

### Step 5: Run Tests
```bash
pytest tests/services/test_camunda_service.py -v
pytest tests/services/test_s3_upload_service.py -v
pytest tests/integration/test_history_import_flow.py -v
```

### Step 6: Start Bot
```bash
python -m luka_bot
```

### Step 7: Test in Telegram
1. Start bot: `/start`
2. Go to groups: `/groups`
3. Select a group
4. Click "Settings" → "📥 Import History"
5. Follow workflow prompts
6. Upload test JSON file
7. Verify completion

---

## 📊 Estimated Timeline

- **Phase 1 (Core Services):** 4-5 days
- **Phase 2 (FSM & Models):** 1-2 days
- **Phase 3 (Keyboards):** 1-2 days
- **Phase 4 (Handlers):** 3-4 days
- **Phase 5 (Integration):** 1-2 days
- **Phase 6 (Configuration):** 1 day
- **Phase 7 (Testing):** 2-3 days
- **Phase 8 (Deployment):** 1 day
- **Phase 9 (Documentation):** 1-2 days

**Total MVP:** ~15-20 days  
**Total with Testing & Docs:** ~20-25 days

---

## 🎯 Success Criteria

✅ Users can start processes from Telegram  
✅ Tasks render correctly with all 4 variable types  
✅ File uploads work to Cloudflare R2  
✅ Task completion triggers next task automatically  
✅ Messages clean up properly after task completion  
✅ Error handling is graceful and informative  
✅ Full test coverage for critical paths  
✅ Documentation is complete and accurate  

---

## 🔮 Future Enhancements

1. **WebSocket Real-Time Updates** - Auto-refresh when tasks complete
2. **Multiple Concurrent Processes** - Allow users to run multiple workflows
3. **Process Templates** - Pre-built workflows for common tasks
4. **Process Analytics Dashboard** - Track completion rates, bottlenecks
5. **Advanced File Processing** - Validate file contents before upload
6. **Batch Operations** - Upload multiple files at once
7. **Process Versioning** - Support multiple BPMN versions
8. **Custom Variable Types** - Extend beyond action/form/s3
9. **Process Monitoring** - Real-time process status tracking
10. **Scheduled Processes** - Cron-like process execution

---

## 📞 Support & Contact

For questions or issues:
- GitHub Issues: [link]
- Documentation: [link]
- Slack Channel: [link]

---

**Document Version:** 1.0  
**Last Updated:** October 14, 2025  
**Author:** AI Assistant  
**Status:** ✅ Ready for Implementation 🚀

