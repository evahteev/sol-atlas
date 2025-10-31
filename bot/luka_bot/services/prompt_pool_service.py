"""Service for serving localized quick-prompt suggestions on /start."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from importlib import resources
from typing import Any, Dict, List

from loguru import logger

PROMPT_PACKAGE = "luka_bot.locales.prompt_pools"
DEFAULT_LOCALE = "en"


@dataclass(slots=True)
class PromptOption:
    """Represents a single quick prompt choice."""

    text: str
    source: str  # "group" or "generic"
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptPoolService:
    """Loads and serves localized prompt pools."""

    def __init__(self) -> None:
        self._catalog_cache: Dict[str, Dict[str, List[str]]] = {}

    async def get_quick_prompts(
        self,
        locale: str | None,
        group_names: List[str] | None = None,
        count: int = 3,
    ) -> List[PromptOption]:
        """
        Return up to `count` quick prompts tailored to the locale and groups.

        Preference:
            1. Fill with group-aware prompts when group names exist.
            2. Fill remaining slots with generic prompts.
        """
        normalized_locale = self._normalize_locale(locale)
        catalog = self._load_catalog(normalized_locale)
        if not catalog:
            logger.warning(f"No prompt catalog for locale={normalized_locale}, using fallback.")
            catalog = self._load_catalog(DEFAULT_LOCALE) or {"group_prompts": [], "generic_prompts": []}

        selected: List[PromptOption] = []
        available_group_prompts = catalog.get("group_prompts", [])
        available_generic_prompts = catalog.get("generic_prompts", [])

        group_names = group_names or []
        random.shuffle(group_names)

        # Choose group-aware prompts first
        if group_names and available_group_prompts:
            group_prompt_templates = available_group_prompts.copy()
            random.shuffle(group_prompt_templates)

            for template, group_name in zip(group_prompt_templates, self._cycle_list(group_names, count)):
                try:
                    text = template.format(group_name=group_name)
                except Exception as exc:  # defensive: badly formatted template
                    logger.warning(f"Failed to render group prompt '{template}': {exc}")
                    continue

                selected.append(PromptOption(text=text, source="group", metadata={"group_name": group_name}))
                if len(selected) >= count:
                    break

        if len(selected) < count and available_generic_prompts:
            generic_candidates = available_generic_prompts.copy()
            random.shuffle(generic_candidates)

            for template in generic_candidates:
                if len(selected) >= count:
                    break
                selected.append(PromptOption(text=template, source="generic"))

        # If still not enough prompts (unlikely), deduplicate and trim
        unique_prompts: Dict[str, PromptOption] = {}
        for option in selected:
            if option.text not in unique_prompts:
                unique_prompts[option.text] = option

        final_prompts = list(unique_prompts.values())[:count]

        logger.debug(
            "PromptPoolService returning %d prompts (locale=%s, groups=%d)",
            len(final_prompts),
            normalized_locale,
            len(group_names),
        )
        return final_prompts

    def _normalize_locale(self, locale: str | None) -> str:
        if not locale:
            return DEFAULT_LOCALE
        normalized = locale.split("-")[0].lower()
        if normalized in self._catalog_cache or self._has_catalog(normalized):
            return normalized
        return DEFAULT_LOCALE

    def _has_catalog(self, locale: str) -> bool:
        try:
            resources.files(PROMPT_PACKAGE).joinpath(f"{locale}.json")
            return True
        except FileNotFoundError:
            return False

    def _load_catalog(self, locale: str) -> Dict[str, List[str]] | None:
        if locale in self._catalog_cache:
            return self._catalog_cache[locale]

        try:
            with resources.files(PROMPT_PACKAGE).joinpath(f"{locale}.json").open("r", encoding="utf-8") as fp:
                catalog = json.load(fp)
                # Ensure expected keys exist
                catalog.setdefault("group_prompts", [])
                catalog.setdefault("generic_prompts", [])
                self._catalog_cache[locale] = catalog
                return catalog
        except FileNotFoundError:
            logger.warning(f"Prompt catalog not found for locale '{locale}'")
        except Exception as exc:
            logger.error(f"Failed to load prompt catalog for locale '{locale}': {exc}")
        return None

    def _cycle_list(self, items: List[str], target_count: int) -> List[str]:
        """Return a repeated list to cover the desired number of prompts."""
        if not items:
            return []
        # Repeat list enough times to cover desired count and shuffle for variety
        multiplier = max(1, (target_count // len(items)) + 1)
        repeated = items * multiplier
        random.shuffle(repeated)
        return repeated


def get_prompt_pool_service() -> PromptPoolService:
    """Convenience accessor when not using service locator."""
    return PromptPoolService()
