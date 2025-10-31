"""
Knowledge Base search tools for Luka bot.

Provides text-based search over user's personal KB (indexed messages).
Uses simple BM25 full-text search - works immediately without embeddings.
"""
from pydantic import Field
from typing import Optional
from loguru import logger
from pydantic_ai import RunContext  # FIX 33: Import RunContext for proper tool context
import hashlib
import json

from luka_bot.agents.context import ConversationContext
from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.core.config import settings
from luka_bot.utils.i18n_helper import _

# Simple in-memory cache for KB search results during a single conversation turn
# This prevents duplicate ES queries when pydantic-ai re-executes tools during get_output()
_kb_search_cache: dict[str, str] = {}


async def _process_large_result_set_batched(
    es_service,
    kb_index: str,
    must_clauses: list,
    total_count: int,
    user_lang: str,
    conv_ctx,
    batch_size: int = 30,
    max_batches: int = 5
) -> tuple[str, list]:
    """
    Process large result sets using batched approach with LLM summarization.
    
    Args:
        max_batches: Maximum number of batches to process (default: 5)
        
    Returns: (combined_summary, all_messages_for_samples)
    """
    max_messages = batch_size * max_batches
    logger.info(f"🔄 Starting batched processing: {total_count} messages in batches of {batch_size}")
    logger.info(f"  └─ Limit: max {max_batches} batches ({max_messages} messages)")
    
    all_messages = []
    batch_summaries = []
    search_after = None
    batch_num = 0
    
    # Fetch and summarize each batch
    while len(all_messages) < total_count and batch_num < max_batches:
        batch_num += 1
        logger.info(f"📦 Processing batch {batch_num}/{max_batches}...")
        
        # Build paginated query
        batch_query = {
            "query": {"bool": {"must": must_clauses}},
            "size": batch_size,
            "sort": [
                {"message_date": {"order": "desc"}}
            ]
        }
        
        if search_after:
            batch_query["search_after"] = search_after
        
        # Fetch batch
        response = await es_service.client.search(index=kb_index, body=batch_query)
        hits = response.get('hits', {}).get('hits', [])
        
        if not hits:
            break
        
        # Extract messages (use score or 1.0 if None/missing)
        batch_messages = [{'doc': hit['_source'], 'score': hit.get('_score') or 1.0} for hit in hits]
        all_messages.extend(batch_messages)
        
        # Get cursor for next batch
        search_after = hits[-1]['sort'] if hits else None
        
        # Summarize this batch with LLM
        logger.info(f"🤖 Summarizing batch {batch_num} ({len(batch_messages)} messages)...")
        batch_summary = await _summarize_message_batch(batch_messages, batch_num, user_lang, conv_ctx)
        batch_summaries.append(f"**Batch {batch_num}:**\n{batch_summary}")
        
        logger.info(f"✅ Batch {batch_num} complete ({len(all_messages)}/{total_count} messages processed)")
    
    # Log if we hit the limit
    if batch_num >= max_batches and len(all_messages) < total_count:
        logger.info(f"⚠️  Reached batch limit ({max_batches} batches, {len(all_messages)} messages). {total_count - len(all_messages)} messages not processed.")
    
    # Combine all batch summaries with final LLM call
    logger.info(f"🎯 Combining {len(batch_summaries)} batch summaries into final digest...")
    combined_summary = await _combine_batch_summaries(batch_summaries, user_lang, conv_ctx)
    
    logger.info(f"✅ Batched processing complete: {len(all_messages)} messages, {len(batch_summaries)} batches")
    
    return combined_summary, all_messages


async def _summarize_message_batch(messages: list, batch_num: int, user_lang: str, conv_ctx) -> str:
    """
    Use LLM to summarize a batch of messages.
    """
    try:
        # Format messages for LLM
        messages_text = "\n".join([
            f"{i+1}. [{msg['doc'].get('sender_name', 'Unknown')}, {msg['doc'].get('message_date', '')[:10]}]: {msg['doc'].get('message_text', '')[:200]}"
            for i, msg in enumerate(messages[:30])  # Max 30 per batch
        ])
        
        prompt = f"""Summarize this batch of messages (Batch {batch_num}):

{messages_text}

Provide a concise summary (max 100 words) covering:
1. Main topics discussed
2. Key points or decisions
3. Notable participants if relevant

Be factual and specific."""
        
        # Use Ollama to generate summary
        from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
        from pydantic_ai import Agent
        
        model = await create_llm_model_with_fallback(f"kb_batch_{batch_num}_{conv_ctx.user_id}")
        agent = Agent(
            model=model,
            system_prompt=f"You are a helpful assistant that summarizes conversations in {user_lang}. Be concise and factual."
        )
        
        result = await agent.run(prompt)
        return result.output.strip()
        
    except Exception as e:
        logger.warning(f"Failed to summarize batch {batch_num}: {e}")
        # Fallback: return simple text summary
        topics = set()
        for msg in messages[:10]:
            text = msg['doc'].get('message_text', '')
            # Extract first few words as "topic"
            words = text.split()[:3]
            if words:
                topics.add(" ".join(words))
        
        return f"Discussed: {', '.join(list(topics)[:5])}"


async def _combine_batch_summaries(batch_summaries: list, user_lang: str, conv_ctx) -> str:
    """
    Combine all batch summaries into one coherent digest using LLM.
    """
    try:
        combined_text = "\n\n".join(batch_summaries)
        
        prompt = f"""Create a comprehensive digest from these batch summaries:

{combined_text}

Provide a well-structured digest (max 200 words) that:
1. Identifies overall themes across all batches
2. Highlights most important discussions
3. Notes key participants if relevant
4. Maintains chronological flow if relevant

IMPORTANT: Format using HTML tags for Telegram:
- Use <b>bold</b> for emphasis
- Use <i>italic</i> for secondary emphasis
- Use bullet points with • or numbered lists
- Use line breaks (just newlines, no <br>)
- Do NOT use markdown (**, ##, ###) - use HTML only

Be engaging and well-organized."""
        
        from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
        from pydantic_ai import Agent
        
        model = await create_llm_model_with_fallback(f"kb_final_{conv_ctx.user_id}")
        agent = Agent(
            model=model,
            system_prompt=f"You are a helpful digest writer in {user_lang}. Create clear, engaging summaries using HTML formatting for Telegram (use <b>, <i>, no markdown)."
        )
        
        result = await agent.run(prompt)
        return result.output.strip()
        
    except Exception as e:
        logger.warning(f"Failed to combine summaries: {e}")
        # Fallback: return concatenated summaries
        return "\n\n".join(batch_summaries)


async def _create_digest_summary(messages: list, user_lang: str, conv_ctx, date_from: str = "", date_to: str = "") -> str:
    """
    Create a well-structured digest summary from messages using proper digest prompt.
    
    This applies the same high-quality digest formatting as batched processing,
    but for smaller result sets (<30 messages).
    """
    try:
        # Format messages for LLM
        messages_text = "\n".join([
            f"{i+1}. [{msg['doc'].get('sender_name', 'Unknown')}, {msg['doc'].get('message_date', '')[:16]}]: {msg['doc'].get('message_text', '')[:300]}"
            for i, msg in enumerate(messages)
        ])
        
        # Build time period description
        time_desc = ""
        if date_from and date_to:
            time_desc = f" from {date_from} to {date_to}"
        elif date_from:
            if date_from.endswith('d'):
                days = date_from[:-1]
                time_desc = f" from the past {days} days"
            elif date_from.endswith('w'):
                weeks = date_from[:-1]
                time_desc = f" from the past {weeks} weeks"
            else:
                time_desc = f" since {date_from}"
        
        prompt = f"""Create a comprehensive digest from these {len(messages)} messages{time_desc}:

{messages_text}

Provide a well-structured digest (max 200 words) that:
1. Identifies main themes and topics discussed
2. Highlights important discussions, decisions, or notable events
3. Notes key participants and their contributions if relevant
4. Maintains chronological flow where appropriate
5. Uses clear sections or bullet points for readability

IMPORTANT: Format using HTML tags for Telegram:
- Use <b>bold</b> for emphasis
- Use <i>italic</i> for secondary emphasis
- Use bullet points with • or numbered lists
- Use line breaks (just newlines, no <br>)
- Do NOT use markdown (**, ##, ###) - use HTML only

Be engaging, well-organized, and factual. Format as a proper digest summary."""
        
        from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
        from pydantic_ai import Agent
        
        model = await create_llm_model_with_fallback(f"kb_digest_{conv_ctx.user_id}")
        agent = Agent(
            model=model,
            system_prompt=f"You are an expert digest writer in {user_lang}. Create clear, engaging, well-structured summaries using HTML formatting for Telegram (use <b>, <i>, no markdown)."
        )
        
        result = await agent.run(prompt)
        return result.output.strip()
        
    except Exception as e:
        logger.warning(f"Failed to create digest summary: {e}")
        # Fallback: use basic summarization
        return await _summarize_message_batch(messages, batch_num=1, user_lang=user_lang, conv_ctx=conv_ctx)


async def _generate_kb_summary(query: str, results: list, conv_ctx: ConversationContext) -> str:
    """
    Generate a tweet-like LLM summary of KB search results.
    
    Args:
        query: User's search query
        results: List of search result dicts with 'text', 'role', 'date', 'sender'
        conv_ctx: Conversation context for language preferences
    
    Returns:
        A concise summary (max 280 chars, tweet-like)
    """
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIModel  # FIX 36: Use OpenAIModel for Ollama
        
        # Prepare context from results
        messages_text = "\n".join([
            f"- {r['role']} ({r['sender']}, {r['date'][:10]}): {r['text'][:200]}"
            for r in results[:5]  # Use top 5 for context
        ])
        
        # Get user's language preference
        from luka_bot.services.user_profile_service import get_user_profile_service
        profile_service = get_user_profile_service()
        user_lang = await profile_service.get_language(conv_ctx.user_id)
        
        lang_instruction = "in English" if user_lang == "en" else "in Russian (русский язык)"
        
        # Create summary prompt - more comprehensive than before
        summary_prompt = f"""Based on these search results for the query: "{query}"

{messages_text}

Provide a clear, informative summary (2-3 sentences, max 400 characters) {lang_instruction} that:
1. Directly answers what was found about "{query}"
2. Highlights the most important information from the conversations
3. Be specific and factual

Summary:"""
        
        # FIX 37: Use OllamaProvider like agent_factory.py does
        from pydantic_ai.providers.ollama import OllamaProvider  # Correct import!
        from pydantic_ai.settings import ModelSettings
        
        ollama_provider = OllamaProvider(base_url=settings.OLLAMA_URL)
        model_settings = ModelSettings(
            temperature=0.3,  # Lower temp for more focused summaries
            max_tokens=100  # Short summaries only
        )
        
        ollama_model = OpenAIModel(
            model_name=settings.OLLAMA_MODEL_NAME,
            provider=ollama_provider,
            settings=model_settings
        )
        
        summary_agent = Agent(
            model=ollama_model,
            system_prompt=f"You are a helpful knowledge base assistant. Provide clear, informative summaries in {user_lang}. Be conversational and helpful."
        )
        
        # Generate summary
        result = await summary_agent.run(summary_prompt)
        summary = result.output.strip()  # FIX 38: Use .output, not .data
        
        # Ensure it's not too long (max 400 chars)
        if len(summary) > 400:
            summary = summary[:397] + "..."
        
        return summary
        
    except Exception as e:
        logger.warning(f"Failed to generate KB summary: {e}")
        # Fallback: use first result's text
        if results:
            first_text = results[0]['text'][:280]
            return f"Found information about: {first_text}..."
        return "Found relevant information in your message history."


async def search_knowledge_base(
    ctx: RunContext[ConversationContext],  # FIX 33: Use RunContext wrapper
    query: str = Field(description=(
        "Search query text. IMPORTANT decision logic:\n"
        "- Use '*' (wildcard) when user wants ALL messages in a time period WITHOUT specific topic\n"
        "  Examples: 'last week digest', 'what happened from 10-17 october', 'show me everything from march'\n"
        "- Use specific keywords when searching FOR something in a time period\n"
        "  Examples: 'postgres issues last week' → query='postgres issues', 'John's messages about API' → query='API'"
    )),
    max_results: int = Field(default=5, description="Maximum number of results to return (1-20)"),
    from_user: str = Field(default="", description="Filter by sender name/username (e.g., 'John', 'alice123'). Leave empty for all users."),
    date_from: str = Field(default="", description="Start date: '7d' (7 days ago), '1m' (1 month), or 'YYYY-MM-DD'. LEAVE EMPTY to search ALL history (recommended default). Only specify if user explicitly mentions time period."),
    date_to: str = Field(default="", description="End date in 'YYYY-MM-DD' format. LEAVE EMPTY for current time (recommended default)."),
    min_score: float = Field(default=0.1, description="Minimum relevance score (0.0-1.0). Higher = more relevant. Default 0.1 for broad search.")
) -> str:
    """
    Search the knowledge base (message history) with advanced filtering.
    
    This tool searches through messages with support for:
    - Text search with BM25 ranking and fuzzy matching
    - Date range filtering (absolute or relative dates)
    - Sender/user filtering
    - Relevance score threshold
    
    CRITICAL QUERY LOGIC:
    - query='*' + date filters = Get ALL messages in time period (for digests, summaries, "what happened")
    - query='keywords' + date filters = Search for specific topic in time period
    
    Use this when users ask:
    - "What did we discuss about X?" → query="X"
    - "What did John say about Y?" → query="Y", from_user="John"
    - "Find messages about Z from last week" → query="Z", date_from="7d"
    - "Show me discussions about A in March" → query="A", date_from="2025-03-01", date_to="2025-03-31"
    - "Last week digest" → query="*", date_from="7d"
    - "What was discussed from 10-17 october?" → query="*", date_from="2025-10-10", date_to="2025-10-17"
    
    Examples:
    - search_knowledge_base(query="deployment issues", date_from="7d")  # Search for "deployment issues" last week
    - search_knowledge_base(query="*", date_from="7d")  # ALL messages from last week
    - search_knowledge_base(query="postgres", from_user="Evgeny")  # Evgeny's messages about postgres
    - search_knowledge_base(query="API design", date_from="2025-01-01", date_to="2025-01-31")  # API in January
    """
    # FIX 33: Access context via RunContext.deps
    conv_ctx = ctx.deps
        
    # Get user language first (needed for error messages)
    user_lang = "en"  # Default
    try:
        from luka_bot.services.user_profile_service import UserProfileService
        profile_service = UserProfileService()
        profile = await profile_service.get_profile(conv_ctx.user_id)
        user_lang = profile.language if profile else "en"
    except Exception as lang_error:
        logger.debug(f"Could not get user language: {lang_error}")
    
    try:
        # Enhanced logging - log all parameters
        logger.info(f"🔍 KB Search STARTED")
        logger.info(f"  └─ User: {conv_ctx.user_id}")
        logger.info(f"  └─ Query: '{query}'")
        logger.info(f"  └─ Filters: from_user='{from_user}', date_from='{date_from}', date_to='{date_to}'")
        logger.info(f"  └─ Settings: max_results={max_results}, min_score={min_score}")
        
        # Create cache key from search parameters to prevent duplicate ES queries
        # This happens when pydantic-ai re-executes tools during get_output()
        # Note: We'll update kb_indices after scope resolution
        cache_params = {
            'user_id': conv_ctx.user_id,
            'query': query,
            'from_user': from_user,
            'date_from': date_from,
            'date_to': date_to,
            'max_results': max_results,
            'min_score': min_score,
            'kb_scope': conv_ctx.kb_scope,  # Include scope in cache key
            'thread_kb': conv_ctx.thread_knowledge_bases
        }
        cache_key = hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()
        
        # Check cache
        if cache_key in _kb_search_cache:
            cached_result = _kb_search_cache[cache_key]
            logger.info(f"💾 Returning CACHED result (key: {cache_key[:8]}..., {len(cached_result)} chars)")
            logger.info(f"🔍 KB Search COMPLETED (from cache)")
            return cached_result
        
        # Check if Elasticsearch is enabled
        if not settings.ELASTICSEARCH_ENABLED:
            logger.warning("Elasticsearch is disabled in settings")
            return _("kb.disabled", language=user_lang)
        
        # Get Elasticsearch service
        es_service = await get_elasticsearch_service()
        
        # Determine which KB to search
        # Priority: user KB scope > thread-specific KB > user KB
        kb_indices = None
        
        # Check user's KB scope preferences first
        if conv_ctx.kb_scope:
            scope = conv_ctx.kb_scope
            scope_source = scope.get("source", "all")
            scope_group_ids = scope.get("group_ids", [])
            
            if scope_source == "all":
                # User wants all sources - use default behavior
                kb_indices = None
                logger.info("User scope: all sources - using default KB behavior")
            elif scope_source in ["auto_groups", "custom"] and scope_group_ids:
                # User has specific group scope - map to KB indices
                kb_indices = [f"group_{group_id}_messages" for group_id in scope_group_ids]
                logger.info(f"User scope: {scope_source} - searching groups: {scope_group_ids}")
                logger.info(f"Mapped to KB indices: {kb_indices}")
            else:
                # Scope exists but no groups - fall back to default
                kb_indices = None
                logger.info("User scope: no groups - using default KB behavior")
        
        # If no scope or scope didn't specify indices, check thread-specific KB
        if kb_indices is None:
            if conv_ctx.thread_knowledge_bases and len(conv_ctx.thread_knowledge_bases) > 0:
                # Thread has specific KBs attached (full index names)
                kb_indices = conv_ctx.thread_knowledge_bases
                logger.info(f"Searching thread-specific KBs: {kb_indices}")
            else:
                # Default: search user's personal KB
                kb_indices = [f"{settings.ELASTICSEARCH_USER_KB_PREFIX}{conv_ctx.user_id}"]
                logger.info(f"Searching user KB: {kb_indices[0]}")
        
        # Update cache key with final kb_indices
        cache_params['kb_indices'] = kb_indices
        cache_key = hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()
        
        # # TEST: Override with specific test index (comment out when done testing)
        # kb_indices = ["tg-kb-group-1001902150742"]
        # logger.info(f"🧪 TEST OVERRIDE: Using test index: {kb_indices}")
        
        # Parse and validate parameters
        actual_max_results = max_results if isinstance(max_results, int) else 5
        actual_max_results = max(1, min(actual_max_results, 20))  # Clamp to 1-20
        
        actual_min_score = min_score if isinstance(min_score, (int, float)) else 0.1
        actual_min_score = max(0.0, min(actual_min_score, 1.0))  # Clamp to 0-1
        
        # Parse date filters
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            try:
                from datetime import datetime, timedelta
                
                # Check if relative date (e.g., "7d", "2w", "1m")
                if date_from.endswith('d') and date_from[:-1].isdigit():
                    # Days ago
                    days = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(days=days)
                    logger.info(f"📅 Parsed relative date_from: '{date_from}' → {days} days ago → {date_from_dt.isoformat()}")
                elif date_from.endswith('w') and date_from[:-1].isdigit():
                    # Weeks ago
                    weeks = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(weeks=weeks)
                    logger.info(f"📅 Parsed relative date_from: '{date_from}' → {weeks} weeks ago → {date_from_dt.isoformat()}")
                elif date_from.endswith('m') and date_from[:-1].isdigit():
                    # Months ago (approximate as 30 days)
                    months = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(days=months * 30)
                    logger.info(f"📅 Parsed relative date_from: '{date_from}' → {months} months ago → {date_from_dt.isoformat()}")
                else:
                    # Try to parse as ISO date
                    date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    logger.info(f"📅 Parsed absolute date_from: '{date_from}' → {date_from_dt.isoformat()}")
            except Exception as e:
                logger.warning(f"⚠️  Could not parse date_from '{date_from}': {e}")
        else:
            logger.info(f"📅 No date_from filter - searching ALL history")
        
        if date_to:
            try:
                from datetime import datetime, timedelta
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                # Add 1 day to include the entire end date (2025-10-17 means "through end of Oct 17")
                date_to_dt = date_to_dt + timedelta(days=1)
                logger.info(f"📅 Parsed date_to: '{date_to}' → {date_to_dt.isoformat()} (inclusive, +1 day)")
            except Exception as e:
                logger.warning(f"⚠️  Could not parse date_to '{date_to}': {e}")
        else:
            logger.info(f"📅 No date_to filter - searching up to NOW")
        
        # Search all relevant KBs
        all_results = []
        for kb_index in kb_indices:
            try:
                logger.info(f"🔎 Building Elasticsearch query for index: {kb_index}")
                
                # Build Elasticsearch query with filters
                # Special handling: If query is "*", use match_all instead of multi_match
                if query.strip() == "*":
                    must_clauses = [{"match_all": {}}]
                    logger.info(f"  └─ Base query: match_all (wildcard '*' detected - returning ALL documents)")
                else:
                    must_clauses = [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["message_text^3", "sender_name^2", "mentions", "hashtags"],
                                "fuzziness": "AUTO",
                                "type": "best_fields"
                            }
                        }
                    ]
                    logger.info(f"  └─ Base query: multi_match on '{query}' (fields: message_text^3, sender_name^2, mentions, hashtags)")
                
                # Add user filter if specified
                if from_user and from_user.strip():
                    must_clauses.append({
                        "match": {
                            "sender_name": {
                                "query": from_user.strip(),
                                "fuzziness": "AUTO"
                            }
                        }
                    })
                    logger.info(f"  └─ 👤 Added user filter: sender_name='{from_user}'")
                
                # Add date range filter if specified
                if date_from_dt or date_to_dt:
                    date_range = {}
                    if date_from_dt:
                        date_range["gte"] = date_from_dt.isoformat()
                    if date_to_dt:
                        date_range["lte"] = date_to_dt.isoformat()
                    
                    must_clauses.append({
                        "range": {
                            "message_date": date_range
                        }
                    })
                    logger.info(f"  └─ 📅 Added date range filter: {date_range}")
                
                # Build full query
                es_query = {
                    "query": {
                        "bool": {
                            "must": must_clauses
                        }
                    },
                    "min_score": actual_min_score,
                    "size": actual_max_results * 3,  # Get more for filtering
                    "sort": [
                        {"_score": {"order": "desc"}},
                        {"message_date": {"order": "desc"}}
                    ]
                }
                
                logger.info(f"  └─ Query settings: min_score={actual_min_score}, size={actual_max_results * 3}")
                logger.info(f"  └─ Total must_clauses: {len(must_clauses)}")
                
                # STEP 1: Count total results first to decide strategy
                count_query = {
                    "query": {
                        "bool": {
                            "must": must_clauses
                        }
                    }
                }
                logger.info(f"📊 Counting total matching documents...")
                count_response = await es_service.client.count(index=kb_index, body=count_query)
                total_count = count_response.get('count', 0)
                logger.info(f"  └─ Total matching documents: {total_count}")
                
                # STEP 2: Decide strategy based on count
                BATCH_THRESHOLD = 30
                
                # Distinguish between digest requests (all messages) vs content searches (top results)
                is_digest_request = (query.strip() == "*" and (date_from_dt or date_to_dt))
                
                if total_count > BATCH_THRESHOLD and is_digest_request:
                    # Large result set + digest request - use batched processing
                    logger.info(f"🔄 Digest request with {total_count} messages (> {BATCH_THRESHOLD}) - using batched processing")
                    
                    combined_summary, batched_messages = await _process_large_result_set_batched(
                        es_service=es_service,
                        kb_index=kb_index,
                        must_clauses=must_clauses,
                        total_count=total_count,
                        user_lang=user_lang,
                        conv_ctx=conv_ctx
                    )
                    
                    # Store batched results and summary
                    all_results.extend(batched_messages)
                    logger.info(f"✅ Batched processing complete: {len(batched_messages)} messages processed")
                    
                    # Store summary for later use (will be prepended to result)
                    # Store it in a way we can retrieve it later
                    if not hasattr(conv_ctx, '_kb_batch_summary'):
                        conv_ctx._kb_batch_summary = combined_summary
                    
                else:
                    # Small result set OR content search - use regular single query
                    if total_count > BATCH_THRESHOLD:
                        logger.info(f"✅ Content search with {total_count} total matches - fetching top {actual_max_results * 3} by relevance (not batching)")
                    else:
                        logger.info(f"✅ Small result set ({total_count} ≤ {BATCH_THRESHOLD}) - using single query")
                    
                    # STEP 3: Execute search (current behavior)
                    logger.info(f"⚡ Executing Elasticsearch query...")
                    # Log the actual query for debugging
                    logger.debug(f"  └─ Full ES query: {json.dumps(es_query, indent=2)}")
                    response = await es_service.client.search(index=kb_index, body=es_query)
                    
                    # Parse results
                    hits = response.get('hits', {}).get('hits', [])
                    total_hits = response.get('hits', {}).get('total', {})

                    if hits:
                        # Calculate score statistics
                        scores = [hit.get('_score') or 1.0 for hit in hits]
                        min_result_score = min(scores)
                        max_result_score = max(scores)
                        avg_result_score = sum(scores) / len(scores)

                        logger.info(f"✅ Found {len(hits)} results in {kb_index}")
                        logger.info(f"  └─ Score range: {min_result_score:.3f} - {max_result_score:.3f} (avg: {avg_result_score:.3f})")
                        logger.info(f"  └─ Total matching docs: {total_hits}")

                        # Log sample of top results
                        for i, hit in enumerate(hits[:3], 1):
                            doc = hit['_source']
                            sender = doc.get('sender_name', 'Unknown')
                            text_preview = doc.get('message_text', '')[:60].replace('\n', ' ')
                            date = doc.get('message_date', 'N/A')[:10]
                            score = hit.get('_score') or 1.0
                            logger.info(f"  └─ #{i}: score={score:.3f}, {sender}, {date}: \"{text_preview}...\"")

                        for hit in hits:
                            all_results.append({
                                'score': hit.get('_score') or 1.0,
                                'doc': hit['_source']
                            })
                    else:
                        logger.info(f"❌ No results found in {kb_index} (total: {total_hits})")
                    
            except Exception as e:
                logger.warning(f"⚠️  Error searching {kb_index}: {e}")
                # Fallback to simple search if advanced query fails
                try:
                    logger.info(f"🔄 Trying fallback search (simple search_messages_text)...")
                    results = await es_service.search_messages_text(
                        index_name=kb_index,
                        query_text=query,
                        min_score=actual_min_score,
                        max_results=actual_max_results * 3
                    )
                    if results:
                        all_results.extend(results)
                        logger.info(f"✅ Fallback search succeeded: {len(results)} results")
                    else:
                        logger.info(f"❌ Fallback search returned no results")
                except Exception as fallback_error:
                    logger.warning(f"⚠️  Fallback search also failed: {fallback_error}")
                continue
        
        # Format results
        if not all_results:
            logger.info(f"🔍 KB Search COMPLETED: 0 results found")
            logger.info(f"  └─ Query: '{query}', Filters: user={from_user or 'none'}, dates={date_from or 'none'} to {date_to or 'none'}")
            # Return instruction for LLM to use general knowledge
            # Empty string confuses LLM into producing no output
            # This format makes it clear: "no KB results, but please answer the question"
            result = "[No messages found in knowledge base - please answer the user's question using your general knowledge]"
            
            # Cache the no-results response too
            _kb_search_cache[cache_key] = result
            logger.debug(f"💾 Cached no-results response (key: {cache_key[:8]}...)")
            
            return result
        
        # Filter out any results with None scores and sort by score (descending)
        all_results = [r for r in all_results if r.get('score') is not None]
        all_results.sort(key=lambda x: x['score'], reverse=True)
        total_found = len(all_results)
        
        # Separate: ALL messages for LLM context vs top 5 for display
        display_results = all_results[:min(5, actual_max_results)]  # Top 5 for cards
        # Keep all_results intact for LLM context summary
        
        # Log final search summary
        logger.info(f"🔍 KB Search COMPLETED: {total_found} total results (showing {len(display_results)} cards, {total_found} for LLM context)")
        logger.info(f"  └─ Query: '{query}'")
        logger.info(f"  └─ Filters applied: user={from_user or 'none'}, date_from={date_from or 'none'}, date_to={date_to or 'none'}")
        if all_results:
            logger.info(f"  └─ Top result score: {all_results[0]['score']:.3f}")
        if display_results:
            logger.info(f"  └─ Lowest shown score: {display_results[-1]['score']:.3f}")
        
        # Build response with modern card-based formatting
        # IMPORTANT: This tool returns ONLY the formatted message snippets
        # The main LLM will provide the summary BEFORE calling this tool
        # Expected format:
        #   [LLM Summary: "Found several discussions about X"]
        #   [Tool Output: formatted message cards with links]
        
        response_parts = []
        
        # Detect if this is a digest request (query='*' with date filters)
        is_digest_request = (query.strip() == "*" and (date_from or date_to))
        
        # If batched processing was used, prepend the combined summary
        if hasattr(conv_ctx, '_kb_batch_summary') and conv_ctx._kb_batch_summary:
            response_parts.append("\n📊 <b>Comprehensive Digest:</b>")
            response_parts.append(conv_ctx._kb_batch_summary)
            response_parts.append("")  # Empty line for separation
            logger.debug(f"📝 Prepended batched summary to results: {len(conv_ctx._kb_batch_summary)} chars")
            # Clear the summary after use
            delattr(conv_ctx, '_kb_batch_summary')
        
        # For digest requests with <30 messages: use proper digest summarization
        elif is_digest_request and total_found <= 30 and total_found > 0:
            # Generate proper digest summary (same quality as batched)
            logger.info(f"🤖 Generating digest summary from {total_found} messages...")
            try:
                digest = await _create_digest_summary(
                    all_results,
                    user_lang=user_lang,
                    conv_ctx=conv_ctx,
                    date_from=date_from,
                    date_to=date_to
                )
                response_parts.append("\n📊 <b>Digest:</b>")
                response_parts.append(digest)
                response_parts.append("")
                logger.debug(f"📝 Generated digest from {total_found} messages: {len(digest)} chars")
            except Exception as e:
                logger.warning(f"Failed to generate digest: {e}")
                # Continue without summary
        
        # For content searches with many results (6-30): generate basic summary
        elif not is_digest_request and total_found > len(display_results) and total_found <= 30:
            # Generate basic summary for content search results
            logger.info(f"🤖 Generating summary from {total_found} search results...")
            try:
                summary = await _summarize_message_batch(all_results, batch_num=1, user_lang=user_lang, conv_ctx=conv_ctx)
                response_parts.append("\n📊 <b>Summary:</b>")
                response_parts.append(summary)
                response_parts.append("")
                logger.debug(f"📝 Generated summary from {total_found} messages: {len(summary)} chars")
            except Exception as e:
                logger.warning(f"Failed to generate summary: {e}")
                # Continue without summary
        
        # Header with count
        message_word = "message" if len(display_results) == 1 else "messages"
        if user_lang == "ru":
            message_word = "сообщение" if len(display_results) == 1 else "сообщения" if len(display_results) < 5 else "сообщений"
        
        response_parts.extend([
            "\n━━━━━━━━━━━━━━━━━━━━",
            f"📚 Found {total_found} {message_word} (showing {len(display_results)} samples)\n"
        ])
        
        for i, result in enumerate(display_results, 1):
            doc = result['doc']
            
            # Extract message details
            sender = doc.get('sender_name', 'Unknown')
            text = doc.get('message_text', '')
            date = doc.get('message_date', '')
            message_id = doc.get('message_id', '')
            group_id = doc.get('group_id', None)
            
            # Format date (just date and time, no seconds)
            if date:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = date[:16]  # Fallback: first 16 chars
            else:
                date_str = "Unknown date"
            
            # Clean text: replace newlines with spaces and truncate
            text = text.replace('\n', ' ').replace('\r', ' ')
            max_text_length = 150
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            
            # Build deeplink if this is a group message
            deeplink_url = None
            if group_id and message_id:
                # Extract telegram message ID from composite message_id
                # Format: {group_id}_{telegram_message_id} or user_{user_id}_group_{group_id}_{telegram_message_id}
                try:
                    # Parse message_id to get telegram_message_id
                    parts = message_id.split('_')
                    telegram_msg_id = parts[-1] if parts else None
                    
                    if telegram_msg_id and telegram_msg_id.isdigit():
                        # Convert group_id for deeplink
                        # Telegram group IDs are like -1001234567890
                        # Deeplink format: https://t.me/c/{chat_id_without_-100_prefix}/{message_id}
                        group_id_str = str(group_id)
                        if group_id_str.startswith('-100'):
                            chat_id_for_link = group_id_str[4:]  # Remove -100 prefix
                            # Ensure both values are non-empty before creating link
                            if chat_id_for_link and telegram_msg_id:
                                deeplink_url = f"https://t.me/c/{chat_id_for_link}/{telegram_msg_id}"
                except Exception as e:
                    logger.debug(f"Failed to generate deeplink: {e}")
            
            # Build message card with simple box decoration
            # ┌─ at first line, └───── as divider
            # Make date clickable if deeplink is available
            if deeplink_url:
                date_display = f"<a href=\"{deeplink_url}\">{date_str}</a>"
            else:
                date_display = date_str
            
            card_lines = [
                # f"┌─ 👤 <b>{sender}</b> • {date_str}",
                f"┌─ 👤 <b>{sender}</b> • {date_display}",
                f"\"{text}\""
            ]
            
            # # Add raw URL link if available (no HTML anchor tags)
            # if deeplink_url:
            #     card_lines.append(f"🔗 {deeplink_url}")
            
            # Add divider after each message
            card_lines.append("└─────")
            
            response_parts.append("\n".join(card_lines) + "\n")
        
        response_parts.append("━━━━━━━━━━━━━━━━━━━━\n")
        
        # Return the structured results
        # The LLM's summary will be separate from this structured data
        result = "\n".join(response_parts)
        
        # Cache the result to prevent duplicate ES queries
        _kb_search_cache[cache_key] = result
        logger.debug(f"💾 Cached result (key: {cache_key[:8]}..., {len(result)} chars)")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in search_knowledge_base: {e}", exc_info=True)
        # FIX 41: Error message with i18n
        return _("kb.error", language=user_lang, error=str(e))


async def list_recent_messages(
    ctx: RunContext[ConversationContext],
    max_results: int = Field(default=10, description="Number of recent messages (5-50, default 10)")
) -> str:
    """
    List the most recent messages from the knowledge base without search query.
    
    Use when users ask:
    - "What's in the knowledge base?"
    - "Show me recent messages"
    - "What have we discussed recently?"
    - "Browse my message history"
    
    Returns formatted list of recent messages with dates and senders.
    """
    conv_ctx = ctx.deps
    
    try:
        from luka_bot.services.user_profile_service import UserProfileService
        profile_service = UserProfileService()
        profile = await profile_service.get_profile(conv_ctx.user_id)
        user_lang = profile.language if profile else "en"
        
        if not settings.ELASTICSEARCH_ENABLED:
            return _("kb.disabled", language=user_lang)
        
        es_service = await get_elasticsearch_service()
        
        # Determine KB index
        if conv_ctx.thread_knowledge_bases:
            kb_indices = conv_ctx.thread_knowledge_bases
        else:
            kb_indices = [f"{settings.ELASTICSEARCH_USER_KB_PREFIX}{conv_ctx.user_id}"]
        
        # Clamp results
        actual_max = max(5, min(max_results, 50))
        
        # Get recent messages
        all_results = []
        for kb_index in kb_indices:
            try:
                query = {
                    "query": {"match_all": {}},
                    "size": actual_max,
                    "sort": [{"message_date": {"order": "desc"}}]
                }
                
                response = await es_service.client.search(index=kb_index, body=query)
                hits = response.get('hits', {}).get('hits', [])
                
                for hit in hits:
                    all_results.append({
                        'doc': hit['_source'],
                        'score': 1.0
                    })
            except Exception as e:
                logger.warning(f"Error listing messages from {kb_index}: {e}")
                continue
        
        if not all_results:
            if user_lang == "ru":
                return "Ваша база знаний пуста. Начните общаться, чтобы создать историю сообщений!"
            return "Your knowledge base is empty. Start chatting to build your message history!"
        
        # Sort by date and limit
        all_results.sort(key=lambda x: x['doc'].get('message_date', ''), reverse=True)
        all_results = all_results[:actual_max]
        
        # Format results
        message_word = "message" if len(all_results) == 1 else "messages"
        if user_lang == "ru":
            message_word = "сообщение" if len(all_results) == 1 else "сообщения" if len(all_results) < 5 else "сообщений"
        
        lines = [
            "\n━━━━━━━━━━━━━━━━━━━━",
            f"📚 Your {len(all_results)} most recent {message_word}:\n"
        ]
        
        for result in all_results:
            doc = result['doc']
            sender = doc.get('sender_name', 'Unknown')
            text = doc.get('message_text', '')
            date = doc.get('message_date', '')
            
            # Format date
            if date:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = date[:16]
            else:
                date_str = "Unknown"
            
            # Truncate text
            text = text.replace('\n', ' ').replace('\r', ' ')
            if len(text) > 100:
                text = text[:100] + "..."
            
            lines.append(f"• {sender} ({date_str}): {text}")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━\n")
        
        return "\n".join(lines)
        
    except Exception as e:
        logger.error(f"Error in list_recent_messages: {e}", exc_info=True)
        return _("kb.error", language=user_lang, error=str(e))


async def get_knowledge_base_stats(
    ctx: RunContext[ConversationContext],
    date_from: str = Field(default="7d", description="Start date: '7d' (days), '1w' (weeks), '1m' (months), '1y' (years), or 'YYYY-MM-DD'. Default: 7d (last 7 days)"),
    date_to: str = Field(default="", description="End date in 'YYYY-MM-DD' format. Leave empty for current time."),
    include_timeline: bool = Field(default=False, description="Include daily message timeline (histogram)"),
    include_hourly_activity: bool = Field(default=False, description="Include hourly activity pattern (peak hours)"),
    include_hashtags: bool = Field(default=False, description="Include most used hashtags"),
    include_media_breakdown: bool = Field(default=False, description="Include media types breakdown"),
    include_user_engagement: bool = Field(default=False, description="Include user engagement distribution"),
    include_unanswered_questions: bool = Field(default=True, description="Include unanswered questions analysis"),
    top_n: int = Field(default=5, description="Number of top items to show (users, hashtags, etc). Default: 5")
) -> str:
    """
    Get comprehensive KB statistics using advanced Elasticsearch aggregations.
    
    This tool provides flexible analytics about the knowledge base:
    
    BASIC STATS (always included):
    - Total messages and KB size
    - Active users count
    - Top contributors
    
    OPTIONAL ADVANCED STATS (controlled by flags):
    - Timeline: Daily message count histogram
    - Hourly Activity: Peak activity hours
    - Hashtags: Most used hashtags
    - Media Breakdown: Distribution of text/images/documents
    - User Engagement: How many users post how often
    - Unanswered Questions: Questions without answers (LLM-analyzed)
    
    Examples:
    - Basic stats for last week: get_knowledge_base_stats()
    - Full analytics for last month: get_knowledge_base_stats(date_from="30d", include_timeline=True, include_hourly_activity=True, include_hashtags=True)
    - Annual review: get_knowledge_base_stats(date_from="1y", include_timeline=True, include_user_engagement=True)
    - Activity patterns: get_knowledge_base_stats(include_hourly_activity=True, include_timeline=True)
    - Content analysis: get_knowledge_base_stats(include_hashtags=True, include_media_breakdown=True)
    """
    conv_ctx = ctx.deps
    
    try:
        from luka_bot.services.user_profile_service import UserProfileService
        from datetime import datetime, timedelta
        
        profile_service = UserProfileService()
        profile = await profile_service.get_profile(conv_ctx.user_id)
        user_lang = profile.language if profile else "en"
        
        if not settings.ELASTICSEARCH_ENABLED:
            return _("kb.disabled", language=user_lang)
        
        es_service = await get_elasticsearch_service()
        stats_parts = []
        
        # Determine which KB indices to query
        kb_indices = []
        if conv_ctx.thread_knowledge_bases and len(conv_ctx.thread_knowledge_bases) > 0:
            kb_indices = conv_ctx.thread_knowledge_bases
            logger.info(f"📊 Getting stats for thread KBs: {kb_indices}")
        else:
            kb_indices = [f"{settings.ELASTICSEARCH_USER_KB_PREFIX}{conv_ctx.user_id}"]
            logger.info(f"📊 Getting stats for user KB: {kb_indices[0]}")
        
        # Parse date parameters
        date_from_dt = None
        date_to_dt = None
        
        if date_from:
            try:
                # Check if relative date (e.g., "7d", "30d", "1w", "1m", "1y")
                if date_from.endswith('d') and date_from[:-1].isdigit():
                    days = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(days=days)
                elif date_from.endswith('w') and date_from[:-1].isdigit():
                    weeks = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(weeks=weeks)
                elif date_from.endswith('m') and date_from[:-1].isdigit():
                    months = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(days=months * 30)
                elif date_from.endswith('y') and date_from[:-1].isdigit():
                    years = int(date_from[:-1])
                    date_from_dt = datetime.utcnow() - timedelta(days=years * 365)
                else:
                    date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"⚠️  Could not parse date_from '{date_from}': {e}")
        
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"⚠️  Could not parse date_to '{date_to}': {e}")
        
        # Collect stats for each index
        for kb_index in kb_indices:
            try:
                # Get basic index stats
                index_stats = await es_service.get_index_stats(kb_index)
                message_count = index_stats.get("message_count", 0)
                size_mb = index_stats.get("size_mb", 0.0)
                
                # Determine if this is a group KB
                is_group_kb = kb_index.startswith("tg-kb-group-")
                
                # Build stats text
                if message_count == 0:
                    stats_parts.append(_("kb.stats.empty_header", user_lang, kb_index=kb_index))
                    continue
                
                # Get advanced stats
                advanced_stats = await es_service.get_advanced_kb_stats(
                    index_name=kb_index,
                    date_from=date_from_dt,
                    date_to=date_to_dt,
                    include_timeline=include_timeline,
                    include_hourly_activity=include_hourly_activity,
                    include_hashtags=include_hashtags,
                    include_media_breakdown=include_media_breakdown,
                    include_user_engagement=include_user_engagement,
                    top_n=top_n
                )
                
                # Header
                if is_group_kb:
                    stats_parts.append(_("kb.stats.group_header", user_lang, index=kb_index))
                else:
                    stats_parts.append(_("kb.stats.user_header", user_lang))
                
                # Basic stats
                total_messages = advanced_stats.get("total_messages", message_count)
                unique_users = advanced_stats.get("unique_users", 0)
                
                stats_parts.append(_("kb.stats.total_messages", user_lang, count=total_messages))
                if is_group_kb:
                    stats_parts.append(_("kb.stats.active_users", user_lang, count=unique_users))
                stats_parts.append(_("kb.stats.kb_size", user_lang, size=size_mb))
                
                # Top users
                top_users = advanced_stats.get("top_users", [])
                if top_users:
                    stats_parts.append(_("kb.stats.top_users_header", user_lang))
                    for i, user_data in enumerate(top_users[:top_n], 1):
                        name = user_data['sender_name']
                        count = user_data['message_count']
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"  {i}."
                        stats_parts.append(_("kb.stats.top_user_entry", user_lang, 
                                           medal=medal, name=name, count=count))
                
                # Timeline
                if include_timeline and "timeline" in advanced_stats:
                    timeline = advanced_stats["timeline"]
                    if timeline:
                        period_desc = f"{date_from or 'all time'}"
                        stats_parts.append(_("kb.stats.timeline_header", user_lang, period=period_desc))
                        for entry in timeline[-7:]:  # Show last 7 days
                            date = entry["date"]
                            count = entry["message_count"]
                            # Create simple bar chart
                            max_bar_len = 20
                            bar_len = min(int((count / max(1, max(e["message_count"] for e in timeline))) * max_bar_len), max_bar_len)
                            bar = "█" * bar_len
                            stats_parts.append(_("kb.stats.timeline_entry", user_lang, 
                                               date=date, bar=bar, count=count))
                
                # Hourly activity
                if include_hourly_activity and "hourly_activity" in advanced_stats:
                    hourly = advanced_stats["hourly_activity"]
                    if hourly:
                        stats_parts.append(_("kb.stats.hourly_header", user_lang))
                        # Sort by message count and show top 3
                        top_hours = sorted(hourly, key=lambda x: x["message_count"], reverse=True)[:3]
                        for i, entry in enumerate(top_hours, 1):
                            hour = entry["hour"]
                            next_hour = (hour + 1) % 24
                            count = entry["message_count"]
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                            stats_parts.append(_("kb.stats.hourly_entry", user_lang,
                                               medal=medal, hour=hour, next_hour=next_hour, count=count))
                
                # Hashtags
                if include_hashtags and "top_hashtags" in advanced_stats:
                    hashtags = advanced_stats["top_hashtags"]
                    if hashtags:
                        stats_parts.append(_("kb.stats.hashtags_header", user_lang))
                        for entry in hashtags[:top_n]:
                            tag = entry["hashtag"]
                            count = entry["count"]
                            stats_parts.append(_("kb.stats.hashtag_entry", user_lang, 
                                               tag=tag, count=count))
                
                # Media breakdown
                if include_media_breakdown and "media_types" in advanced_stats:
                    media = advanced_stats["media_types"]
                    if media:
                        stats_parts.append(_("kb.stats.media_header", user_lang))
                        total = sum(e["count"] for e in media)
                        for entry in media:
                            media_type = entry["type"]
                            count = entry["count"]
                            percent = (count / total * 100) if total > 0 else 0
                            
                            # Icon mapping
                            icon = {
                                "text": "📝",
                                "photo": "📷",
                                "document": "📎",
                                "video": "🎥",
                                "audio": "🎵",
                                "voice": "🎤"
                            }.get(media_type, "📄")
                            
                            stats_parts.append(_("kb.stats.media_entry", user_lang,
                                               icon=icon, type=media_type, count=count, percent=f"{percent:.1f}"))
                
                # User engagement
                if include_user_engagement and "user_engagement" in advanced_stats:
                    engagement = advanced_stats["user_engagement"]
                    stats_parts.append(_("kb.stats.engagement_header", user_lang))
                    
                    engagement_map = [
                        ("one_time", "💬", _("kb.stats.engagement_onetime", user_lang)),
                        ("occasional", "📝", _("kb.stats.engagement_occasional", user_lang)),
                        ("regular", "✍️", _("kb.stats.engagement_regular", user_lang)),
                        ("active", "🔥", _("kb.stats.engagement_active", user_lang)),
                        ("very_active", "⭐", _("kb.stats.engagement_veryactive", user_lang))
                    ]
                    
                    for key, icon, level_name in engagement_map:
                        count = engagement.get(key, 0)
                        if count > 0:
                            stats_parts.append(_("kb.stats.engagement_entry", user_lang,
                                               icon=icon, level=level_name, count=count))
                
                # Unanswered questions (for groups)
                if include_unanswered_questions and is_group_kb:
                    unanswered = await es_service.find_unanswered_questions_llm(
                        index_name=kb_index,
                        lookback_days=7,
                        max_messages=50,
                        language=user_lang
                    )
                    
                    if unanswered:
                        stats_parts.append(_("kb.stats.unanswered_header", user_lang, count=len(unanswered)))
                        for i, q in enumerate(unanswered[:5], 1):
                            question_text = q.get('question', '')[:100]
                            sender = q.get('sender', 'Unknown')
                            reason = q.get('reason', 'No response found')
                            stats_parts.append(_("kb.stats.unanswered_entry", user_lang,
                                               num=i, sender=sender, question=question_text, reason=reason))
                    else:
                        stats_parts.append(_("kb.stats.no_unanswered", user_lang))
                            
            except Exception as e:
                logger.warning(f"Failed to get stats for {kb_index}: {e}")
                continue
        
        if not stats_parts:
            return _("kb.stats.error", user_lang)
        
        return "\n".join(stats_parts)
        
    except Exception as e:
        logger.error(f"Error in get_knowledge_base_stats: {e}", exc_info=True)
        return _("kb.error", language=user_lang, error=str(e))


def get_tools():
    """Return KB search tools for agent."""
    from pydantic_ai.tools import Tool
    
    return [
        Tool(
            search_knowledge_base,
            name="search_knowledge_base",
            description=(
                "Search user's message history with text query and optional filters.\n\n"
                "USE WHEN: User asks about past conversations/messages they've had.\n"
                "✅ ALWAYS USE FOR DIGESTS/SUMMARIES/OVERVIEWS with time periods!\n"
                "Examples:\n"
                "  - 'digest for last 5 days' → USE THIS TOOL with query='*', date_from='5d'\n"
                "  - 'what happened from 10-17 oct' → USE THIS TOOL with query='*', date_from='2025-10-10', date_to='2025-10-17'\n"
                "  - 'make digest from group for last week' → USE THIS TOOL with query='*', date_from='7d'\n"
                "  - 'what did we discuss about X?' → USE THIS TOOL with query='X'\n"
                "  - 'what did John say?' → USE THIS TOOL with query='', from_user='John'\n"
                "  - 'postgres issues last week' → USE THIS TOOL with query='postgres issues', date_from='7d'\n\n"
                "DON'T USE: Greetings ('hey'), general knowledge ('what is X?'), current events, questions ABOUT the KB feature\n\n"
                "Parameters:\n"
                "- query (required): CRITICAL LOGIC:\n"
                "  * Use '*' for ALL messages in time period (digests, summaries, overviews)\n"
                "  * Use keywords when searching FOR specific topic: 'postgres issues', 'API discussions'\n"
                "- from_user (optional): Filter by sender name\n"
                "- date_from (optional): '7d', '1m', or 'YYYY-MM-DD'. LEAVE EMPTY to search all history\n"
                "- date_to (optional): 'YYYY-MM-DD'. LEAVE EMPTY for current time\n"
                "- max_results (optional): 1-20, default 5 (but use 20+ for digests)\n\n"
                "CRITICAL: Only add date filters if user explicitly mentions time period.\n"
                "Call this tool EXACTLY ONCE - never duplicate.\n"
                "Write 1-2 intro sentences BEFORE calling.\n"
                "The tool will return formatted message cards with links.\n"
                "After calling: Write 2-3 sentence summary of what was found.\n"
                "If no results: Answer using your general knowledge instead."
            )
        ),
        Tool(
            list_recent_messages,
            name="list_recent_messages",
            description=(
                "List the 10 most recent messages without any filtering or date ranges.\n\n"
                "USE WHEN: User explicitly asks to 'list' or 'show' recent messages WITHOUT time period.\n"
                "Examples: 'list recent messages', 'show latest messages'\n\n"
                "❌ DON'T USE FOR:\n"
                "  - Digests ('last week digest') → use search_knowledge_base instead!\n"
                "  - Overviews with dates ('what happened last month') → use search_knowledge_base instead!\n"
                "  - Questions about the KB feature ('what's in the knowledge base?')\n"
                "  - Any request mentioning time periods → use search_knowledge_base instead!\n\n"
                "CRITICAL: Call EXACTLY ONCE - never duplicate.\n"
                "Write 1-2 intro sentences BEFORE calling.\n"
                "Returns: Simple chronological list of most recent messages with dates and senders."
            )
        ),
        Tool(
            get_knowledge_base_stats,
            name="get_knowledge_base_stats",
            description=(
                "Get comprehensive KB statistics with OPTIONAL advanced analytics.\n\n"
                "ALWAYS INCLUDED (basic stats):\n"
                "- Total messages and KB size\n"
                "- Active users count\n"
                "- Top contributors\n"
                "- Unanswered questions (if enabled)\n\n"
                "OPTIONAL ADVANCED ANALYTICS (set flags to true):\n"
                "- include_timeline: Daily message histogram showing activity over time\n"
                "- include_hourly_activity: Peak activity hours pattern\n"
                "- include_hashtags: Most frequently used hashtags\n"
                "- include_media_breakdown: Distribution of content types\n"
                "- include_user_engagement: User participation levels\n\n"
                "USE WHEN:\n"
                "- Basic: 'How much info is in KB?' 'Who's most active?' 'Show me stats'\n"
                "- Timeline: 'Show activity over time' 'When are people most active?'\n"
                "- Content: 'What topics are discussed?' 'What media is shared?'\n"
                "- Engagement: 'How many people contribute?' 'User participation levels?'\n"
                "- Questions: 'What questions are unanswered?' 'Show open questions'\n\n"
                "PARAMETERS:\n"
                "- date_from/date_to: Custom date range (default: last 7 days)\n"
                "- top_n: Number of top items (default: 5)\n"
                "- Various include_* flags for advanced stats\n\n"
                "Examples:\n"
                "- Basic: get_knowledge_base_stats()\n"
                "- Full analytics: get_knowledge_base_stats(include_timeline=True, include_hashtags=True, include_media_breakdown=True)\n"
                "- Custom period: get_knowledge_base_stats(date_from='2025-10-01', date_to='2025-10-31', include_timeline=True)"
            )
        )
    ]


def clear_kb_search_cache():
    """
    Clear the KB search cache.
    
    Should be called after each conversation turn completes to free memory
    and ensure fresh results for new queries.
    """
    global _kb_search_cache
    cache_size = len(_kb_search_cache)
    _kb_search_cache.clear()
    if cache_size > 0:
        logger.debug(f"🧹 Cleared KB search cache ({cache_size} entries)")


def get_prompt_description() -> str:
    """Return description for system prompt."""
    return """
**Knowledge Base Tools**

You have THREE tools for working with message history:

1. **search_knowledge_base** - Search with filters (ALWAYS use for digests/summaries/overviews!)
2. **list_recent_messages** - Simple list of 10 most recent messages (rarely needed)
3. **get_knowledge_base_stats** - Get KB statistics with optional advanced analytics (NEW!)

Your conversation history contains only the last 20 messages.
The knowledge base contains THOUSANDS of messages with full search capability.

**WHEN TO USE search_knowledge_base:**
✅ ALWAYS USE FOR ANY DIGEST, SUMMARY, OR OVERVIEW REQUEST!
- "digest for last 5 days" → query='*', date_from='5d'
- "what happened from 10-17 oct" → query='*', date_from='2025-10-10', date_to='2025-10-17'
- "make digest from group for last week" → query='*', date_from='7d'
- "what was discussed last month" → query='*', date_from='1m'
- Questions about specific topics: "what did we discuss about X?" → query='X'
- Looking for who said what: "what did John say?" → query='', from_user='John'
- Topic with timeframe: "postgres issues last week" → query='postgres issues', date_from='7d'

**WHEN TO USE get_knowledge_base_stats:**
- User asks about KB scope: "How much info is in the KB?" "How many messages?"
- User asks about activity: "Who's most active?" (in groups) "Show me activity"
- User asks about contributors: "Who talks the most here?"
- User asks for statistics: "Show me stats" "Give me KB stats"
- User asks about open questions: "What questions are unanswered?" "Show open questions"
- User wants activity patterns: "When are people most active?" (use include_hourly_activity=True)
- User wants content analysis: "What topics are discussed?" (use include_hashtags=True)
- When you need to understand the size/scope BEFORE searching

**WHEN TO USE list_recent_messages:**
- ONLY when user explicitly asks to "list" or "show" recent messages WITHOUT mentioning any time period
- Examples: "list recent messages", "show latest messages"
- This tool is RARELY needed!

**WHEN NOT TO USE TOOLS:**
- Greetings: "hey", "hello"
- General knowledge: "what is quantum computing?"
- Current facts not from chat history
- Questions ABOUT the KB feature: "what's in the knowledge base?" (explain descriptively, then optionally use get_knowledge_base_stats)

**CRITICAL RULES:**
1. Write 1-2 sentences BEFORE calling any tool (provide context)
2. Call each tool EXACTLY ONCE per query - NEVER duplicate calls
3. Leave date filters EMPTY unless user mentions time period
4. The tool will return formatted message cards - don't duplicate them in your response
5. After tool returns results, write 2-3 sentence summary of what was found
6. If tool returns empty, answer from your general knowledge
7. Never leave response empty - always be helpful

**CRITICAL QUERY LOGIC for search_knowledge_base:**
- Use query='*' when user wants ALL messages in time period (digests, summaries, overviews)
- Use query='keywords' when searching FOR specific topic
- For digests, use max_results=20 to get comprehensive results

**Example Flows:**

User: "Digest for last 5 days"
→ Write: "Let me get all messages from the past 5 days..."
→ Call: search_knowledge_base(query="*", date_from="5d", max_results=20)
→ Tool returns: Summary + formatted message cards
→ Write: "Here's what happened over the past 5 days - main topics were X, Y, Z..."

User: "What was discussed from 10 to 17 october?"
→ Write: "Let me retrieve all messages from that period..."
→ Call: search_knowledge_base(query="*", date_from="2025-10-10", date_to="2025-10-17", max_results=20)
→ Tool returns: Summary + formatted message cards
→ Write: "Found several discussions from Oct 10-17..."

User: "What did we discuss about postgres?"
→ Write: "Let me search for postgres discussions..."
→ Call: search_knowledge_base(query="postgres")
→ Tool returns: Formatted message cards
→ Write: "Found 3 discussions about PostgreSQL connection issues..."

User: "Last week digest"
→ Write: "Let me get all messages from last week..."
→ Call: search_knowledge_base(query="*", date_from="7d", max_results=20)
→ Tool returns: Summary + formatted message cards
→ Write: "Here's what happened last week - 15 messages covering X, Y, Z topics..."

User: "What's in the knowledge base?"
→ DON'T call tools - explain what KB is
→ Write: "The knowledge base stores all our conversations, messages, who said what and when..."

User: "List recent messages"
→ Write: "Here are your most recent messages..."
→ Call: list_recent_messages()
→ Tool returns: Simple list
→ No additional writing needed

User: "Hey"
→ Don't call tools - just greet: "Hey! How can I help?"

User: "What is PostgreSQL?"
→ Don't call tools - answer from general knowledge
"""
