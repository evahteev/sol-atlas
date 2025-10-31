"""
Shared UI event builders for AG-UI clients.

Generates `uiContext` and `taskList` events so both the HTTP agent
endpoint and WebSocket handlers can stay in sync with the current
Telegram UX (menus, quick prompts, task drawers).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from ag_ui_gateway.adapters.task_adapter import get_task_adapter
from luka_bot.core.config import settings
from luka_bot.services.prompt_pool_service import PromptOption, get_prompt_pool_service
from luka_bot.services.user_kb_scope_service import (
    UserKBScope,
    get_user_kb_scope_service,
)
from luka_bot.services.user_profile_service import get_user_profile_service
from luka_bot.services.group_service import get_group_service
from luka_bot.utils.i18n_helper import _, get_user_language

PROMPT_LIMIT = 3
PROMPT_TRUNCATE_AT = 40

MODE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "start": {"requires_auth": False, "show_in_menu": True, "label_key": "section.start"},
    "chat": {"requires_auth": False, "show_in_menu": True, "label_key": "section.chat"},
    "tasks": {"requires_auth": True, "show_in_menu": True, "label_key": "section.tasks"},
    "profile": {"requires_auth": True, "show_in_menu": True, "label_key": "section.profile"},
    "groups": {"requires_auth": True, "show_in_menu": True, "label_key": "section.groups"},
}

SCOPE_CONTROL_DEFINITIONS = [
    {"id": "edit_groups", "label_key": "kb_scope_edit_groups_button"},
    {"id": "all_sources", "label_key": "kb_scope_all_sources_button"},
    {"id": "my_groups", "label_key": "kb_scope_user_groups_button"},
]


async def build_ui_context_event(
    user_id: Optional[int],
    active_mode: str,
    is_guest: bool,
) -> Optional[Dict[str, Any]]:
    """
    Build uiContext event mirroring Telegram reply keyboards.

    Args:
        user_id: Numeric telegram user id (0/None for guests)
        active_mode: Currently active mode (start/chat/tasks/profile/groups)
        is_guest: Whether the viewer is an unauthenticated guest

    Returns:
        Event dict or None if generation fails.
    """
    try:
        language = await _get_language(user_id)

        profile_display_name = "Guest"
        if user_id and user_id > 0:
            try:
                profile_service = get_user_profile_service()
                profile = await profile_service.get_profile(user_id)
                if profile:
                    profile_display_name = (
                        profile.first_name
                        or profile.username
                        or profile.full_name
                        or str(user_id)
                    )
                else:
                    profile_display_name = str(user_id)
            except Exception as profile_error:
                logger.debug(f"Using fallback display name: {profile_error}")
                profile_display_name = str(user_id)

        group_names: List[str] = []
        group_ids: List[str] = []
        group_count = 0

        if user_id and user_id > 0:
            try:
                group_service = await get_group_service()
                links = await group_service.list_user_groups(user_id, active_only=True)
                group_count = len(links)

                for link in links:
                    group_ids.append(str(link.group_id))
                    if len(group_names) >= PROMPT_LIMIT * 2:
                        continue
                    try:
                        metadata = await group_service.get_cached_group_metadata(link.group_id)
                        if metadata and metadata.group_title:
                            group_names.append(metadata.group_title)
                        else:
                            group_names.append(f"Group {link.group_id}")
                    except Exception as metadata_error:
                        logger.debug(
                            f"Failed to load metadata for group {link.group_id}: {metadata_error}"
                        )
                        group_names.append(f"Group {link.group_id}")
            except Exception as group_error:
                logger.warning(f"Failed to load group info for uiContext: {group_error}")

        prompts = await _get_quick_prompts(language=language, group_names=group_names)
        scope_controls, scope_metadata = await _build_scope_controls(
            user_id=user_id,
            language=language,
            available_group_ids=group_ids,
        )
        task_count = await _get_task_count(user_id)

        modes_payload = _build_modes_payload(
            language=language,
            task_count=task_count,
            is_guest=is_guest,
        )

        event: Dict[str, Any] = {
            "type": "uiContext",
            "contextId": str(uuid.uuid4()),
            "timestamp": int(time.time() * 1000),
            "activeMode": active_mode if active_mode in MODE_DEFINITIONS else "chat",
            "modes": modes_payload,
            "quickPrompts": prompts,
            "scopeControls": scope_controls,
            "userInfo": {
                "userId": str(user_id) if user_id is not None else None,
                "displayName": profile_display_name,
                "language": language,
                "isGuest": is_guest,
            },
            "metadata": {
                "groupCount": group_count,
                "taskCount": task_count,
                "scope": scope_metadata,
            },
        }
        return event
    except Exception as error:
        logger.error(f"Failed to build uiContext event: {error}")
        return None


async def build_task_list_event(
    user_id: Optional[int],
    *,
    tasks: Optional[List[Dict[str, Any]]] = None,
    language: Optional[str] = None,
    selected_task_id: Optional[str] = None,
    source: str = "chatbot_start",
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Build taskList event representing Camunda tasks.

    Args:
        user_id: Numeric telegram user id (0/None for guests)
        tasks: Optional prefetched tasks (list of dicts)
        language: Optional language override
        selected_task_id: Task to highlight
        source: Logical source identifier
        force: Emit event even if there are no tasks

    Returns:
        Event dict or None when no data should be emitted.
    """
    if not user_id or user_id <= 0:
        if not force:
            return None

    try:
        lang = language or await _get_language(user_id)
        task_adapter = get_task_adapter()

        task_items = tasks
        if task_items is None and user_id:
            task_items = await task_adapter.get_user_tasks(user_id)
        task_items = task_items or []

        if not task_items and not force:
            return None

        formatted_tasks = [_format_task_item(item) for item in task_items]

        event: Dict[str, Any] = {
            "type": "taskList",
            "timestamp": int(time.time() * 1000),
            "source": source,
            "tasks": formatted_tasks,
            "pagination": {
                "limit": len(formatted_tasks),
                "offset": 0,
                "total": len(formatted_tasks),
            },
            "traceId": uuid.uuid4().hex,
        }

        if selected_task_id:
            event["selectedTaskId"] = selected_task_id

        if formatted_tasks:
            event["metadata"] = {
                "taskCount": len(formatted_tasks),
            }
        else:
            event["emptyState"] = {
                "title": _strip_markup(_("start.tasks_menu_title", lang)),
                "message": _strip_markup(_("start.no_tasks_info", lang)),
            }

        return event
    except Exception as error:
        logger.error(f"Failed to build taskList event: {error}")
        return None


async def _get_language(user_id: Optional[int]) -> str:
    if user_id and user_id > 0:
        try:
            return await get_user_language(user_id)
        except Exception as language_error:
            logger.debug(f"Falling back to default locale: {language_error}")
    return settings.DEFAULT_LOCALE


async def _get_task_count(user_id: Optional[int]) -> int:
    if not user_id or user_id <= 0:
        return 0

    try:
        adapter = get_task_adapter()
        tasks = await adapter.get_user_tasks(user_id)
        return len(tasks)
    except Exception as task_error:
        logger.debug(f"Failed to load task count for uiContext: {task_error}")
        return 0


async def _build_scope_controls(
    user_id: Optional[int],
    language: str,
    available_group_ids: List[str],
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    scope_service = get_user_kb_scope_service()
    scope: Optional[UserKBScope] = None

    if user_id and user_id > 0:
        try:
            scope = await scope_service.refresh_scope_from_groups(
                user_id=user_id,
                available_group_ids=available_group_ids,
            )
        except Exception as scope_error:
            logger.debug(f"Failed to refresh KB scope: {scope_error}")

    scope_source = scope.source if scope else "all"
    selected_map = {
        "all": "all_sources",
        "auto_groups": "my_groups",
        "custom": None,
    }
    selected_id = selected_map.get(scope_source)

    controls: List[Dict[str, Any]] = []
    for definition in SCOPE_CONTROL_DEFINITIONS:
        label = _(definition["label_key"], language)
        emoji = label.split(" ", 1)[0] if " " in label else ""
        controls.append(
            {
                "id": definition["id"],
                "label": _strip_markup(label),
                "emoji": emoji,
                "selected": definition["id"] == selected_id,
            }
        )

    metadata = {
        "source": scope_source,
        "groupIds": scope.group_ids if scope else [],
    }

    return controls, metadata


async def _get_quick_prompts(language: str, group_names: List[str]) -> List[Dict[str, Any]]:
    try:
        prompt_service = get_prompt_pool_service()
        prompt_options = await prompt_service.get_quick_prompts(
            locale=language,
            group_names=group_names,
            count=PROMPT_LIMIT,
        )
    except Exception as prompt_error:
        logger.warning(f"Failed to load quick prompts: {prompt_error}")
        prompt_options = []

    prompts: List[Dict[str, Any]] = []
    for option in prompt_options:
        if not isinstance(option, PromptOption):
            continue
        text = option.text.strip()
        prompts.append(
            {
                "id": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
                "text": _truncate_prompt(text),
                "source": option.source,
            }
        )
    return prompts


def _build_modes_payload(language: str, task_count: int, is_guest: bool) -> List[Dict[str, Any]]:
    modes: List[Dict[str, Any]] = []
    for mode_id, definition in MODE_DEFINITIONS.items():
        label_key = definition.get("label_key", f"section.{mode_id}")
        label_value = _(label_key, language)
        emoji = ""
        if " " in label_value:
            emoji = label_value.split(" ", 1)[0]

        payload: Dict[str, Any] = {
            "id": mode_id,
            "label": _strip_markup(label_value),
            "emoji": emoji,
            "requiresAuth": definition.get("requires_auth", False),
            "showInMenu": definition.get("show_in_menu", True),
        }

        if mode_id == "tasks":
            payload["badgeCount"] = task_count

        if is_guest and definition.get("requires_auth"):
            payload["disabled"] = True

        modes.append(payload)
    return modes


def _truncate_prompt(text: str) -> str:
    if len(text) <= PROMPT_TRUNCATE_AT:
        return text
    return text[: PROMPT_TRUNCATE_AT - 3] + "..."


def _strip_markup(value: str) -> str:
    return value.replace("<b>", "").replace("</b>", "")


def _format_task_item(task: Dict[str, Any]) -> Dict[str, Any]:
    task_id = str(task.get("id") or "")
    name = task.get("name") or f"Task {task_id[:8]}"
    truncated_name = name if len(name) <= 18 else name[:15] + "..."

    created_at = _iso_to_timestamp(task.get("created"))
    due_at = _iso_to_timestamp(task.get("due"))

    return {
        "id": task_id,
        "name": truncated_name,
        "status": "pending",
        "createdAt": created_at,
        "dueAt": due_at,
        "metadata": {
            "processInstanceId": task.get("process_instance_id"),
            "description": task.get("description"),
            "assignee": task.get("assignee"),
        },
    }


def _iso_to_timestamp(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None

