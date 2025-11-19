"""
Tests for LLM configuration priority system.

Tests verify that LLM settings are correctly resolved using the priority:
1. Runtime parameters (highest)
2. Environment variables
3. Hardcoded defaults (lowest)
"""

import os
import pytest
from unittest.mock import patch

from luka_agent.state import create_initial_state


class TestLLMConfigPriority:
    """Test LLM configuration priority system."""

    def test_uses_hardcoded_defaults_when_no_env_or_runtime(self):
        """When no env vars or runtime params, should use hardcoded defaults."""
        with patch.dict(os.environ, {}, clear=True):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
            )

            assert state["llm_provider"] == "ollama"  # Hardcoded default
            assert state["llm_model"] == "llama3.2"  # Hardcoded default
            assert state["llm_temperature"] == 0.7
            assert state["llm_max_tokens"] == 2000
            assert state["llm_streaming"] is True

    def test_env_vars_override_hardcoded_defaults(self):
        """Environment variables should override hardcoded defaults."""
        with patch.dict(
            os.environ,
            {
                "DEFAULT_LLM_PROVIDER": "openai",
                "DEFAULT_LLM_MODEL": "gpt-4o",
                "DEFAULT_LLM_TEMPERATURE": "0.5",
                "DEFAULT_LLM_MAX_TOKENS": "3000",
                "DEFAULT_LLM_STREAMING": "false",
            },
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
            )

            assert state["llm_provider"] == "openai"  # From env
            assert state["llm_model"] == "gpt-4o"  # From env
            assert state["llm_temperature"] == 0.5  # From env
            assert state["llm_max_tokens"] == 3000  # From env
            assert state["llm_streaming"] is False  # From env

    def test_runtime_params_override_env_vars(self):
        """Runtime parameters should override both env vars and defaults."""
        with patch.dict(
            os.environ,
            {
                "DEFAULT_LLM_PROVIDER": "ollama",
                "DEFAULT_LLM_MODEL": "llama3.2",
            },
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="web",
                llm_provider="anthropic",  # Runtime override
                llm_model="claude-sonnet-4",  # Runtime override
                llm_temperature=0.3,  # Runtime override
            )

            assert state["llm_provider"] == "anthropic"  # Runtime wins
            assert state["llm_model"] == "claude-sonnet-4"  # Runtime wins
            assert state["llm_temperature"] == 0.3  # Runtime wins

    def test_partial_runtime_override(self):
        """Can override some params while using env for others."""
        with patch.dict(
            os.environ,
            {
                "DEFAULT_LLM_PROVIDER": "ollama",
                "DEFAULT_LLM_MODEL": "llama3.2",
                "DEFAULT_LLM_TEMPERATURE": "0.7",
            },
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="telegram",
                llm_model="gpt-4o-mini",  # Only override model
            )

            assert state["llm_provider"] == "ollama"  # From env
            assert state["llm_model"] == "gpt-4o-mini"  # Runtime override
            assert state["llm_temperature"] == 0.7  # From env

    def test_streaming_boolean_parsing(self):
        """Test that streaming env var is correctly parsed as boolean."""
        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_STREAMING": "true"},
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
            )
            assert state["llm_streaming"] is True

        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_STREAMING": "false"},
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
            )
            assert state["llm_streaming"] is False

    def test_temperature_float_parsing(self):
        """Test that temperature env var is parsed as float."""
        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_TEMPERATURE": "0.42"},
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
            )
            assert isinstance(state["llm_temperature"], float)
            assert state["llm_temperature"] == 0.42

    def test_max_tokens_int_parsing(self):
        """Test that max_tokens env var is parsed as int."""
        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_MAX_TOKENS": "4096"},
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
            )
            assert isinstance(state["llm_max_tokens"], int)
            assert state["llm_max_tokens"] == 4096


class TestLLMConfigUseCases:
    """Test real-world LLM configuration use cases."""

    def test_cli_worker_platform_uses_env_defaults(self):
        """CLI/worker platform uses env vars without runtime overrides."""
        with patch.dict(
            os.environ,
            {
                "DEFAULT_LLM_PROVIDER": "ollama",
                "DEFAULT_LLM_MODEL": "gpt-oss",
            },
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=12345,
                thread_id="cli_thread",
                platform="worker",  # CLI platform
                # No runtime overrides
            )

            assert state["llm_provider"] == "ollama"
            assert state["llm_model"] == "gpt-oss"

    def test_web_platform_user_model_selection(self):
        """Web platform allows per-user model selection."""
        # User chose GPT-4o in web UI settings
        user_preferences = {
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "llm_temperature": 0.4,
        }

        state = create_initial_state(
            user_message="test",
            user_id=456,
            thread_id="web_thread",
            platform="web",
            **user_preferences,  # User's choice overrides defaults
        )

        assert state["llm_provider"] == "openai"
        assert state["llm_model"] == "gpt-4o"
        assert state["llm_temperature"] == 0.4

    def test_telegram_subscription_tiers(self):
        """Telegram platform supports different models per subscription tier."""
        # Premium user gets better model
        premium_state = create_initial_state(
            user_message="test",
            user_id=789,
            thread_id="tg_789",
            platform="telegram",
            llm_provider="anthropic",
            llm_model="claude-sonnet-4",
        )

        assert premium_state["llm_provider"] == "anthropic"
        assert premium_state["llm_model"] == "claude-sonnet-4"

        # Free user uses env defaults (local Ollama)
        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_PROVIDER": "ollama", "DEFAULT_LLM_MODEL": "llama3.2"},
            clear=True,
        ):
            free_state = create_initial_state(
                user_message="test",
                user_id=790,
                thread_id="tg_790",
                platform="telegram",
                # No overrides - free tier
            )

            assert free_state["llm_provider"] == "ollama"
            assert free_state["llm_model"] == "llama3.2"

    def test_cost_optimization_scenario(self):
        """Simple queries use cheap model, complex use expensive."""

        def get_optimal_llm(query: str):
            """Route based on query complexity."""
            if len(query) < 50:
                return None, None  # Use env defaults (cheap)
            else:
                return "openai", "gpt-4o"  # Use cloud (expensive)

        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_PROVIDER": "ollama", "DEFAULT_LLM_MODEL": "llama3.2"},
            clear=True,
        ):
            # Simple query
            simple_query = "Hello"
            provider, model = get_optimal_llm(simple_query)
            simple_state = create_initial_state(
                user_message=simple_query,
                user_id=123,
                thread_id="test",
                platform="web",
                llm_provider=provider,
                llm_model=model,
            )
            assert simple_state["llm_provider"] == "ollama"  # Cheap

            # Complex query
            complex_query = "Analyze the macroeconomic implications of the recent Federal Reserve policy changes"
            provider, model = get_optimal_llm(complex_query)
            complex_state = create_initial_state(
                user_message=complex_query,
                user_id=123,
                thread_id="test",
                platform="web",
                llm_provider=provider,
                llm_model=model,
            )
            assert complex_state["llm_provider"] == "openai"  # Expensive


class TestLLMConfigValidation:
    """Test LLM configuration validation and edge cases."""

    def test_none_values_use_fallback(self):
        """Explicit None values should fall through to next priority."""
        with patch.dict(
            os.environ,
            {"DEFAULT_LLM_PROVIDER": "openai"},
            clear=True,
        ):
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform="worker",
                llm_provider=None,  # Explicit None should use env
            )

            assert state["llm_provider"] == "openai"  # From env, not None

    def test_zero_temperature_is_respected(self):
        """Zero temperature should be valid (not treated as falsy)."""
        state = create_initial_state(
            user_message="test",
            user_id=123,
            thread_id="test",
            platform="worker",
            llm_temperature=0.0,  # Zero is valid!
        )

        assert state["llm_temperature"] == 0.0  # Should be exactly 0.0

    def test_false_streaming_is_respected(self):
        """False streaming should be valid (not use default True)."""
        state = create_initial_state(
            user_message="test",
            user_id=123,
            thread_id="test",
            platform="worker",
            llm_streaming=False,  # Explicitly disable
        )

        assert state["llm_streaming"] is False  # Should be False, not True


class TestLLMConfigBackwardCompatibility:
    """Test that LLM config changes don't break existing code."""

    def test_state_still_has_llm_fields(self):
        """State must still have all LLM-related fields."""
        state = create_initial_state(
            user_message="test",
            user_id=123,
            thread_id="test",
            platform="worker",
        )

        # All LLM fields must be present
        assert "llm_provider" in state
        assert "llm_model" in state
        assert "llm_temperature" in state
        assert "llm_max_tokens" in state
        assert "llm_streaming" in state

    def test_all_platforms_work(self):
        """All platform types should work with LLM config."""
        for platform in ["web", "telegram", "worker"]:
            state = create_initial_state(
                user_message="test",
                user_id=123,
                thread_id="test",
                platform=platform,
            )

            assert state["llm_provider"] is not None
            assert state["llm_model"] is not None
            assert state["platform"] == platform
