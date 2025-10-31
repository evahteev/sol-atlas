"""
RAG (Retrieval Augmented Generation) Service for Luka Bot.

Provides prompt templates and workflows for answering questions using
retrieved context from the knowledge base.

Based on vpotoke_app/rag_search_kb/ but adapted for Luka's architecture.
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from luka_bot.core.config import settings


# ============================================================================
# Prompt Templates
# ============================================================================

def build_rag_answer_prompt(question: str, messages: List[Dict[str, Any]], language: str = "en") -> str:
    """
    Build a prompt for answering a question using retrieved messages as context.
    
    Args:
        question: User's question
        messages: List of retrieved message documents from ES
        language: Target language for the response (en, ru, etc.)
    
    Returns:
        Formatted prompt for the LLM
    """
    # Format messages for context
    formatted_messages = []
    for msg in messages:
        role = msg.get('role', 'unknown')
        sender = msg.get('sender_name', 'Unknown')
        text = msg.get('message_text', '')
        date = msg.get('message_date', '')
        
        # Role emoji
        role_emoji = {'user': '👤', 'assistant': '🤖', 'system': '⚙️'}.get(role, '💬')
        
        formatted_messages.append(
            f"{role_emoji} {sender} [{date[:10] if date else 'unknown'}]: {text}"
        )
    
    context = "\n".join(formatted_messages)
    
    # Language-specific instructions
    lang_instruction = {
        "en": "Provide your answer in English.",
        "ru": "Предоставьте ваш ответ на русском языке.",
    }.get(language, "Provide your answer in English.")
    
    prompt = f"""You are provided with a question and relevant messages from the user's conversation history.
These messages were retrieved from the knowledge base and may contain useful context to answer the question.

Your task:
1. Analyze the provided messages carefully
2. Answer the question using ONLY the information from these messages
3. If the messages don't contain enough information, say so honestly
4. Keep your answer concise (2-4 sentences)
5. {lang_instruction}

Question: {question}

Retrieved Messages:
{context}

Answer:"""
    
    return prompt


def build_rag_summary_prompt(messages: List[Dict[str, Any]], language: str = "en") -> str:
    """
    Build a prompt for summarizing a collection of messages.
    
    Args:
        messages: List of message documents from ES
        language: Target language for the summary (en, ru, etc.)
    
    Returns:
        Formatted prompt for the LLM
    """
    # Format messages for context
    formatted_messages = []
    for msg in messages:
        role = msg.get('role', 'unknown')
        sender = msg.get('sender_name', 'Unknown')
        text = msg.get('message_text', '')
        date = msg.get('message_date', '')
        
        role_emoji = {'user': '👤', 'assistant': '🤖', 'system': '⚙️'}.get(role, '💬')
        
        formatted_messages.append(
            f"{role_emoji} {sender} [{date[:10] if date else 'unknown'}]: {text}"
        )
    
    context = "\n".join(formatted_messages)
    
    # Language-specific instructions
    lang_instruction = {
        "en": "Provide your summary in English.",
        "ru": "Предоставьте ваше резюме на русском языке.",
    }.get(language, "Provide your summary in English.")
    
    prompt = f"""You are provided with a collection of messages from a conversation.

Your task:
1. Read through all the messages carefully
2. Create a concise summary (3-5 sentences) that captures:
   - Main topics discussed
   - Key decisions or conclusions
   - Important information shared
3. Use not only message text, but also metadata (authors, timestamps)
4. {lang_instruction}

Messages:
{context}

Summary:"""
    
    return prompt


def build_rag_topic_prompt(question: str, topics: List[Dict[str, Any]], language: str = "en") -> str:
    """
    Build a prompt for answering a question using topic summaries as context.
    
    Args:
        question: User's question
        topics: List of topic documents from ES
        language: Target language for the response (en, ru, etc.)
    
    Returns:
        Formatted prompt for the LLM
    """
    # Format topics for context
    formatted_topics = []
    for topic in topics:
        topic_name = topic.get('topic_name', 'Unknown Topic')
        summary = topic.get('summary', 'No summary available')
        keywords = topic.get('keywords', [])
        msg_count = topic.get('message_count', 0)
        
        keywords_str = ", ".join(keywords[:5]) if keywords else "none"
        
        formatted_topics.append(
            f"📌 {topic_name}\n"
            f"   Summary: {summary}\n"
            f"   Keywords: {keywords_str}\n"
            f"   Messages: {msg_count}"
        )
    
    context = "\n\n".join(formatted_topics)
    
    # Language-specific instructions
    lang_instruction = {
        "en": "Provide your answer in English.",
        "ru": "Предоставьте ваш ответ на русском языке.",
    }.get(language, "Provide your answer in English.")
    
    prompt = f"""You are provided with a question and relevant topics from the user's conversation history.
These topics were identified through clustering and may contain useful context to answer the question.

Your task:
1. Analyze the provided topic summaries and keywords
2. Answer the question using ONLY the information from these topics
3. If the topics don't contain enough information, say so honestly
4. Keep your answer concise (2-4 sentences)
5. {lang_instruction}

Question: {question}

Retrieved Topics:
{context}

Answer:"""
    
    return prompt


# ============================================================================
# RAG Workflows
# ============================================================================

async def rag_search_and_answer(
    question: str,
    index_name: str,
    search_method: str = "text",
    max_results: int = 5,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Complete RAG workflow: search KB and generate an answer using LLM.
    
    Args:
        question: User's question
        index_name: Elasticsearch index to search
        search_method: "text" (BM25), "vector" (k-NN), or "hybrid" (both)
        max_results: Maximum number of results to retrieve
        language: Target language for the response
    
    Returns:
        Dict with:
        - answer: LLM-generated answer
        - sources: List of source documents used
        - search_method: Method used for retrieval
        - num_sources: Number of sources found
    """
    try:
        logger.info(f"🔍 RAG workflow: question='{question[:50]}...', index={index_name}, method={search_method}")
        
        # Get Elasticsearch service
        es_service = await get_elasticsearch_service()
        
        # Step 1: Retrieve relevant messages
        if search_method == "text":
            results = await es_service.search_messages_text(
                index_name=index_name,
                query_text=question,
                min_score=settings.DEFAULT_MIN_SCORE,
                max_results=max_results
            )
        elif search_method == "vector":
            # Note: Requires embeddings to be generated first
            results = await es_service.search_messages_vector(
                index_name=index_name,
                query_text=question,
                min_score=settings.DEFAULT_MIN_SCORE,
                max_results=max_results
            )
        elif search_method == "hybrid":
            # Note: Requires embeddings to be generated first
            results = await es_service.search_messages_hybrid(
                index_name=index_name,
                query_text=question,
                min_score=settings.DEFAULT_MIN_SCORE,
                max_results=max_results
            )
        else:
            raise ValueError(f"Invalid search method: {search_method}")
        
        if not results:
            logger.warning(f"No results found for question: {question[:50]}...")
            return {
                "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                "sources": [],
                "search_method": search_method,
                "num_sources": 0
            }
        
        # Extract documents from results
        messages = [r['doc'] for r in results]
        
        logger.info(f"Retrieved {len(messages)} messages for RAG")
        
        # Step 2: Build RAG prompt
        prompt = build_rag_answer_prompt(question, messages, language)
        
        # Step 3: Generate answer using LLM
        # Note: This would typically use the LLM service, but for now we'll return
        # the prompt and sources. The actual LLM call should be done by the tool
        # that calls this function, as it has access to the agent.
        
        return {
            "prompt": prompt,  # Return prompt for LLM to process
            "sources": results,  # Original results with scores
            "search_method": search_method,
            "num_sources": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in RAG workflow: {e}", exc_info=True)
        return {
            "answer": f"I encountered an error while searching the knowledge base: {str(e)}",
            "sources": [],
            "search_method": search_method,
            "num_sources": 0
        }


async def rag_summarize_messages(
    index_name: str,
    filters: Optional[Dict[str, Any]] = None,
    max_messages: int = 50,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Retrieve messages and generate a summary.
    
    Args:
        index_name: Elasticsearch index to search
        filters: Optional filters (e.g., date range, sender, thread_id)
        max_messages: Maximum number of messages to summarize
        language: Target language for the summary
    
    Returns:
        Dict with:
        - prompt: LLM prompt for summarization
        - sources: List of source messages
        - num_sources: Number of messages included
    """
    try:
        logger.info(f"📝 RAG summarization: index={index_name}, max_messages={max_messages}")
        
        # Get Elasticsearch service
        es_service = await get_elasticsearch_service()
        
        # For now, use a wildcard query to get recent messages
        # In the future, this could be enhanced with filters
        results = await es_service.search_messages_text(
            index_name=index_name,
            query_text="*",  # Match all
            min_score=0.0,
            max_results=max_messages
        )
        
        if not results:
            logger.warning(f"No messages found in {index_name}")
            return {
                "prompt": None,
                "sources": [],
                "num_sources": 0
            }
        
        # Extract documents
        messages = [r['doc'] for r in results]
        
        logger.info(f"Retrieved {len(messages)} messages for summarization")
        
        # Build summary prompt
        prompt = build_rag_summary_prompt(messages, language)
        
        return {
            "prompt": prompt,
            "sources": results,
            "num_sources": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in RAG summarization: {e}", exc_info=True)
        return {
            "prompt": None,
            "sources": [],
            "num_sources": 0
        }


# ============================================================================
# Singleton
# ============================================================================

# Note: This service is stateless, so no singleton is needed.
# All functions are standalone and can be imported directly.
