"""Manage per-user knowledge base scope preferences."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import orjson
from loguru import logger

from luka_bot.core.loader import redis_client


SCOPE_KEY_PREFIX = "luka_kb_scope:"
SCOPE_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days


@dataclass(slots=True)
class UserKBScope:
    source: str  # "all", "auto_groups", "custom"
    group_ids: List[str] = field(default_factory=list)
    updated_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "group_ids": self.group_ids,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserKBScope":
        return cls(
            source=data.get("source", "all"),
            group_ids=list(data.get("group_ids", []) or []),
            updated_at=float(data.get("updated_at", time.time())),
        )


class UserKBScopeService:
    """Persist and retrieve knowledge base scopes per user."""

    def __init__(self, ttl_seconds: int = SCOPE_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds

    def _key(self, user_id: int) -> str:
        return f"{SCOPE_KEY_PREFIX}{user_id}"

    async def get_scope(self, user_id: int) -> Optional[UserKBScope]:
        try:
            raw = await redis_client.get(self._key(user_id))
            if not raw:
                return None
            data = orjson.loads(raw)
            return UserKBScope.from_dict(data)
        except Exception as exc:
            logger.warning(f"Failed to load KB scope for user {user_id}: {exc}")
            return None

    async def set_scope(self, user_id: int, scope: UserKBScope) -> UserKBScope:
        try:
            await redis_client.setex(
                name=self._key(user_id),
                time=self.ttl_seconds,
                value=orjson.dumps(scope.to_dict()),
            )
            return scope
        except Exception as exc:
            logger.warning(f"Failed to persist KB scope for user {user_id}: {exc}")
            return scope

    async def clear_scope(self, user_id: int) -> None:
        try:
            await redis_client.delete(self._key(user_id))
        except Exception as exc:
            logger.warning(f"Failed to clear KB scope for user {user_id}: {exc}")

    async def refresh_scope_from_groups(
        self,
        user_id: int,
        available_group_ids: List[str],
        force: bool = False,
    ) -> UserKBScope:
        """Ensure scope matches current groups unless a custom scope is active."""

        available_group_ids = list(dict.fromkeys(filter(None, available_group_ids)))
        current = await self.get_scope(user_id)

        if current and current.source == "custom" and not force:
            # Prune removed groups while keeping custom choice
            filtered = [gid for gid in current.group_ids if gid in available_group_ids]
            if filtered != current.group_ids:
                current.group_ids = filtered
                current.updated_at = time.time()
                await self.set_scope(user_id, current)
            return current

        if available_group_ids:
            scope = UserKBScope(source="auto_groups", group_ids=available_group_ids, updated_at=time.time())
        else:
            scope = UserKBScope(source="all", group_ids=[], updated_at=time.time())

        return await self.set_scope(user_id, scope)

    async def set_custom_scope(self, user_id: int, group_ids: List[str]) -> UserKBScope:
        cleaned = list(dict.fromkeys(filter(None, group_ids)))
        if not cleaned:
            scope = UserKBScope(source="all", group_ids=[], updated_at=time.time())
        else:
            scope = UserKBScope(source="custom", group_ids=cleaned, updated_at=time.time())
        return await self.set_scope(user_id, scope)


def get_user_kb_scope_service() -> UserKBScopeService:
    """Convenience accessor when not using service locator."""
    return UserKBScopeService()
