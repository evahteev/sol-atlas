"""
AG-UI Protocol Agent Endpoint

This module provides an HTTP streaming endpoint compatible with the AG-UI protocol
and dojo frontend. It wraps existing adapters (LLM, Task, Catalog, Command) to provide
Server-Sent Events (SSE) streaming.
"""

import time
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from loguru import logger

try:
    from ag_ui.core.types import RunAgentInput as AGUIRunAgentInput, UserMessage
    from ag_ui.encoder import EventEncoder
    HAS_AG_UI = True
except ImportError:
    logger.warning("ag-ui package not installed. Install with: pip install ag-ui-protocol")
    HAS_AG_UI = False
    AGUIRunAgentInput = None
    UserMessage = None

# Always use our simplified input type for easier API
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

class SimpleMessage(BaseModel):
    """Simplified message format."""
    role: str = "user"
    content: str
    id: Optional[str] = None

class RunAgentInput(BaseModel):
    """
    Simplified input for Luka agent.
    
    This is much simpler than the full AG-UI RunAgentInput.
    Supports both regular agent calls and CopilotKit GraphQL operations.
    """
    messages: Optional[List[SimpleMessage]] = None  # Optional for GraphQL operations
    user_id: Optional[str] = "guest"
    thread_id: Optional[str] = "default"
    agent: Optional[str] = "luka"
    
    # Password authentication (when LUKA_PASSWORD_ENABLED=true)
    password: Optional[str] = None
    password_authenticated: Optional[bool] = None  # Set by endpoint after validation
    session_token: Optional[str] = None
    
    # CopilotKit GraphQL support
    operationName: Optional[str] = None
    query: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None

class EventEncoder:
    """Simple event encoder for SSE streaming."""
    
    def __init__(self, accept: Optional[str] = None):
        # Always use SSE format for streaming responses
        self.format = "sse"
    
    def encode(self, event: Dict[str, Any]) -> str:
        """Encode event in SSE format with proper data: prefix and double newlines."""
        # Ensure we always return SSE format for streaming
        return f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
    
    def get_content_type(self) -> str:
        return "text/event-stream"

from ag_ui_gateway.adapters.llm_adapter import get_llm_adapter
from ag_ui_gateway.adapters.task_adapter import get_task_adapter
from ag_ui_gateway.adapters.catalog_adapter import get_catalog_adapter
from ag_ui_gateway.adapters.command_adapter import get_command_adapter
from ag_ui_gateway.services.ui_events import build_task_list_event, build_ui_context_event

router = APIRouter()


class LukaAgent:
    """
    Luka Bot agent wrapper for AG-UI protocol.
    
    This class wraps existing adapters to provide an AG-UI compatible interface
    for the dojo frontend and other AG-UI clients.
    
    Features:
    - Agentic chat with LLM streaming
    - Human-in-the-loop task management
    - Backend tool rendering
    - Catalog/KB search
    - Command execution with BPMN workflows
    """
    
    def __init__(self):
        self.name = "luka"
        self.description = "Community Knowledge Assistant with BPMN workflows"
        self.llm_adapter = get_llm_adapter()
        self.task_adapter = get_task_adapter()
        self.catalog_adapter = get_catalog_adapter()
        self.command_adapter = get_command_adapter()
        logger.info(f"Initialized {self.name} agent")

    def _resolve_user_id(self, user_id: Optional[str]) -> tuple[int, bool]:
        """
        Convert incoming user id string into numeric identifier.

        Returns:
            (numeric_id, is_guest)
        """
        if not user_id or user_id == "guest":
            return 0, True

        try:
            if str(user_id).isdigit():
                return int(user_id), False
            numeric = int(str(user_id))
            return numeric, False
        except (TypeError, ValueError):
            hashed = hash(str(user_id)) % (10 ** 8)
            return hashed, False

    def _command_to_mode(self, command: str) -> str:
        mapping = {
            "start": "start",
            "chat": "chat",
            "tasks": "tasks",
            "profile": "profile",
            "groups": "groups",
            "catalog": "catalog",
        }
        return mapping.get(command.lower(), "chat")

    async def _build_ui_context_event(
        self,
        user_id_int: int,
        is_guest: bool,
        active_mode: str,
    ) -> Optional[Dict[str, Any]]:
        return await build_ui_context_event(
            user_id=user_id_int if user_id_int > 0 else None,
            active_mode=active_mode,
            is_guest=is_guest,
        )

    async def _build_task_list_event(
        self,
        user_id_int: int,
        active_mode: str,
    ) -> Optional[Dict[str, Any]]:
        force = active_mode in {"start", "tasks"}
        return await build_task_list_event(
            user_id=user_id_int if user_id_int > 0 else None,
            source="chatbot_start",
            force=force,
        )
    
    async def run(self, input_data: RunAgentInput) -> AsyncGenerator:
        """
        Run the agent and yield AG-UI protocol events.
        
        This is the main entry point called by the dojo frontend.
        It processes user messages and yields streaming events.
        
        Args:
            input_data: Simplified RunAgentInput with messages, user_id, thread_id
            
        Yields:
            CopilotKit protocol events (RUN_STARTED, TEXT_MESSAGE_*, TOOL_CALL_*, etc.)
        """
        user_id = input_data.user_id
        thread_id = input_data.thread_id
        messages = input_data.messages
        
        # Emit RUN_STARTED first (required by CopilotKit)
        run_id = f"run_{int(time.time()*1000)}"
        logger.debug(f"🎬 agent.run() starting: run_id={run_id}, messages={len(messages) if messages else 0}")
        
        yield {
            "type": "RUN_STARTED",
            "runId": run_id,
            "threadId": thread_id,  # Required by CopilotKit
            "timestamp": int(time.time() * 1000)
        }
        
        logger.debug(f"✅ Yielded RUN_STARTED for {run_id}")

        user_id_int, is_guest = self._resolve_user_id(user_id)

        if not messages:
            logger.warning("No messages in input")
            context_event = await self._build_ui_context_event(
                user_id_int=user_id_int,
                is_guest=is_guest,
                active_mode="start",
            )
            if context_event:
                yield context_event
            yield {
                "type": "RUN_FINISHED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": int(time.time() * 1000)
            }
            return
        
        # Filter out empty assistant messages (placeholder messages from frontend)
        filtered_messages = [msg for msg in messages if not (
            hasattr(msg, 'role') and msg.role == 'assistant' and 
            hasattr(msg, 'content') and not msg.content
        )]
        
        logger.debug(f"📊 Filtered messages: {len(messages)} -> {len(filtered_messages)}")
        
        if not filtered_messages:
            logger.warning("All messages were empty placeholders")
            context_event = await self._build_ui_context_event(
                user_id_int=user_id_int,
                is_guest=is_guest,
                active_mode="chat",
            )
            if context_event:
                yield context_event
            yield {
                "type": "RUN_FINISHED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": int(time.time() * 1000)
            }
            return
        
        # Get last user message
        last_message = filtered_messages[-1]
        message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        logger.info(f"Processing message for user {user_id}, thread {thread_id}: {message_content[:50]}...")
        logger.debug(f"📝 Full message: role={getattr(last_message, 'role', 'unknown')}, content={message_content}")
        
        def _build_text_events(text: str, role: str = "assistant"):
            message_id = f"msg_{int(time.time()*1000)}"
            timestamp = int(time.time() * 1000)
            return [
                {
                    "type": "TEXT_MESSAGE_START",
                    "messageId": message_id,
                    "role": role,
                    "timestamp": timestamp
                },
                {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": message_id,
                    "delta": text,
                    "timestamp": int(time.time() * 1000)
                },
                {
                    "type": "TEXT_MESSAGE_END",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                },
            ]
        
        try:
            if not input_data.password_authenticated:
                logger.info(f"🔐 Password authentication required for user {user_id}")

                from luka_bot.core.config import settings as luka_settings

                prompt_sent = any(
                    getattr(msg, "role", "") == "assistant"
                    and "password-protected" in (getattr(msg, "content", "") or "")
                    for msg in filtered_messages
                )

                provided_password = None
                if input_data.password:
                    provided_password = input_data.password.strip()
                elif prompt_sent and getattr(last_message, "role", "") == "user":
                    provided_password = message_content.strip()

                if provided_password and provided_password == luka_settings.LUKA_PASSWORD:
                    logger.info(f"✅ Password authentication successful for user {user_id_int}")
                    input_data.password_authenticated = True

                    session_token = getattr(input_data, "session_token", None)
                    if session_token:
                        try:
                            from ag_ui_gateway.middleware.password import verify_password_for_session, PasswordAuthError
                            await verify_password_for_session(session_token, provided_password, user_id_int)
                            logger.info(f"🔐 Session token authenticated for user {user_id_int}")
                        except PasswordAuthError:
                            logger.warning("⚠️  Session token authentication failed despite correct password")
                        except Exception as e:
                            logger.error(f"❌ Error storing password authentication state: {e}")

                    for event in _build_text_events("Password accepted. How can I help you?"):
                        yield event
                    yield {
                        "type": "RUN_FINISHED",
                        "runId": run_id,
                        "threadId": thread_id,
                        "timestamp": int(time.time() * 1000)
                    }
                    return

                if provided_password and provided_password != luka_settings.LUKA_PASSWORD:
                    logger.warning(f"❌ Password attempt failed for user {user_id_int}")
                    for event in _build_text_events("Incorrect password. Please try again."):
                        yield event
                    yield {
                        "type": "RUN_FINISHED",
                        "runId": run_id,
                        "threadId": thread_id,
                        "timestamp": int(time.time() * 1000)
                    }
                    return

                for event in _build_text_events("This bot is password-protected. Please provide the password to continue."):
                    yield event
                yield {
                    "type": "RUN_FINISHED",
                    "runId": run_id,
                    "threadId": thread_id,
                    "timestamp": int(time.time() * 1000)
                }
                return

            is_command = message_content.startswith("/")
            command_name = None
            if is_command:
                command_name = message_content.split()[0].split("@", 1)[0].lstrip("/")

            active_mode = self._command_to_mode(command_name or "")
            ui_context_event = await self._build_ui_context_event(
                user_id_int=user_id_int,
                is_guest=is_guest,
                active_mode=active_mode if is_command else "chat",
            )
            if ui_context_event:
                yield ui_context_event

            if is_command and command_name:
                logger.debug(f"🔧 Handling command: {message_content}")
                async for event in self._handle_command(
                    raw_command=message_content,
                    user_id_int=user_id_int,
                    is_guest=is_guest,
                    thread_id=thread_id,
                ):
                    logger.debug(f"   → Yielding command event: {event.get('type')}")
                    yield event
            else:
                logger.debug("💬 Handling chat message via LLM adapter")
                event_count = 0
                async for event in self._handle_chat(
                    message=message_content,
                    user_id_int=user_id_int,
                    is_guest=is_guest,
                    thread_id=thread_id,
                    raw_user_id=user_id,
                ):
                    event_count += 1
                    event_type = event.get('type') if isinstance(event, dict) else type(event).__name__
                    logger.debug(f"   → Yielding LLM event #{event_count}: {event_type}")
                    yield event
                logger.debug(f"✅ LLM adapter yielded {event_count} events total")

            task_list_event = await self._build_task_list_event(
                user_id_int=user_id_int,
                active_mode=active_mode if is_command else "chat",
            )
            if task_list_event:
                logger.debug("   → Yielding taskList event")
                yield task_list_event
            
            # Emit RUN_FINISHED at the end (required by CopilotKit)
            yield {
                "type": "RUN_FINISHED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": int(time.time() * 1000)
            }
                
        except Exception as e:
            logger.error(f"Error in agent.run: {e}", exc_info=True)
            # Yield error event
            yield {
                "type": "RUN_ERROR",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
            # Still emit RUN_FINISHED even on error
            yield {
                "type": "RUN_FINISHED",
                "runId": run_id,
                "threadId": thread_id,
                "timestamp": int(time.time() * 1000)
            }
    
    async def _handle_chat(
        self,
        message: str,
        user_id_int: int,
        is_guest: bool,
        thread_id: Optional[str],
        raw_user_id: Optional[str] = None,
    ):
        """
        Handle regular chat message with LLM streaming.
        
        This uses the existing LLM adapter which already emits AG-UI events:
        - textStreamStart
        - textStreamDelta (multiple)
        - textStreamComplete
        - toolInvocation (if tools are called)
        - toolResult (when tools complete)
        """
        effective_user_id = user_id_int

        if is_guest:
            effective_user_id = 0
            try:
                logger.info("🧹 Clearing guest user cache to ensure fresh state...")
                from luka_bot.core.loader import redis_client

                guest_keys = [
                    "llm_provider_preferred:user_0",
                    "user_profile:0",
                    "user_session:0",
                    "camunda_user_mapping:0",
                    "llm_history:0",
                ]
                if thread_id:
                    guest_keys.append(f"thread_history:{thread_id}")

                cleared_count = 0
                for key in guest_keys:
                    result = await redis_client.delete(key)
                    if result:
                        cleared_count += 1
                        logger.debug(f"   🗑️  Cleared: {key}")

                logger.info(f"✅ Cleared {cleared_count} guest cache keys")
            except Exception as cache_error:
                logger.warning(f"⚠️  Failed to clear guest cache (non-critical): {cache_error}")

        async for event in self.llm_adapter.stream_response(
            user_message=message,  # Correct parameter name
            user_id=effective_user_id,
            thread_id=thread_id,
            session_context=None
        ):
            yield event
    
    async def _handle_command(
        self,
        raw_command: str,
        user_id_int: int,
        is_guest: bool,
        thread_id: Optional[str] = None,
    ):
        """
        Handle command execution (commands starting with /).
        
        Examples:
        - /search <query> - Search knowledge base
        - /tasks - List active tasks
        - /clear - Clear conversation context
        - /help - Show available commands
        """
        try:
            # Parse command and parameters
            parts = raw_command.strip().split(maxsplit=1)
            cmd_name = parts[0].lstrip("/")  # Remove leading /
            cmd_params = parts[1] if len(parts) > 1 else ""

            # Generate message ID
            message_id = f"cmd_{int(time.time()*1000)}"
            
            # Handle /clear command specially (client-side operation)
            if cmd_name == "clear":
                logger.info(f"🧹 Clearing conversation context for user {user_id_int}, thread {thread_id}")
                
                # Note: History clearing is handled client-side or in-memory
                # Database integration can be added later when database module is available
                success_message = "✅ Conversation cleared! Starting fresh."
                
                # Yield success response
                yield {
                    "type": "TEXT_MESSAGE_START",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                }
                
                yield {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": message_id,
                    "delta": success_message,
                    "timestamp": int(time.time() * 1000)
                }
                
                yield {
                    "type": "TEXT_MESSAGE_END",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                }
                return
            
            # Handle other commands via CommandAdapter
            # Build parameters dict based on command
            parameters = {}
            if cmd_params:
                if cmd_name == "search":
                    parameters = {"query": cmd_params}
                else:
                    parameters = {"text": cmd_params}

            result = await self.command_adapter.execute_command(
                command=cmd_name,
                parameters=parameters,
                user_id=user_id_int,
                is_guest=is_guest or user_id_int == 0
            )
            
            # Check if result is a form request
            if result.get("type") == "formRequest":
                # Yield the form request directly
                yield result
            elif result.get("type") == "stateUpdate":
                # Yield state update directly
                yield result
            elif result.get("type") == "commandResult":
                # Extract and yield the command result message
                yield {
                    "type": "TEXT_MESSAGE_START",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                }
                
                yield {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": message_id,
                    "delta": result.get("message", "Command executed"),
                    "timestamp": int(time.time() * 1000)
                }
                
                yield {
                    "type": "TEXT_MESSAGE_END",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                }
            else:
                # Default: yield as text message
                yield {
                    "type": "TEXT_MESSAGE_START",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                }
                
                yield {
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": message_id,
                    "delta": result.get("message", "Command executed"),
                    "timestamp": int(time.time() * 1000)
                }
                
                yield {
                    "type": "TEXT_MESSAGE_END",
                    "messageId": message_id,
                    "timestamp": int(time.time() * 1000)
                }
            
        except Exception as e:
            logger.error(f"Error executing command {command}: {e}")
            message_id = f"cmd_error_{int(time.time()*1000)}"
            
            yield {
                "type": "TEXT_MESSAGE_START",
                "messageId": message_id,
                "timestamp": int(time.time() * 1000)
            }
            
            yield {
                "type": "TEXT_MESSAGE_CONTENT",
                "messageId": message_id,
                "delta": f"Error executing command: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
            
            yield {
                "type": "TEXT_MESSAGE_END",
                "messageId": message_id,
                "timestamp": int(time.time() * 1000)
            }
    
# Create singleton agent instance
_luka_agent = None

def get_luka_agent() -> LukaAgent:
    """Get or create the Luka agent singleton."""
    global _luka_agent
    if _luka_agent is None:
        _luka_agent = LukaAgent()
    return _luka_agent


@router.post("/agent/luka")
@router.post("/copilotkit/luka")  # CopilotKit-compatible alias
async def luka_agent_endpoint(input_data: RunAgentInput, request: Request, feature: str = "agentic_chat"):
    """
    Luka Bot agent endpoint compatible with AG-UI protocol.
    
    This endpoint provides HTTP streaming (Server-Sent Events) for the dojo
    frontend and other AG-UI clients. It wraps the existing websocket/chat
    logic to provide the same functionality over HTTP.
    
    Available at:
    - POST /api/agent/luka (primary path)
    - POST /api/copilotkit/luka (CopilotKit alias)
    
    Supports:
    - Regular agent calls with messages
    - CopilotKit GraphQL operations (loadAgentState, etc.)
    
    Request format:
    ```json
    {
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "userId": "user123",
        "threadId": "thread456",
        "password": "optional_password"  // Required if LUKA_PASSWORD_ENABLED=true
    }
    ```
    
    Response: Server-Sent Events stream
    ```
    data: {"type":"textStreamStart","messageId":"...","timestamp":...}
    
    data: {"type":"textStreamDelta","messageId":"...","delta":"Hello","timestamp":...}
    
    data: {"type":"textStreamComplete","messageId":"...","timestamp":...}
    ```
    """
    # Extract and validate token from Authorization header
    token = None
    user_context = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        
        # Validate token to get user context
        from ag_ui_gateway.auth.tokens import get_token_manager
        token_manager = get_token_manager()
        user_context = await token_manager.validate_token(token)
        
        if not user_context:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={
                    'error': 'invalid_token',
                    'message': 'Invalid or expired token. Please authenticate again.',
                    'hint': 'Get a new token from /api/auth/guest or /api/auth/telegram-miniapp'
                }
            )
        
        # Extract user context for logging
        effective_user_id = user_context.get('user_id')
        token_type = user_context.get('token_type', 'unknown')
        
        # For guest users, use "guest" as user_id (as expected by the agent)
        if token_type == 'guest':
            effective_user_id = "guest"
        
        # Check password authentication (if enabled) - but don't block the request
        # Instead, let the LLM handle password requests naturally through conversation
        from ag_ui_gateway.middleware.password import verify_password_for_session, PasswordAuthError
        from luka_bot.core.config import settings as luka_settings
        
        password_authenticated = False
        if luka_settings.LUKA_PASSWORD_ENABLED and luka_settings.LUKA_PASSWORD:
            try:
                await verify_password_for_session(token, input_data.password, effective_user_id)
                password_authenticated = True
                logger.info(f"✅ Password authentication successful for user {effective_user_id}")
            except PasswordAuthError as e:
                # Don't block the request - let the LLM handle password requests
                password_authenticated = False
                logger.info(f"🔐 Password authentication pending for user {effective_user_id}: {str(e)}")
        else:
            password_authenticated = True  # No password protection enabled
    else:
        # No token provided
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={
                'error': 'token_required',
                'message': 'Authorization token required. Use Bearer token in Authorization header.',
                'hint': 'Get a token from /api/auth/guest or /api/auth/telegram-miniapp'
            }
        )
    # Handle CopilotKit GraphQL operations
    if input_data.operationName:
        from fastapi.responses import JSONResponse
        
        logger.info(f"📊 GraphQL Operation: {input_data.operationName}")
        logger.debug(f"   Query: {input_data.query[:100] if input_data.query else 'None'}...")
        logger.debug(f"   Variables: {input_data.variables}")
        
        if input_data.operationName == "loadAgentState":
            # Extract threadId from variables
            thread_id = None
            if input_data.variables and "data" in input_data.variables:
                thread_id = input_data.variables["data"].get("threadId")
            
            logger.info(f"✅ CopilotKit loadAgentState: thread={thread_id}")
            
            # Return empty state for now (thread history can be implemented later)
            return JSONResponse({
                "data": {
                    "loadAgentState": {
                        "threadId": thread_id or input_data.thread_id,
                        "threadExists": False,  # No persistent thread storage yet
                        "state": {},
                        "messages": [],
                        "__typename": "AgentState"
                    }
                }
            })
        
        elif input_data.operationName == "availableAgents":
            logger.info(f"✅ CopilotKit availableAgents query")
            
            # Return available agents for this integration
            return JSONResponse({
                "data": {
                    "availableAgents": {
                        "agents": [
                            {
                                "id": "luka",
                                "name": "luka",
                                "description": "Community Knowledge Assistant with BPMN workflows and task management",
                                "__typename": "Agent"
                            }
                        ],
                        "__typename": "AvailableAgents"
                    }
                }
            })
        
        elif input_data.operationName == "generateCopilotResponse":
            logger.info(f"✅ CopilotKit generateCopilotResponse: Converting to agent run")
            
            # Extract messages from variables
            messages_data = []
            if input_data.variables and "data" in input_data.variables:
                data = input_data.variables["data"]
                messages_data = data.get("messages", [])
                input_data.thread_id = data.get("threadId", input_data.thread_id)
                input_data.user_id = data.get("userId", input_data.user_id)
            
            # Convert to agent input format
            # CopilotKit messages have nested structure: msg.textMessage.content
            converted_messages = []
            for msg in messages_data:
                # Extract content from nested textMessage structure
                text_msg = msg.get("textMessage", {})
                role = text_msg.get("role", "user")
                content = text_msg.get("content", "")
                msg_id = msg.get("id")
                
                converted_messages.append(
                    SimpleMessage(
                        role=role,
                        content=content,
                        id=msg_id
                    )
                )
                logger.debug(f"   Converted message: role={role}, content_len={len(content)}, id={msg_id}")
            
            input_data.messages = converted_messages
            
            # Fall through to regular agent processing below
            logger.info(f"✅ Converted GraphQL to agent input: {len(input_data.messages)} messages")
        
        # Add handlers for additional CopilotKit operations
        elif input_data.operationName in ["saveAgentState", "updateAgentState"]:
            logger.info(f"✅ CopilotKit {input_data.operationName}: State persistence (no-op for now)")
            # For now, just acknowledge the save
            return JSONResponse({
                "data": {
                    input_data.operationName: {
                        "success": True,
                        "__typename": "AgentStateMutation"
                    }
                }
            })
        
        elif input_data.operationName == "listThreads":
            logger.info(f"✅ CopilotKit listThreads: Returning empty list")
            # For now, return empty thread list
            return JSONResponse({
                "data": {
                    "listThreads": {
                        "threads": [],
                        "__typename": "ThreadList"
                    }
                }
            })
        
        else:
            logger.error(f"❌ Unknown CopilotKit operation: {input_data.operationName}")
            logger.error(f"   Full request: operationName={input_data.operationName}, variables={input_data.variables}")
            return JSONResponse({
                "errors": [{
                    "message": f"Unknown operation: {input_data.operationName}",
                    "extensions": {
                        "code": "UNKNOWN_OPERATION",
                        "operationName": input_data.operationName
                    }
                }]
            }, status_code=400)
    
    # Regular agent message handling
    message_count = len(input_data.messages) if input_data.messages else 0
    
    # Override input_data.user_id with validated user context
    if effective_user_id:
        input_data.user_id = effective_user_id
    
    # Add password authentication status to input data for LLM handling
    input_data.password_authenticated = password_authenticated
    
    logger.info(f"Agent request: feature={feature}, user={effective_user_id}, type={token_type}, thread={input_data.thread_id}, messages={message_count}, password_auth={password_authenticated}")
    
    # Preserve session token for downstream password updates
    input_data.session_token = token
    
    # Check guest message limits
    if token_type == 'guest':
        message_count = user_context.get('message_count', 0)
        from ag_ui_gateway.config.settings import settings
        if message_count >= settings.GUEST_TOTAL_MESSAGES:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    'error': 'guest_limit_exceeded',
                    'message': f'Guest message limit ({settings.GUEST_TOTAL_MESSAGES}) reached. Please sign in for unlimited messages.',
                    'upgrade_url': '/api/auth/telegram-miniapp',
                    'current_count': message_count,
                    'limit': settings.GUEST_TOTAL_MESSAGES
                }
            )
    
    # Get the accept header
    accept_header = request.headers.get("accept", "application/json")
    
    # Create encoder
    encoder = EventEncoder(accept=accept_header)
    
    # Get agent
    agent = get_luka_agent()
    
    async def event_generator():
        """
        Generate SSE events from agent with graceful error handling.
        
        Ensures the frontend always receives proper stream termination:
        - Tracks run state (started, finished)
        - Sends RUN_FINISHED if stream is interrupted
        - Always properly encodes events as SSE
        """
        run_started = False
        run_finished = False
        run_id = None
        
        try:
            event_num = 0
            async for event in agent.run(input_data):
                event_num += 1
                event_type = event.get("type") if isinstance(event, dict) else "unknown"
                
                # Track run state to ensure proper cleanup
                if event.get("type") == "RUN_STARTED":
                    run_started = True
                    run_id = event.get("runId")
                    logger.debug(f"🚀 Run started: {run_id}")
                elif event.get("type") == "RUN_FINISHED":
                    run_finished = True
                    logger.debug(f"✅ Run finished: {run_id}")
                else:
                    logger.debug(f"📤 Event #{event_num}: {event_type}")
                
                # Encode and yield event
                encoded = encoder.encode(event)
                logger.debug(f"   Encoded length: {len(encoded)} bytes")
                yield encoded
            
            logger.debug(f"🏁 agent.run() completed, yielded {event_num} events total")
                
        except GeneratorExit:
            # Client disconnected - log but don't try to send more data
            logger.warning(f"⚠️  Client disconnected during stream (run_id={run_id})")
            # Don't yield anything - connection is already closed
            
        except Exception as e:
            logger.error(f"❌ Error in event_generator: {e}", exc_info=True)
            
            try:
                # Send error event to frontend
                error_event = {
                    "type": "RUN_ERROR",
                    "error": str(e),
                    "runId": run_id,
                    "timestamp": int(time.time() * 1000)
                }
                yield encoder.encode(error_event)
                
                # Ensure run is properly terminated if it was started
                if run_started and not run_finished:
                    logger.info(f"🔚 Sending final RUN_FINISHED after error (run_id={run_id})")
                    finish_event = {
                        "type": "RUN_FINISHED",
                        "runId": run_id,
                        "threadId": input_data.thread_id,
                        "timestamp": int(time.time() * 1000)
                    }
                    yield encoder.encode(finish_event)
            except Exception as cleanup_error:
                # Last resort - log error but don't crash
                logger.error(f"❌ Failed to send error cleanup events: {cleanup_error}")
        
        finally:
            # Final safety net: ensure run is marked complete
            if run_started and not run_finished:
                try:
                    logger.warning(f"⚠️  Run {run_id} was started but never finished, sending final event")
                    finish_event = {
                        "type": "RUN_FINISHED",
                        "runId": run_id or f"run_{int(time.time()*1000)}",
                        "threadId": input_data.thread_id,
                        "timestamp": int(time.time() * 1000)
                    }
                    yield encoder.encode(finish_event)
                except GeneratorExit:
                    # Client already disconnected
                    pass
                except Exception as final_error:
                    logger.error(f"❌ Failed to send final RUN_FINISHED: {final_error}")
    
    # Create a wrapper to handle guest message counting
    async def event_generator_with_counting():
        try:
            async for event in event_generator():
                yield event
            
            # Increment guest message count after successful processing
            if token_type == 'guest' and token:
                try:
                    await token_manager.increment_guest_message_count(token)
                    logger.debug(f"✅ Incremented guest message count for token {token[:20]}...")
                except Exception as count_error:
                    logger.warning(f"⚠️  Failed to increment guest message count: {count_error}")
                    
        except Exception as e:
            logger.error(f"❌ Error in event generator with counting: {e}")
            raise
    
    return StreamingResponse(
        event_generator_with_counting(),
        media_type=encoder.get_content_type(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        }
    )


@router.get("/agent/luka/health")
def luka_health():
    """
    Health check endpoint for Luka agent.
    
    Returns agent information and available features.
    """
    agent = get_luka_agent()
    
    return {
        "status": "ok",
        "agent": {
            "name": agent.name,
            "description": agent.description,
            "features": [
                "agentic_chat",
                "human_in_the_loop",
                "backend_tool_rendering",
                "catalog_search",
                "task_management",
                "command_execution",
                "bpmn_workflows"
            ],
            "version": "1.0.0"
        },
        "adapters": {
            "llm": agent.llm_adapter is not None,
            "task": agent.task_adapter is not None,
            "catalog": agent.catalog_adapter is not None,
            "command": agent.command_adapter is not None,
        }
    }


@router.get("/agent/luka/info")
def luka_info():
    """
    Detailed agent information endpoint.
    
    Provides comprehensive information about the Luka agent,
    its capabilities, and configuration.
    """
    return {
        "name": "luka",
        "displayName": "Luka Bot",
        "description": "Community Knowledge Assistant with BPMN workflows and task management",
        "version": "1.0.0",
        "protocol": "ag-ui",
        "features": {
            "agentic_chat": {
                "enabled": True,
                "description": "Real-time chat with LLM streaming"
            },
            "human_in_the_loop": {
                "enabled": True,
                "description": "Interactive task approval and completion"
            },
            "backend_tool_rendering": {
                "enabled": True,
                "description": "Visualization of tool execution"
            },
            "catalog_search": {
                "enabled": True,
                "description": "Search across knowledge bases"
            },
            "task_management": {
                "enabled": True,
                "description": "Camunda BPMN task management"
            },
            "command_execution": {
                "enabled": True,
                "description": "Slash commands for quick actions"
            }
        },
        "integrations": {
            "camunda": "BPMN workflow engine",
            "elasticsearch": "Knowledge base search",
            "flow_api": "User authentication",
            "s3": "File storage"
        },
        "endpoints": {
            "agent": "/api/agent/luka",
            "health": "/api/agent/luka/health",
            "info": "/api/agent/luka/info",
            "websocket": "/ws/chat"  # Legacy WebSocket endpoint
        }
    }


# ========================================
# Feature-Specific Endpoints for AG-UI Compatibility
# ========================================

@router.post("/agent/luka/agentic_chat/")
async def agentic_chat_endpoint(input_data: RunAgentInput, request: Request):
    """Agentic chat feature endpoint for AG-UI compatibility."""
    return await luka_agent_endpoint(input_data, request, feature="agentic_chat")

@router.post("/agent/luka/agentic_generative_ui/")
async def agentic_generative_ui_endpoint(input_data: RunAgentInput, request: Request):
    """Agentic generative UI feature endpoint for AG-UI compatibility."""
    return await luka_agent_endpoint(input_data, request, feature="agentic_generative_ui")

@router.post("/agent/luka/human_in_the_loop/")
async def human_in_the_loop_endpoint(input_data: RunAgentInput, request: Request):
    """Human in the loop feature endpoint for AG-UI compatibility."""
    return await luka_agent_endpoint(input_data, request, feature="human_in_the_loop")

@router.post("/agent/luka/shared_state/")
async def shared_state_endpoint(input_data: RunAgentInput, request: Request):
    """Shared state feature endpoint for AG-UI compatibility."""
    return await luka_agent_endpoint(input_data, request, feature="shared_state")

@router.post("/agent/luka/tool_based_generative_ui/")
async def tool_based_generative_ui_endpoint(input_data: RunAgentInput, request: Request):
    """Tool-based generative UI feature endpoint for AG-UI compatibility."""
    return await luka_agent_endpoint(input_data, request, feature="tool_based_generative_ui")

@router.post("/agent/luka/backend_tool_rendering/")
async def backend_tool_rendering_endpoint(input_data: RunAgentInput, request: Request):
    """Backend tool rendering feature endpoint for AG-UI compatibility."""
    return await luka_agent_endpoint(input_data, request, feature="backend_tool_rendering")

@router.get("/agent/luka/onboarding-form")
async def get_onboarding_form(
    request: Request, 
    user_id: Optional[str] = None, 
    is_guest: bool = True,
    command: Optional[str] = None,
    language: Optional[str] = None
):
    """
    Get the onboarding form directly without SSE streaming.
    
    This endpoint provides a direct way for the frontend to get the onboarding form
    without relying on the SSE event stream processing.
    
    Args:
        user_id: Optional user ID (None for guests)
        is_guest: Whether the user is a guest (default: True)
        command: Optional command (start, select_language, set_language, back_to_onboarding)
        language: Optional language code (en, ru) for language-specific forms
    
    Returns:
        FormRequest object with onboarding form structure
    """
    try:
        from ag_ui_gateway.adapters.command_adapter import get_command_adapter
        
        # Get command adapter
        command_adapter = get_command_adapter()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id and user_id != "null" and user_id != "undefined":
            try:
                user_id_int = int(user_id)
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id}")
        
        # Get request headers for language detection
        request_headers = dict(request.headers) if request.headers else {}
        
        # Override language detection if language parameter is provided
        if language:
            request_headers["accept-language"] = f"{language}-{language.upper()},{language};q=0.9"
        
        # Determine command to execute
        command_to_execute = command or "start"
        parameters = {"language": language} if language else None
        
        # Execute the specified command to get the form
        result = await command_adapter.execute_command(
            command=command_to_execute,
            parameters=parameters,
            user_id=user_id_int,
            is_guest=is_guest,
            request_headers=request_headers
        )
        
        logger.info(f"📋 Onboarding form requested for user_id={user_id_int}, is_guest={is_guest}")
        logger.debug(f"📋 Form result: {result}")
        
        # Return the form result directly
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting onboarding form: {e}")
        return {
            "type": "error",
            "message": f"Failed to get onboarding form: {str(e)}",
            "code": "ONBOARDING_FORM_ERROR"
        }
