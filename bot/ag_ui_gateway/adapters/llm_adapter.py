"""
LLM Adapter for AG-UI Protocol

Converts luka_bot LLM service responses to AG-UI protocol events.
Streams text as textStreamDelta events and handles tool executions.
"""
from typing import AsyncIterator, Optional, Dict, Any
import uuid
import time
from loguru import logger

# Lazy import to avoid circular dependencies
# from luka_bot.services.llm_service import LLMService


class AGUIProtocol:
    """
    CopilotKit protocol event types.
    
    Compatible with AG-UI Dojo frontend and CopilotKit.
    Uses uppercase event type names as expected by CopilotKit.
    """
    
    @staticmethod
    def text_message_start(message_id: str) -> Dict[str, Any]:
        """
        Create TEXT_MESSAGE_START event.
        
        Args:
            message_id: Unique message identifier
        
        Returns:
            CopilotKit protocol event
        """
        return {
            "type": "TEXT_MESSAGE_START",
            "messageId": message_id,
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def text_stream_delta(text: str, message_id: str) -> Dict[str, Any]:
        """
        Create TEXT_MESSAGE_CONTENT event (streaming text chunk).
        
        Args:
            text: Text chunk to stream
            message_id: Unique message identifier
        
        Returns:
            CopilotKit protocol event
        """
        return {
            "type": "TEXT_MESSAGE_CONTENT",
            "messageId": message_id,
            "delta": text,  # Field is "delta" not "content"
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def text_stream_complete(message_id: str, full_text: str) -> Dict[str, Any]:
        """
        Create TEXT_MESSAGE_END event.
        
        Args:
            message_id: Unique message identifier
            full_text: Complete message text
        
        Returns:
            CopilotKit protocol event
        """
        return {
            "type": "TEXT_MESSAGE_END",
            "messageId": message_id,
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def tool_invocation(tool_name: str, tool_args: Dict[str, Any], tool_id: str) -> Dict[str, Any]:
        """
        Create TOOL_CALL_START event.
        
        Args:
            tool_name: Name of the tool being invoked
            tool_args: Tool arguments
            tool_id: Unique tool invocation identifier
        
        Returns:
            CopilotKit protocol event
        """
        return {
            "type": "TOOL_CALL_START",
            "toolCallId": tool_id,
            "toolCallName": tool_name,  # CopilotKit expects toolCallName, not toolName
            "args": tool_args,
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def tool_result(tool_id: str, result: Any, message_id: str, success: bool = True) -> Dict[str, Any]:
        """
        Create TOOL_CALL_RESULT event.
        
        Args:
            tool_id: Unique tool invocation identifier
            result: Tool execution result
            message_id: Message identifier for the response
            success: Whether tool executed successfully
        
        Returns:
            CopilotKit protocol event
        """
        # CopilotKit expects messageId and content in tool results
        return {
            "type": "TOOL_CALL_RESULT",
            "toolCallId": tool_id,
            "messageId": message_id,  # Required by CopilotKit
            "content": str(result) if result else "",  # Required by CopilotKit
            "result": result,  # Keep for backwards compatibility
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def error(error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Create error event.
        
        Args:
            error_message: Error message
            error_code: Optional error code
        
        Returns:
            AG-UI protocol event
        """
        return {
            "type": "error",
            "message": error_message,
            "code": error_code or "INTERNAL_ERROR",
            "timestamp": int(time.time() * 1000)
        }


class LLMAdapter:
    """
    Adapter for streaming LLM responses as AG-UI protocol events.
    
    Wraps luka_bot's LLMService and converts output to AG-UI format.
    """
    
    def __init__(self):
        # Lazy initialization to avoid circular imports
        self._llm_service = None
    
    @property
    def llm_service(self):
        """Get LLM service (lazy loaded)."""
        if self._llm_service is None:
            from luka_bot.services.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    @staticmethod
    def _sanitize_markdown(text: str) -> str:
        """
        Normalize LLM output so it is Markdown-friendly and free of raw HTML.
        """
        if not text:
            return ""
        
        from html import unescape
        import re
        
        # Normalize common HTML tags to Markdown/newlines
        cleaned = text
        cleaned = cleaned.replace("\r\n", "\n")
        cleaned = re.sub(r"<\s*br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*/\s*p\s*>", "\n\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*p\s*>", "\n\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*(strong|b)\s*>", "**", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*/\s*(strong|b)\s*>", "**", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*(em|i)\s*>", "*", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*/\s*(em|i)\s*>", "*", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*(u)\s*>", "__", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<\s*/\s*(u)\s*>", "__", cleaned, flags=re.IGNORECASE)
        
        # Remove any remaining HTML tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        
        # Unescape HTML entities
        cleaned = unescape(cleaned)
        
        # Collapse excessive blank lines (max two consecutive newlines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        
        return cleaned
    
    async def _ensure_thread_with_kb(self, user_id: int, thread_id: str):
        """
        Ensure thread exists with KB indices for the user.
        
        If thread doesn't exist, creates it with user's KB index.
        If thread exists but has no KB indices, adds user's KB index.
        
        Args:
            user_id: User ID
            thread_id: Thread ID
        
        Returns:
            Thread object with KB indices
        """
        from luka_bot.services.thread_service import get_thread_service
        from luka_bot.services.user_profile_service import get_user_profile_service
        from luka_bot.models.thread import Thread
        
        thread_service = get_thread_service()
        profile_service = get_user_profile_service()
        
        # Try to get existing thread
        thread = await thread_service.get_thread(thread_id)
        
        # Get user's KB index
        user_kb_index = f"tg-kb-user-{user_id}"
        
        # Ensure profile has KB index set (especially for guest users)
        profile_kb_index = await profile_service.get_kb_index(user_id)
        if not profile_kb_index:
            logger.info(f"📚 Setting KB index for user {user_id} (first time): {user_kb_index}")
            await profile_service.set_kb_index(user_id, user_kb_index)
        
        # Get user's language preference
        user_lang = await profile_service.get_language(user_id) or "en"
        
        if not thread:
            # Create new thread with KB index
            logger.info(f"📝 Creating new thread {thread_id} for user {user_id} with KB index {user_kb_index}")
            thread = Thread(
                thread_id=thread_id,
                owner_id=user_id,
                name=f"Conversation {thread_id[:8]}",
                thread_type="dm",
                language=user_lang,
                knowledge_bases=[user_kb_index],
                enabled_tools=["knowledge_base", "support", "youtube"]
            )
            await thread_service._save_thread(thread)
            
            # Note: Elasticsearch index will be auto-created when first message is indexed
            # KB searches on empty index will return "no results" (expected behavior)
        elif not thread.knowledge_bases or user_kb_index not in thread.knowledge_bases:
            # Thread exists but missing KB index - add it
            logger.info(f"📝 Adding KB index {user_kb_index} to existing thread {thread_id}")
            if not thread.knowledge_bases:
                thread.knowledge_bases = [user_kb_index]
            else:
                thread.knowledge_bases.append(user_kb_index)
            await thread_service.update_thread(thread)
        
        logger.debug(f"✅ Thread {thread_id} ready with KB indices: {thread.knowledge_bases}")
        return thread
    
    async def stream_response(
        self,
        user_message: str,
        user_id: int,
        thread_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream LLM response as AG-UI protocol events.
        
        Args:
            user_message: User's message text
            user_id: User ID (telegram_user_id)
            thread_id: Optional thread/conversation ID
            session_context: Optional session context with thread settings
        
        Yields:
            AG-UI protocol events (textStreamDelta, toolInvocation, toolResult, etc.)
        """
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        full_response = ""
        
        try:
            logger.info(f"🤖 LLM stream started: user={user_id}, thread={thread_id}")
            
            # Emit TEXT_MESSAGE_START event first
            yield AGUIProtocol.text_message_start(message_id)
            
            # Extract thread configuration from session context if available
            thread = session_context.get("thread") if session_context else None
            
            # If no thread object exists, ensure thread is created with KB indices
            if not thread and thread_id:
                thread = await self._ensure_thread_with_kb(user_id, thread_id)
            
            # Stream response from luka_bot LLM service
            logger.debug(f"🔍 About to call llm_service.stream_response()")
            logger.debug(f"   user_id={user_id}, thread_id={thread_id}, has_thread={thread is not None}")
            
            chunk_count = 0
            try:
                async for chunk in self.llm_service.stream_response(
                    user_message=user_message,
                    user_id=user_id,
                    thread_id=thread_id,
                    thread=thread,
                    save_history=True
                ):
                    chunk_count += 1
                    if chunk_count == 1:
                        logger.debug(f"✅ First chunk received from llm_service!")
                    elif chunk_count % 10 == 0:
                        logger.debug(f"📊 Received {chunk_count} chunks so far...")
                    
                    # Check if chunk is a tool notification (dict with type)
                    if isinstance(chunk, dict) and chunk.get("type") == "tool_notification":
                        # Convert tool notification to AG-UI format
                        tool_name = chunk.get("tool_name", "unknown")
                        tool_id = f"tool_{uuid.uuid4().hex[:8]}"
                        
                        # Emit tool invocation
                        yield AGUIProtocol.tool_invocation(
                            tool_name=tool_name,
                            tool_args={},
                            tool_id=tool_id
                        )
                        
                        # Optionally emit a visual indicator (emoji) as text
                        emoji = chunk.get("text", "")
                        if emoji:
                            yield AGUIProtocol.text_stream_delta(
                                text=emoji,
                                message_id=message_id
                            )
                            full_response += emoji
                        
                        # Emit tool result (immediate for now)
                        yield AGUIProtocol.tool_result(
                            tool_id=tool_id,
                            result={"status": "executed"},
                            message_id=message_id,
                            success=True
                        )
                    
                    # Regular text chunk
                    elif isinstance(chunk, str):
                        if chunk:
                            sanitized_chunk = self._sanitize_markdown(chunk)
                            if sanitized_chunk:
                                logger.debug(f"📤 Yielding text chunk: {len(sanitized_chunk)} chars - '{sanitized_chunk[:100]}...'")
                                # Emit text stream delta with sanitized Markdown
                                yield AGUIProtocol.text_stream_delta(
                                    text=sanitized_chunk,
                                    message_id=message_id
                                )
                                full_response += sanitized_chunk
                            else:
                                logger.debug("⚠️  Sanitized chunk became empty after removing HTML, skipping")
                        else:
                            logger.debug("⚠️  Received empty string chunk, skipping")
                    else:
                        logger.warning(f"⚠️  Received unknown chunk type: {type(chunk)}")
                
                logger.debug(f"✅ llm_service.stream_response() completed, total chunks: {chunk_count}")
                
            except Exception as llm_error:
                logger.error(f"❌ FATAL ERROR in llm_service.stream_response(): {llm_error}", exc_info=True)
                logger.error(f"   Error type: {type(llm_error).__name__}")
                logger.error(f"   Error occurred after {chunk_count} chunks")
                raise  # Re-raise so upstream handler can deal with it
            
            # Emit completion event
            yield AGUIProtocol.text_stream_complete(
                message_id=message_id,
                full_text=full_response
            )
            
            logger.info(f"✅ LLM stream complete: {len(full_response)} chars")
            
        except Exception as e:
            logger.error(f"❌ LLM streaming error: {e}")
            yield AGUIProtocol.error(
                error_message=str(e),
                error_code="LLM_ERROR"
            )
    
    async def generate_response(
        self,
        user_message: str,
        user_id: int,
        thread_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate complete LLM response (non-streaming).
        
        Args:
            user_message: User's message text
            user_id: User ID (telegram_user_id)
            thread_id: Optional thread/conversation ID
            session_context: Optional session context with thread settings
        
        Returns:
            Complete response text
        """
        full_response = ""
        
        try:
            # Ensure thread exists with KB indices
            thread = session_context.get("thread") if session_context else None
            if not thread and thread_id:
                thread = await self._ensure_thread_with_kb(user_id, thread_id)
            
            async for chunk in self.llm_service.stream_response(
                user_message=user_message,
                user_id=user_id,
                thread_id=thread_id,
                thread=thread,
                save_history=True
            ):
                # Accumulate text chunks only (ignore tool notifications)
                if isinstance(chunk, str):
                    full_response += chunk
            
            return full_response
            
        except Exception as e:
            logger.error(f"❌ LLM generation error: {e}")
            raise


# Singleton instance
_llm_adapter: Optional[LLMAdapter] = None


def get_llm_adapter() -> LLMAdapter:
    """Get or create LLMAdapter singleton."""
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter()
        logger.info("✅ LLMAdapter singleton created")
    return _llm_adapter
