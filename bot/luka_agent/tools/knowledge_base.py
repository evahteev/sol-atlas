"""
Knowledge Base search tool for luka_agent.

Provides text-based search over user's personal KB (indexed messages).
"""

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field


class SearchKnowledgeBaseInput(BaseModel):
    """Input schema for knowledge base search tool."""

    query: str = Field(
        ...,
        description=(
            "Search query. Use '*' for ALL messages in time period (digests), "
            "or keywords for specific topics like 'postgres issues'"
        ),
    )
    from_user: str | None = Field(
        None, description="Filter by sender name (optional)"
    )
    date_from: str | None = Field(
        None,
        description=(
            "Start date: '7d' (days), '1w' (weeks), '1m' (months), '1y' (years), "
            "or 'YYYY-MM-DD'. Leave empty to search all history."
        ),
    )
    date_to: str | None = Field(
        None, description="End date in 'YYYY-MM-DD' format. Leave empty for current time."
    )
    max_results: int = Field(
        5, description="Maximum results (1-20, use 20+ for digests)", ge=1, le=100
    )


async def search_knowledge_base_impl(
    query: str,
    from_user: str | None,
    date_from: str | None,
    date_to: str | None,
    max_results: int,
    user_id: int,
    thread_id: str,
    language: str,
    knowledge_bases: list[str],
) -> str:
    """Search user's knowledge base for relevant information.

    Args:
        query: Search query
        from_user: Filter by sender name
        date_from: Start date filter
        date_to: End date filter
        max_results: Maximum results
        user_id: User ID for context
        thread_id: Thread ID for context
        language: User's language
        knowledge_bases: List of KB indices to search

    Returns:
        Formatted search results or error message
    """
    try:
        from luka_bot.services import get_elasticsearch_service, get_user_profile_service
        from luka_bot.core.config import settings

        # Check if Elasticsearch is enabled
        if not settings.ELASTICSEARCH_ENABLED:
            logger.warning("Elasticsearch is disabled in settings")
            return "Knowledge base is currently disabled."

        es_service = await get_elasticsearch_service()
        profile_service = get_user_profile_service()

        # Determine KB index to search
        kb_index = knowledge_bases[0] if knowledge_bases else f"tg-kb-user-{user_id}"

        logger.info(f"🔍 Searching KB '{kb_index}' for query: {query[:100]}...")

        # Search Elasticsearch using text search
        results = await es_service.search_messages_text(
            index_name=kb_index,
            query_text=query,
            max_results=max_results or 5,
        )

        if not results or len(results) == 0:
            logger.info(f"ℹ️ No results found in KB '{kb_index}' for query: {query[:50]}")
            return f"No relevant information found in your knowledge base for: {query}"

        # Format results with context
        formatted_results = []
        for i, result in enumerate(results[:max_results or 5], 1):
            doc = result.get("doc", {})
            text = doc.get("message_text", "")
            score = result.get("score", 0)
            date = doc.get("message_date", "")
            from_name = doc.get("sender_name", doc.get("from_user", ""))

            # Build result entry
            entry_parts = [f"{i}. {text[:300]}"]
            if from_name:
                entry_parts.append(f"   (from: {from_name})")
            if date:
                entry_parts.append(f"   (date: {date})")
            entry_parts.append(f"   (relevance: {score:.2f})")

            formatted_results.append("\n".join(entry_parts))

        result_text = "\n\n".join(formatted_results)
        logger.info(f"✅ Found {len(results)} KB results, returning top {len(formatted_results)}")

        return f"Found {len(results)} results in knowledge base:\n\n{result_text}"

    except Exception as e:
        logger.error(f"❌ Error in search_knowledge_base: {e}", exc_info=True)
        return f"Error searching knowledge base: {str(e)}"


def create_knowledge_base_tool(
    user_id: int,
    thread_id: str,
    language: str,
    knowledge_bases: list[str],
) -> StructuredTool:
    """Create knowledge base search tool with user context.

    Args:
        user_id: User ID for access control
        thread_id: Thread ID for context
        language: User's language
        knowledge_bases: List of KB indices user can access

    Returns:
        LangChain StructuredTool for KB search
    """
    return StructuredTool.from_function(
        name="search_knowledge_base",
        description=(
            "Search the user's knowledge base (message history) for relevant information. "
            "Use this when the user asks about past conversations, stored documents, "
            "or specific information that might be in their personal knowledge base. "
            "Supports time-based filters and user filters. "
            "Use query='*' for digests/summaries of all messages in a time period."
        ),
        func=lambda query, from_user=None, date_from=None, date_to=None, max_results=5: search_knowledge_base_impl(
            query=query,
            from_user=from_user,
            date_from=date_from,
            date_to=date_to,
            max_results=max_results,
            user_id=user_id,
            thread_id=thread_id,
            language=language,
            knowledge_bases=knowledge_bases,
        ),
        args_schema=SearchKnowledgeBaseInput,
        coroutine=lambda query, from_user=None, date_from=None, date_to=None, max_results=5: search_knowledge_base_impl(
            query=query,
            from_user=from_user,
            date_from=date_from,
            date_to=date_to,
            max_results=max_results,
            user_id=user_id,
            thread_id=thread_id,
            language=language,
            knowledge_bases=knowledge_bases,
        ),
    )


__all__ = ["create_knowledge_base_tool"]
