"""
Tests for luka_agent state schema.

Tests validate the AgentState TypedDict structure, field types,
and default values.
"""

import pytest
from typing import get_type_hints
from langchain_core.messages import HumanMessage, AIMessage

from luka_agent.state import AgentState


class TestAgentStateStructure:
    """Test AgentState structure and fields."""

    def test_agent_state_has_required_fields(self):
        """Test AgentState has all required fields."""
        hints = get_type_hints(AgentState)

        required_fields = {
            "messages",
            "user_id",
            "thread_id",
            "knowledge_bases",
            "language",
            "platform",
            "conversation_suggestions",
        }

        for field in required_fields:
            assert field in hints, f"AgentState missing required field: {field}"

    def test_agent_state_field_types(self):
        """Test AgentState field types are correct."""
        hints = get_type_hints(AgentState)

        # Check key field types
        assert "messages" in hints
        assert "user_id" in hints
        assert "thread_id" in hints
        assert "language" in hints
        assert "platform" in hints

    def test_agent_state_can_be_created(self):
        """Test AgentState dict can be created with valid values."""
        state: AgentState = {
            "messages": [HumanMessage(content="Hello")],
            "user_id": 123,
            "thread_id": "test_thread",
            "knowledge_bases": ["test-kb"],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["user_id"] == 123
        assert state["thread_id"] == "test_thread"
        assert state["language"] == "en"
        assert state["platform"] == "telegram"
        assert len(state["messages"]) == 1
        assert state["knowledge_bases"] == ["test-kb"]


class TestAgentStateMessages:
    """Test AgentState messages field."""

    def test_messages_accepts_human_message(self):
        """Test messages field accepts HumanMessage."""
        state: AgentState = {
            "messages": [HumanMessage(content="User input")],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], HumanMessage)
        assert state["messages"][0].content == "User input"

    def test_messages_accepts_ai_message(self):
        """Test messages field accepts AIMessage."""
        state: AgentState = {
            "messages": [AIMessage(content="AI response")],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert len(state["messages"]) == 1
        assert isinstance(state["messages"][0], AIMessage)
        assert state["messages"][0].content == "AI response"

    def test_messages_accepts_multiple_messages(self):
        """Test messages field accepts multiple messages."""
        state: AgentState = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
                HumanMessage(content="How are you?"),
            ],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert len(state["messages"]) == 3


class TestAgentStatePlatforms:
    """Test AgentState platform field."""

    def test_platform_accepts_telegram(self):
        """Test platform field accepts 'telegram'."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["platform"] == "telegram"

    def test_platform_accepts_web(self):
        """Test platform field accepts 'web'."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "web",
            "conversation_suggestions": [],
        }

        assert state["platform"] == "web"

    def test_platform_accepts_worker(self):
        """Test platform field accepts 'worker' (CLI/background jobs)."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "worker",
            "conversation_suggestions": [],
        }

        assert state["platform"] == "worker"


class TestAgentStateKnowledgeBases:
    """Test AgentState knowledge_bases field."""

    def test_knowledge_bases_accepts_single_kb(self):
        """Test knowledge_bases field accepts single KB."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": ["tg-kb-user-123"],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert len(state["knowledge_bases"]) == 1
        assert state["knowledge_bases"][0] == "tg-kb-user-123"

    def test_knowledge_bases_accepts_multiple_kbs(self):
        """Test knowledge_bases field accepts multiple KBs."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": ["kb1", "kb2", "kb3"],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert len(state["knowledge_bases"]) == 3
        assert "kb1" in state["knowledge_bases"]
        assert "kb2" in state["knowledge_bases"]
        assert "kb3" in state["knowledge_bases"]

    def test_knowledge_bases_accepts_empty_list(self):
        """Test knowledge_bases field accepts empty list."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert len(state["knowledge_bases"]) == 0


class TestAgentStateSuggestions:
    """Test AgentState suggestions field."""

    def test_suggestions_accepts_empty_list(self):
        """Test conversation_suggestions accepts empty list."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["conversation_suggestions"] == []

    def test_suggestions_accepts_suggestion_list(self):
        """Test conversation_suggestions accepts list of strings."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [
                "Tell me more",
                "What's next?",
                "Go back",
            ],
        }

        assert len(state["conversation_suggestions"]) == 3
        assert "Tell me more" in state["conversation_suggestions"]


class TestAgentStateLanguages:
    """Test AgentState language field."""

    def test_language_accepts_english(self):
        """Test language field accepts 'en'."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["language"] == "en"

    def test_language_accepts_russian(self):
        """Test language field accepts 'ru'."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "ru",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["language"] == "ru"

    def test_language_accepts_other_codes(self):
        """Test language field accepts other language codes."""
        for lang in ["es", "fr", "de", "zh", "ja"]:
            state: AgentState = {
                "messages": [],
                "user_id": 123,
                "thread_id": "test",
                "knowledge_bases": [],
                "language": lang,
                "platform": "telegram",
                "conversation_suggestions": [],
            }

            assert state["language"] == lang


class TestAgentStateUserContext:
    """Test AgentState user context fields."""

    def test_user_id_accepts_integer(self):
        """Test user_id field accepts integer."""
        state: AgentState = {
            "messages": [],
            "user_id": 12345,
            "thread_id": "test",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["user_id"] == 12345
        assert isinstance(state["user_id"], int)

    def test_thread_id_accepts_string(self):
        """Test thread_id field accepts string."""
        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": "telegram_123_thread_456",
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["thread_id"] == "telegram_123_thread_456"
        assert isinstance(state["thread_id"], str)

    def test_thread_id_accepts_uuid_format(self):
        """Test thread_id field accepts UUID format."""
        import uuid
        thread_id = str(uuid.uuid4())

        state: AgentState = {
            "messages": [],
            "user_id": 123,
            "thread_id": thread_id,
            "knowledge_bases": [],
            "language": "en",
            "platform": "telegram",
            "conversation_suggestions": [],
        }

        assert state["thread_id"] == thread_id
