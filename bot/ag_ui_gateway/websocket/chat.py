"""
WebSocket Chat Handler

Handles AG-UI protocol WebSocket communication.
"""
import time
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json

from ag_ui_gateway.auth.tokens import get_token_manager
from ag_ui_gateway.adapters.llm_adapter import get_llm_adapter
from ag_ui_gateway.adapters.task_adapter import get_task_adapter
from ag_ui_gateway.adapters.catalog_adapter import get_catalog_adapter
from ag_ui_gateway.adapters.command_adapter import get_command_adapter
from ag_ui_gateway.services.ui_events import build_task_list_event, build_ui_context_event


def _resolve_user_id(session: dict) -> tuple[int, bool]:
    """Return (user_id_int, is_guest)."""
    user_id = session.get("user_id")
    token_type = session.get("token_type")
    is_guest = token_type == "guest"

    if user_id is None:
        return 0, True

    if isinstance(user_id, int):
        return user_id, is_guest or user_id == 0

    try:
        user_id_str = str(user_id)
        if user_id_str.isdigit():
            numeric_id = int(user_id_str)
            return numeric_id, is_guest or numeric_id == 0
        numeric_id = int(user_id_str)
        return numeric_id, is_guest or numeric_id == 0
    except (ValueError, TypeError):
        hashed = hash(str(user_id)) % (10 ** 8)
        return hashed, is_guest


def _command_to_mode(command: str) -> str:
    mapping = {
        "start": "start",
        "chat": "chat",
        "tasks": "tasks",
        "profile": "profile",
        "groups": "groups",
        "catalog": "catalog",
    }
    return mapping.get(command.lower(), "chat")


async def handle_onboarding_form_submit(
    user_id: int,
    form_id: str,
    form_data: dict
) -> dict:
    """
    Handle onboarding form submission.
    
    Args:
        user_id: User ID 
        form_id: Onboarding form ID
        form_data: Form data from client
        
    Returns:
        AG-UI formSubmitted event
    """
    try:
        logger.info(f"🎉 Processing onboarding form: user={user_id}, form={form_id}")
        
        # Extract form data
        language = form_data.get('language', 'en')
        action = None
        
        # Check which action was triggered
        if 'complete_onboarding' in form_data:
            action = 'complete_onboarding'
        elif 'browse_groups' in form_data:
            action = 'browse_groups'
        
        # Process language selection and complete onboarding
        if language in ['en', 'ru']:
            from luka_bot.services.user_profile_service import get_user_profile_service
            
            profile_service = get_user_profile_service()
            
            # Update user language
            await profile_service.update_language(user_id, language)
            
            # Mark onboarding as complete
            await profile_service.mark_onboarding_complete(user_id)
            
            # Set KB index for user
            from luka_bot.core.config import settings
            kb_index_name = f"{settings.ELASTICSEARCH_USER_KB_PREFIX}{user_id}"
            await profile_service.set_kb_index(user_id, kb_index_name)
            
            logger.info(f"✅ Onboarding completed for user {user_id} with language {language}")
        
        # Handle action-specific logic
        if action == 'complete_onboarding':
            # Start the chatbot_start workflow now that onboarding is complete
            try:
                from ag_ui_gateway.adapters.command_adapter import get_command_adapter
                command_adapter = get_command_adapter()
                
                # Trigger the start workflow 
                workflow_result = await command_adapter._handle_workflow_command(
                    user_id=user_id,
                    workflow_key="chatbot_start",
                    parameters={"onboarding_completed": True}
                )
                
                logger.info(f"🔄 Started chatbot_start workflow after onboarding: {workflow_result}")
                
            except Exception as e:
                logger.error(f"❌ Error starting workflow after onboarding: {e}")
            
            return {
                "type": "formSubmitted",
                "formId": form_id,
                "success": True,
                "message": "🎉 Welcome! Your account is now set up. Let's get started!",
                "metadata": {
                    "onboarding_completed": True,
                    "language": language,
                    "action": action,
                    "redirect": "start"  # Suggest UI redirect to start mode
                }
            }
            
        elif action == 'browse_groups':
            return {
                "type": "formSubmitted", 
                "formId": form_id,
                "success": True,
                "message": "Let's set up your groups!",
                "metadata": {
                    "onboarding_completed": True,
                    "language": language,
                    "action": action,
                    "redirect": "groups"  # Suggest UI redirect to groups mode
                }
            }
        
        else:
            # Default completion
            return {
                "type": "formSubmitted",
                "formId": form_id,
                "success": True,
                "message": "Settings updated successfully!",
                "metadata": {
                    "language": language,
                    "action": action or "update"
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error processing onboarding form: {e}")
        return {
            "type": "formSubmitted",
            "formId": form_id,
            "success": False,
            "message": f"Onboarding failed: {str(e)}",
            "metadata": {
                "error": str(e)
            }
        }


async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for AG-UI protocol chat.
    
    Handles:
    - Authentication
    - Message routing
    - Event dispatching
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted: {websocket.client}")
    
    token_manager = get_token_manager()
    session = None
    
    try:
        # Wait for auth message
        auth_message = await websocket.receive_json()
        
        if auth_message.get('type') != 'auth':
            await websocket.send_json({
                'type': 'error',
                'code': 'AUTH_REQUIRED',
                'message': 'Authentication required'
            })
            await websocket.close(code=1008)
            return
        
        # Validate token
        token = auth_message.get('token')
        session = await token_manager.validate_token(token)
        
        if not session:
            await websocket.send_json({
                'type': 'error',
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired token'
            })
            await websocket.close(code=1008)
            return
        
        # Check password authentication (if enabled)
        from ag_ui_gateway.middleware.password import verify_password_for_session, PasswordAuthError
        
        password = auth_message.get('password')
        try:
            await verify_password_for_session(token, password, session.get('user_id'))
        except PasswordAuthError as e:
            error_code = 'INCORRECT_PASSWORD' if 'incorrect' in str(e).lower() else 'PASSWORD_REQUIRED'
            await websocket.send_json({
                'type': 'error',
                'code': error_code,
                'message': str(e),
                'hint': 'Include "password" field in auth message with correct password'
            })
            await websocket.close(code=1008)
            return
        
        # Send auth success
        await websocket.send_json({
            'type': 'auth_success',
            'mode': session['token_type'],
            'user_id': session.get('user_id'),
            'permissions': session.get('permissions', []),
            'message': f"{session['token_type'].capitalize()} mode active"
        })
        
        logger.info(f"WebSocket authenticated: mode={session['token_type']}")
        
        # Message loop
        while True:
            message = await websocket.receive_json()
            await handle_message(websocket, message, session)
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


async def handle_message(websocket: WebSocket, message: dict, session: dict):
    """Handle incoming WebSocket message."""
    message_type = message.get('type')
    
    logger.info(f"Received message: type={message_type}")
    
    if message_type == 'user_message':
        await handle_user_message(websocket, message, session)
    elif message_type == 'command':
        await handle_command(websocket, message, session)
    elif message_type == 'form_submit':
        await handle_form_submit(websocket, message, session)
    elif message_type == 'search_kb':
        await handle_search(websocket, message, session)
    elif message_type == 'ping':
        await websocket.send_json({'type': 'pong'})
    else:
        await websocket.send_json({
            'type': 'error',
            'code': 'UNKNOWN_MESSAGE_TYPE',
            'message': f'Unknown message type: {message_type}'
        })


async def handle_user_message(websocket: WebSocket, message: dict, session: dict):
    """
    Handle user chat message with LLM streaming.
    
    Args:
        websocket: WebSocket connection
        message: Message data with 'content' field
        session: User session with token_type, user_id, etc.
    """
    try:
        user_message = message.get('content', '')
        thread_id = message.get('threadId')  # Optional conversation thread ID
        
        if not user_message:
            await websocket.send_json({
                'type': 'error',
                'code': 'EMPTY_MESSAGE',
                'message': 'Message content cannot be empty'
            })
            return
        
        token_type = session.get('token_type')
        user_id_int, resolved_guest = _resolve_user_id(session)
        is_guest = resolved_guest or token_type == 'guest'

        if token_type == 'guest':
            # Check message count limit for guests
            message_count = session.get('message_count', 0)
            from ag_ui_gateway.config.settings import settings
            
            if message_count >= settings.GUEST_TOTAL_MESSAGES:
                await websocket.send_json({
                    'type': 'error',
                    'code': 'GUEST_LIMIT_EXCEEDED',
                    'message': f'Guest message limit ({settings.GUEST_TOTAL_MESSAGES}) reached. Please sign in for unlimited messages.',
                    'upgradeUrl': '/api/auth/telegram-miniapp'
                })
                return
            
            # Increment guest message count
            token = session.get('token')
            if token:
                token_manager = get_token_manager()
                await token_manager.increment_guest_message_count(token)
        
        ui_event = await build_ui_context_event(
            user_id=user_id_int if user_id_int > 0 else None,
            active_mode="chat",
            is_guest=is_guest,
        )
        if ui_event:
            await websocket.send_json(ui_event)

        # Determine effective user id for LLM streaming
        token = session.get('token', '')
        effective_user_id = user_id_int if user_id_int > 0 else hash(token) % (10 ** 8)

        # Get LLM adapter and stream response
        llm_adapter = get_llm_adapter()
        
        logger.info(f"🤖 Processing message: user_id={effective_user_id}, thread={thread_id}, type={token_type}")
        
        # Stream LLM response as AG-UI events
        async for event in llm_adapter.stream_response(
            user_message=user_message,
            user_id=effective_user_id,
            thread_id=thread_id,
            session_context=session
        ):
            # Send event to client
            await websocket.send_json(event)
        
        logger.info(f"✅ Message processing complete for user {effective_user_id}")

        task_event = await build_task_list_event(
            user_id=user_id_int if user_id_int > 0 else None,
            source="chatbot_start",
            force=False,
        )
        if task_event:
            await websocket.send_json(task_event)
        
    except Exception as e:
        logger.error(f"❌ Error handling user message: {e}")
        await websocket.send_json({
            'type': 'error',
            'code': 'MESSAGE_PROCESSING_ERROR',
            'message': 'Failed to process message'
        })


async def handle_command(websocket: WebSocket, message: dict, session: dict):
    """
    Handle command execution and optional workflow triggering.
    
    Args:
        websocket: WebSocket connection
        message: Message with 'command' and optional 'parameters'
        session: User session
    """
    try:
        command = message.get('command')
        parameters = message.get('parameters', {})
        
        if not command:
            await websocket.send_json({
                'type': 'error',
                'code': 'MISSING_COMMAND',
                'message': 'Command is required'
            })
            return
        
        token_type = session.get('token_type')
        user_id_int, resolved_guest = _resolve_user_id(session)
        is_guest = resolved_guest or token_type == 'guest'

        logger.info(f"⚡ Command execution: command={command}, user={user_id_int}, guest={is_guest}")

        mode = _command_to_mode(command or "")
        ui_event = await build_ui_context_event(
            user_id=user_id_int if user_id_int > 0 else None,
            active_mode=mode,
            is_guest=is_guest,
        )
        if ui_event:
            await websocket.send_json(ui_event)

        # Send processing state
        await websocket.send_json({
            'type': 'stateUpdate',
            'status': 'processing',
            'metadata': {'message': f'Executing command: {command}'}
        })
        
        # Execute command via CommandAdapter
        command_adapter = get_command_adapter()
        result = await command_adapter.execute_command(
            command=command,
            parameters=parameters,
            user_id=user_id_int,
            is_guest=is_guest
        )
        
        # Send result
        await websocket.send_json(result)
        
        # Send completion state
        success = result.get('type') != 'error'
        await websocket.send_json({
            'type': 'stateUpdate',
            'status': 'complete' if success else 'error',
            'metadata': {
                'message': result.get('message', 'Command executed'),
                'command': command
            }
        })
        
        logger.info(f"✅ Command execution complete: {command}, success={success}")

        task_event = await build_task_list_event(
            user_id=user_id_int if user_id_int > 0 else None,
            source="chatbot_start",
            force=mode in {"start", "tasks"},
        )
        if task_event:
            await websocket.send_json(task_event)
        
    except Exception as e:
        logger.error(f"❌ Error handling command: {e}")
        await websocket.send_json({
            'type': 'error',
            'code': 'COMMAND_ERROR',
            'message': 'Command execution failed'
        })


async def handle_form_submit(websocket: WebSocket, message: dict, session: dict):
    """
    Handle task form submission.
    
    Args:
        websocket: WebSocket connection
        message: Message with 'formId' and 'formData' fields
        session: User session with user_id
    """
    try:
        form_id = message.get('formId')  # This is the task_id
        form_data = message.get('formData', {})
        
        if not form_id:
            await websocket.send_json({
                'type': 'error',
                'code': 'MISSING_FORM_ID',
                'message': 'Form ID is required'
            })
            return
        
        # Check form type - onboarding forms have special handling
        is_onboarding_form = form_id.startswith('onboarding_')
        
        # Check if user is authenticated (guests can't submit forms, except onboarding)
        token_type = session.get('token_type')

        user_id_int, resolved_guest = _resolve_user_id(session)
        if (token_type == 'guest' or user_id_int <= 0 or resolved_guest) and not is_onboarding_form:
            await websocket.send_json({
                'type': 'error',
                'code': 'AUTH_REQUIRED',
                'message': 'Authentication required to submit forms. Please sign in.',
                'upgradeUrl': '/api/auth/telegram-miniapp'
            })
            return
        
        logger.info(f"📤 Form submission: user={user_id_int}, form={form_id}")
        
        # Send processing state
        await websocket.send_json({
            'type': 'stateUpdate',
            'status': 'processing',
            'metadata': {'message': 'Submitting form...'}
        })
        
        # Handle different form types
        if is_onboarding_form:
            # Handle onboarding form submission
            result = await handle_onboarding_form_submit(
                user_id=user_id_int,
                form_id=form_id,
                form_data=form_data
            )
        else:
            # Submit via TaskAdapter for task forms
            task_adapter = get_task_adapter()
            result = await task_adapter.submit_task_form(
                user_id=user_id_int,
                task_id=form_id,
                form_data=form_data
            )
        
        # Send result
        await websocket.send_json(result)
        
        # Send completion state
        await websocket.send_json({
            'type': 'stateUpdate',
            'status': 'complete' if result.get('success') else 'error',
            'metadata': {'message': result.get('message', '')}
        })
        
        logger.info(f"✅ Form submission complete: form={form_id}, success={result.get('success')}")

        # Only send task list updates for non-onboarding forms
        if not is_onboarding_form:
            task_event = await build_task_list_event(
                user_id=user_id_int,
                source="chatbot_start",
                force=True,
            )
            if task_event:
                await websocket.send_json(task_event)
        else:
            # For onboarding forms, send updated UI context
            ui_context_event = await build_ui_context_event(
                user_id=user_id_int,
                active_mode="start",
                force=True
            )
            if ui_context_event:
                await websocket.send_json(ui_context_event)
        
    except Exception as e:
        logger.error(f"❌ Error handling form submission: {e}")
        await websocket.send_json({
            'type': 'error',
            'code': 'FORM_SUBMISSION_ERROR',
            'message': 'Failed to submit form'
        })


async def handle_search(websocket: WebSocket, message: dict, session: dict):
    """
    Handle knowledge base search.
    
    Args:
        websocket: WebSocket connection
        message: Message with 'query', 'kb_id', and optional 'search_method'
        session: User session
    """
    try:
        query = message.get('query', '')
        kb_id = message.get('kb_id')
        search_method = message.get('search_method', 'text')  # text, vector, hybrid
        max_results = message.get('max_results', 5)
        
        if not query:
            await websocket.send_json({
                'type': 'error',
                'code': 'EMPTY_QUERY',
                'message': 'Search query cannot be empty'
            })
            return
        
        if not kb_id:
            await websocket.send_json({
                'type': 'error',
                'code': 'MISSING_KB_ID',
                'message': 'Knowledge base ID is required'
            })
            return
        
        # Get user ID (None for guests - public search only)
        user_id = session.get('user_id')
        token_type = session.get('token_type')
        
        logger.info(f"🔍 Search request: user={user_id}, kb={kb_id}, query='{query}', type={token_type}")
        
        # Send searching state
        await websocket.send_json({
            'type': 'stateUpdate',
            'status': 'searching',
            'metadata': {'message': 'Searching knowledge base...'}
        })
        
        # Search via CatalogAdapter
        catalog_adapter = get_catalog_adapter()
        results = await catalog_adapter.search_knowledge_base(
            kb_id=kb_id,
            query=query,
            user_id=user_id,
            max_results=max_results,
            search_method=search_method
        )
        
        # Send results
        await websocket.send_json({
            'type': 'searchResult',
            'query': query,
            'kb_id': kb_id,
            'results': results,
            'count': len(results),
            'timestamp': int(time.time() * 1000)
        })
        
        # Send completion state
        await websocket.send_json({
            'type': 'stateUpdate',
            'status': 'complete',
            'metadata': {'message': f'Found {len(results)} results'}
        })
        
        logger.info(f"✅ Search complete: {len(results)} results")
        
    except Exception as e:
        logger.error(f"❌ Error handling search: {e}")
        await websocket.send_json({
            'type': 'error',
            'code': 'SEARCH_ERROR',
            'message': 'Search failed'
        })
