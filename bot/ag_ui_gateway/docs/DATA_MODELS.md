# Data Models & Schemas

**Version:** 1.0  
**Date:** October 18, 2025

---

## Overview

This document defines all Pydantic models used in the AG-UI Gateway API for request/response validation and WebSocket event schemas.

---

## Core Models

### KnowledgeBase

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class KBVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"

class KBStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    INDEXING = "indexing"
    ERROR = "error"

class KBCategory(str, Enum):
    CRYPTO = "crypto"
    WEB3 = "web3"
    TECH = "tech"
    GAMING = "gaming"
    COMMUNITY = "community"
    EDUCATION = "education"
    BUSINESS = "business"
    OTHER = "other"

class KnowledgeBase(BaseModel):
    kb_index: str
    kb_id: str
    name: str
    description: Optional[str] = None
    icon: str = "📚"
    visibility: KBVisibility
    status: KBStatus
    categories: List[KBCategory] = []
    tags: List[str] = []
    owner_id: int
    source_type: str  # "group", "user", "topic"
    source_id: int
    stats: dict
    featured: bool = False
    verified: bool = False
    quality_score: float = 0.0
    created_at: datetime
    updated_at: datetime
```

---

## Authentication Models

### AuthRequest

```python
class TelegramMiniAppAuthRequest(BaseModel):
    initData: str  # Signed data from Telegram

class GuestSessionResponse(BaseModel):
    token: str
    token_type: str = "guest"
    expires_in: int = 3600
    message: str
    upgrade_url: str
    permissions: List[str]

class AuthResponse(BaseModel):
    jwt_token: str
    expires_in: int = 3600
    user: dict
```

---

## WebSocket Event Models

### Base Event

```python
class BaseEvent(BaseModel):
    type: str
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None
```

### Client → Server Events

```python
class UserMessage(BaseEvent):
    type: str = "user_message"
    message: str
    thread_id: Optional[str] = None
    metadata: Optional[dict] = None

class CommandRequest(BaseEvent):
    type: str = "command"
    command: str
    args: Optional[dict] = None

class FormSubmission(BaseEvent):
    type: str = "form_submit"
    form_id: str
    values: dict
    action: Optional[str] = None

class SearchRequest(BaseEvent):
    type: str = "search_kb"
    query: str
    kb_ids: List[str] = []
    max_results: int = 10
    search_method: str = "text"
```

### Server → Client Events

```python
class TextStreamDelta(BaseEvent):
    type: str = "textStreamDelta"
    delta: str
    message_id: str
    metadata: Optional[dict] = None

class ToolInvocation(BaseEvent):
    type: str = "toolInvocation"
    tool_id: str
    tool_name: str
    args: dict
    emoji: Optional[str] = None

class ToolResult(BaseEvent):
    type: str = "toolResult"
    tool_id: str
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None

class FormRequest(BaseEvent):
    type: str = "formRequest"
    form_id: str
    title: str
    description: Optional[str] = None
    fields: List[dict]

class StateUpdate(BaseEvent):
    type: str = "stateUpdate"
    status: str  # generating, waiting, complete, error
    thread_id: Optional[str] = None
    metadata: Optional[dict] = None

class ErrorEvent(BaseEvent):
    type: str = "error"
    code: str
    message: str
    details: Optional[dict] = None
    severity: str = "error"
    recoverable: bool = False
```

---

## Form Models

### FormField

```python
class FormFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    FILE = "file"
    BUTTON = "button"
    SELECT = "select"
    CHECKBOX = "checkbox"

class FormField(BaseModel):
    type: FormFieldType
    name: str
    label: str
    value: Optional[Any] = None
    required: bool = False
    readonly: bool = False
    placeholder: Optional[str] = None
    accept: Optional[str] = None  # For file uploads
    maxSize: Optional[int] = None  # For file uploads
    variant: Optional[str] = None  # For buttons

class FormData(BaseModel):
    form_id: str
    title: str
    description: Optional[str] = None
    fields: List[FormField]
    process_info: Optional[dict] = None
```

---

## Profile Models

```python
class UserProfile(BaseModel):
    user_id: int
    telegram_user_id: int
    username: Optional[str] = None
    first_name: str
    language: str = "en"
    created_at: datetime
    stats: dict
    settings: dict
    active_processes: List[dict] = []

class ProfileSettings(BaseModel):
    language: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    streaming_enabled: Optional[bool] = None
```

---

## File Upload Models

```python
class FileUploadResponse(BaseModel):
    file_url: str
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: datetime
```

---

## Error Models

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## Command Models

```python
class CommandConfig(BaseModel):
    command: str
    workflow_key: Optional[str] = None
    auto_execute: bool = False
    description: str
    requires_auth: bool = True
    show_in_menu: bool = True
    parameters: List[dict] = []
```

---

**Document Version:** 1.0  
**Last Updated:** October 18, 2025
