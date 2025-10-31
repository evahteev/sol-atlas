"""
Conversation Summary Service - Manages conversation summaries for context-aware responses.

Features:
- Generates compact summaries of conversation history using LLM
- Updates summaries incrementally (every N messages)
- Provides summaries for context injection into KB search

Token Efficiency:
- Reduces context from ~2000 tokens (20 messages) to ~500 tokens (summary)
- 75% token reduction while maintaining conversation context
"""
from datetime import datetime
from typing import Optional
from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from luka_bot.models.thread import Thread


class ConversationSummaryService:
    """
    Manages conversation summaries for context-aware responses.
    
    Summaries are compact representations of conversation history that:
    - Cover main topics discussed
    - Include key questions and answers
    - Preserve important context
    - Stay under 500 tokens for efficiency
    
    Summaries are updated incrementally (every N messages) and stored in Thread model.
    """
    
    SUMMARY_INTERVAL = 10  # Update summary every 10 messages
    MAX_SUMMARY_TOKENS = 500  # Keep summaries compact
    MIN_MESSAGES_FOR_SUMMARY = 5  # Don't summarize conversations with <5 messages
    
    def __init__(self):
        """Initialize the conversation summary service."""
        pass
    
    def _format_messages_for_summary(self, messages: list[dict]) -> str:
        """
        Format message history for summary generation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Formatted conversation text
        """
        formatted = []
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                formatted.append(f"User: {content}")
            elif role == 'assistant':
                formatted.append(f"Assistant: {content}")
            elif role == 'system':
                # Skip system messages in summary
                continue
        
        return "\n".join(formatted)
    
    async def generate_summary(
        self, 
        user_id: int, 
        thread_id: str,
        recent_messages: list[dict]
    ) -> str:
        """
        Generate compact conversation summary using LLM.
        
        Args:
            user_id: User ID for logging
            thread_id: Thread ID for logging
            recent_messages: List of recent message dicts
            
        Returns:
            Compact summary (~200-500 tokens) of key discussion points
        """
        if len(recent_messages) < self.MIN_MESSAGES_FOR_SUMMARY:
            logger.info(f"📝 Skipping summary for thread {thread_id}: only {len(recent_messages)} messages")
            return ""
        
        try:
            # Format messages
            conversation_text = self._format_messages_for_summary(recent_messages)
            
            if not conversation_text.strip():
                logger.warning(f"📝 No content to summarize for thread {thread_id}")
                return ""
            
            # Create LLM model for summarization
            from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
            
            summary_model = await create_llm_model_with_fallback(
                context=f"summary_{user_id}",
                model_settings=ModelSettings(
                    temperature=0.3,  # Lower for factual summaries
                    max_tokens=self.MAX_SUMMARY_TOKENS
                )
            )
            
            # Create summary prompt
            summary_prompt = f"""Analyze this conversation and create a compact summary (max 400 tokens) covering:

1. **Main topics** discussed
2. **Key questions** asked by the user
3. **Important information** shared
4. **Current context** of the conversation
5. **Unresolved issues** or ongoing discussions

Be concise and factual. Focus on what would help understand future messages in context.
Use bullet points for clarity. Write in a natural, flowing style.

Conversation:
{conversation_text}

Summary:"""
            
            # Create summary agent
            summary_agent: Agent[None, str] = Agent(
                summary_model,
                system_prompt="You create concise, factual summaries of conversations. Focus on key topics, questions, and context.",
                retries=0
            )
            
            # Generate summary
            logger.info(f"📝 Generating summary for thread {thread_id}: {len(recent_messages)} messages")
            result = await summary_agent.run(summary_prompt)
            summary = result.output.strip()
            
            if not summary:
                logger.warning(f"📝 Empty summary generated for thread {thread_id}")
                return ""
            
            logger.info(f"📝 Summary generated for thread {thread_id}: {len(summary)} chars")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary for thread {thread_id}: {e}", exc_info=True)
            return ""
    
    async def should_update_summary(self, thread: Thread) -> bool:
        """
        Check if summary needs updating based on message count.
        
        Args:
            thread: Thread object with message count and summary info
            
        Returns:
            True if summary should be updated
        """
        # Check if we have enough messages
        if thread.message_count < self.MIN_MESSAGES_FOR_SUMMARY:
            return False
        
        # Check if we've never generated a summary
        if thread.summary_message_count == 0:
            return True
        
        # Check if enough new messages since last summary
        messages_since_summary = thread.message_count - thread.summary_message_count
        return messages_since_summary >= self.SUMMARY_INTERVAL
    
    async def update_summary_if_needed(
        self, 
        user_id: int, 
        thread: Thread
    ) -> Optional[str]:
        """
        Update summary if needed (called after each message).
        
        This method checks if summary needs updating based on message count,
        generates a new summary if needed, and updates the Thread object.
        
        Args:
            user_id: User ID
            thread: Thread object to potentially update
            
        Returns:
            New summary if updated, None otherwise
        """
        # Check if update is needed
        if not await self.should_update_summary(thread):
            return None
        
        try:
            # Load recent messages for summarization
            from luka_bot.services.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            # Load more messages for comprehensive summary
            recent_messages = await llm_service._get_history(
                user_id, 
                thread.thread_id, 
                max_messages=50  # Summarize more history
            )
            
            if not recent_messages:
                logger.info(f"📝 No messages found for summary update: thread {thread.thread_id}")
                return None
            
            # Generate new summary
            new_summary = await self.generate_summary(
                user_id, 
                thread.thread_id, 
                recent_messages
            )
            
            if not new_summary:
                logger.warning(f"📝 Failed to generate summary for thread {thread.thread_id}")
                return None
            
            # Update thread
            from luka_bot.services.thread_service import get_thread_service
            thread_service = get_thread_service()
            
            thread.conversation_summary = new_summary
            thread.summary_updated_at = datetime.utcnow()
            thread.summary_message_count = thread.message_count
            
            await thread_service.update_thread(thread)
            
            logger.info(f"📝 Updated conversation summary for thread {thread.thread_id}: {len(new_summary)} chars, {thread.message_count} messages")
            return new_summary
            
        except Exception as e:
            logger.error(f"Failed to update summary for thread {thread.thread_id}: {e}", exc_info=True)
            return None


# Singleton instance
_conversation_summary_service: Optional[ConversationSummaryService] = None


def get_conversation_summary_service() -> ConversationSummaryService:
    """Get or create the ConversationSummaryService singleton."""
    global _conversation_summary_service
    if _conversation_summary_service is None:
        _conversation_summary_service = ConversationSummaryService()
        logger.info("✅ ConversationSummaryService singleton created")
    return _conversation_summary_service

