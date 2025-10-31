"""
Command Adapter for AG-UI Protocol

Routes commands to handlers and optionally triggers BPMN workflows.
"""
from typing import Optional, Dict, Any
import time
from loguru import logger

# Lazy imports to avoid circular dependencies
# from luka_bot.services.camunda_service import get_camunda_service
from ag_ui_gateway.config.commands import get_command_config, COMMAND_WORKFLOWS
from ag_ui_gateway.adapters.task_adapter import get_task_adapter
from ag_ui_gateway.adapters.catalog_adapter import get_catalog_adapter


class CommandAdapter:
    """
    Adapter for command routing and workflow execution.
    
    Handles:
    - Command validation and permission checks
    - Workflow triggering (Camunda BPMN)
    - Command result formatting
    - State management
    """
    
    def __init__(self):
        # Lazy initialization to avoid circular imports
        self._camunda_service = None
        self.task_adapter = get_task_adapter()
        self.catalog_adapter = get_catalog_adapter()
    
    @property
    def camunda_service(self):
        """Get Camunda service (lazy loaded)."""
        if self._camunda_service is None:
            from luka_bot.services.camunda_service import get_camunda_service
            self._camunda_service = get_camunda_service()
        return self._camunda_service
    
    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]],
        user_id: Optional[int],
        is_guest: bool = False,
        request_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command.
        
        Args:
            command: Command name (e.g., "tasks", "search", "catalog")
            parameters: Optional command parameters
            user_id: User ID (None for guests)
            is_guest: Whether user is a guest
        
        Returns:
            Command execution result
        """
        try:
            logger.info(f"⚡ Executing command: {command}, user={user_id}, guest={is_guest}")
            
            # Get command configuration
            config = get_command_config(command)
            
            if not config:
                return self._error_response(
                    f"Unknown command: {command}",
                    "UNKNOWN_COMMAND"
                )
            
            # Check authentication requirement
            if config.requires_auth and (is_guest or not user_id):
                return self._error_response(
                    f"Command '{command}' requires authentication",
                    "AUTH_REQUIRED"
                )
            
            # Route to specific handler
            if command == "tasks":
                return await self._handle_tasks_command(user_id, parameters)
            elif command == "search":
                return await self._handle_search_command(user_id, parameters)
            elif command == "catalog":
                return await self._handle_catalog_command(user_id, parameters)
            elif command == "profile":
                return await self._handle_profile_command(user_id, parameters)
            elif command == "groups":
                return await self._handle_groups_command(user_id, parameters)
            elif command == "scope_toggle":
                return await self._handle_scope_toggle_command(user_id, parameters)
            elif command == "start":
                return await self._handle_start_command(user_id, parameters, is_guest, request_headers)
            elif command == "select_language":
                # Handle language selection form
                current_lang = parameters.get("language", "en") if parameters else "en"
                return await self._handle_language_selection(current_lang)
            elif command == "set_language":
                # Handle setting a specific language - re-render onboarding with new language
                language = parameters.get("language", "en") if parameters else "en"
                # Create fake headers for the selected language
                fake_headers = {"accept-language": f"{language}-{language.upper()},{language};q=0.9"}
                return await self._handle_guest_start(fake_headers)
            elif command == "back_to_onboarding":
                # Go back to onboarding form
                current_lang = parameters.get("language", "en") if parameters else "en"
                fake_headers = {"accept-language": f"{current_lang}-{current_lang.upper()},{current_lang};q=0.9"}
                return await self._handle_guest_start(fake_headers)
            elif command == "start_exploring":
                # Handle start exploring - send initial prompt to LLM
                return await self._handle_start_exploring(user_id, parameters, is_guest, request_headers)
            else:
                # Generic command response
                return {
                    "type": "commandResult",
                    "command": command,
                    "success": True,
                    "message": f"Command '{command}' executed",
                    "data": {},
                    "timestamp": int(time.time() * 1000)
                }
        
        except Exception as e:
            logger.error(f"❌ Error executing command {command}: {e}")
            return self._error_response(
                f"Command execution failed: {str(e)}",
                "EXECUTION_ERROR"
            )
    
    async def _handle_start_command(
        self,
        user_id: Optional[int],
        parameters: Optional[Dict[str, Any]],
        is_guest: bool = False,
        request_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle 'start' command with onboarding detection.
        
        Replicates the Telegram bot's onboarding experience:
        1. Check if user needs onboarding
        2. If yes, show welcome + language selection
        3. If no, proceed with normal workflow
        """
        try:
            # For guests, show simplified welcome without onboarding
            if is_guest or not user_id:
                return await self._handle_guest_start(request_headers)
            
            # Check if user needs onboarding
            from luka_bot.services.user_profile_service import get_user_profile_service
            
            profile_service = get_user_profile_service()
            needs_onboarding = await profile_service.needs_onboarding(user_id)
            
            if needs_onboarding:
                logger.info(f"✨ User {user_id} needs onboarding - showing welcome flow")
                return await self._handle_onboarding_welcome(user_id, parameters)
            else:
                logger.info(f"📋 User {user_id} already onboarded - starting workflow")
                # User already onboarded, trigger the workflow
                config = get_command_config("start")
                if config and config.workflow_key:
                    return await self._handle_workflow_command(
                        user_id, config.workflow_key, parameters
                    )
                else:
                    return self._error_response(
                        "Start workflow not configured",
                        "WORKFLOW_NOT_CONFIGURED"
                    )
                
        except Exception as e:
            logger.error(f"❌ Error handling start command: {e}")
            return self._error_response(
                f"Start command failed: {str(e)}",
                "START_COMMAND_ERROR"
            )
    
    async def _handle_guest_start(self, request_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle start command for guest users with language detection."""
        
        # Detect language from Accept-Language header (default to English)
        detected_lang = "en"
        if request_headers:
            accept_lang = request_headers.get("accept-language", "")
            if "ru" in accept_lang.lower():
                detected_lang = "ru"
        
        # Get localized content
        if detected_lang == "ru":
            title = "👋 Добро пожаловать в Luka!"
            intro = "Я ваш AI-ассистент для управления Telegram сообществами."
            capabilities_header = "🎯 Что я могу для ваших групп:"
            cap_ai = "• 🤖 AI-помощник - Отвечайте на вопросы и помогайте участникам умными контекстными ответами"
            cap_kb = "• 📚 База знаний - Индексируйте и ищите по всем сообщениям и разговорам группы"
            cap_moderation = "• 🛡️ Умная модерация - Автоматическая фильтрация контента, стоп-слова и AI-оценка качества"
            cap_analytics = "• 📊 Аналитика - Отслеживайте активность, вовлеченность участников и детальную статистику группы"
            get_started_header = "🚀 Начните работу:"
            step1 = "1️⃣ Используйте /groups для управления вашими Telegram группами"
            step2 = "2️⃣ Добавьте меня в вашу группу как администратора"
            step3 = "3️⃣ Настройте AI-помощника, модерацию и индексацию БЗ"
            guest_note = "💡 Гостевой режим: Ограниченный доступ к публичному контенту"
            btn_catalog = "🚀 Начать исследование"
            btn_signin = "🔑 Войти для полного доступа"
        else:
            title = "👋 Welcome to Luka!"
            intro = "I'm your AI-powered group management assistant for Telegram communities."
            capabilities_header = "🎯 What I can do for your groups:"
            cap_ai = "• 🤖 AI Assistant - Answer questions and help members with smart, context-aware responses"
            cap_kb = "• 📚 Knowledge Base - Index and search through all group messages and conversations"
            cap_moderation = "• 🛡️ Smart Moderation - Automatic content filtering, stopwords, and AI-powered quality scoring"
            cap_analytics = "• 📊 Analytics - Track activity, member engagement, and generate detailed group statistics"
            get_started_header = "🚀 Get Started:"
            step1 = "1️⃣ Use /groups to manage your Telegram groups"
            step2 = "2️⃣ Add me to your group as an admin"
            step3 = "3️⃣ Configure AI assistance, moderation, and KB indexing"
            guest_note = "💡 Guest Mode: Limited access to public content"
            btn_catalog = "🚀 Start Exploring"
            btn_signin = "🔑 Sign In for Full Access"
        
        # Build comprehensive description
        full_description = f"""{intro}

{capabilities_header}
{cap_ai}
{cap_kb}
{cap_moderation}
{cap_analytics}

{get_started_header}
{step1}
{step2}
{step3}

{guest_note}"""
        
        return {
            "type": "formRequest",
            "form_id": f"guest_welcome_{int(time.time())}",
            "title": title,
            "description": full_description,
            "renderMode": "modal",
            "complexity": "simple",
            "fields": [
                {
                    "type": "button",
                    "name": "start_exploring",
                    "label": btn_catalog,
                    "variant": "primary"
                },
                {
                    "type": "button",
                    "name": "sign_in",
                    "label": btn_signin,
                    "variant": "secondary"
                },
                {
                    "type": "button",
                    "name": "select_language",
                    "label": "🌍",
                    "variant": "outline",
                    "action": "select_language"
                }
            ],
            "metadata": {
                "command": "start",
                "user_type": "guest",
                "language": detected_lang
            }
        }
    
    async def _handle_language_selection(self, current_language: str = "en") -> Dict[str, Any]:
        """Handle language selection form."""
        
        if current_language == "ru":
            title = "🌍 Выберите язык"
            description = "Выберите предпочитаемый язык для интерфейса:"
        else:
            title = "🌍 Select Language"
            description = "Choose your preferred language for the interface:"
        
        return {
            "type": "formRequest",
            "form_id": f"language_selection_{int(time.time())}",
            "title": title,
            "description": description,
            "renderMode": "modal",
            "complexity": "simple",
            "fields": [
                {
                    "type": "button",
                    "name": "set_language_en",
                    "label": "🇺🇸 English",
                    "variant": "primary" if current_language == "en" else "outline",
                    "action": "set_language",
                    "data": {"language": "en"}
                },
                {
                    "type": "button",
                    "name": "set_language_ru",
                    "label": "🇷🇺 Русский",
                    "variant": "primary" if current_language == "ru" else "outline",
                    "data": {"language": "ru"}
                },
                {
                    "type": "button",
                    "name": "back_to_onboarding",
                    "label": "← Back" if current_language == "en" else "← Назад",
                    "variant": "secondary",
                    "action": "back_to_onboarding"
                }
            ],
            "metadata": {
                "command": "select_language",
                "current_language": current_language
            }
        }
    
    async def _handle_onboarding_welcome(
        self,
        user_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle onboarding welcome for new users.
        
        Shows welcome message with language selection and next steps.
        """
        try:
            # Auto-detect language (default to English for web UI)
            # TODO: Could be enhanced to detect browser language
            detected_lang = parameters.get("language", "en") if parameters else "en"
            
            # Create or update user profile with detected language
            from luka_bot.services.user_profile_service import get_user_profile_service
            
            profile_service = get_user_profile_service()
            
            # Create a minimal user object for profile creation
            class MockUser:
                def __init__(self, user_id: int, language_code: str = "en"):
                    self.id = user_id
                    self.username = None
                    self.first_name = "User"
                    self.last_name = None
                    self.language_code = language_code
            
            mock_user = MockUser(user_id, detected_lang)
            profile = await profile_service.get_or_create_profile(user_id, mock_user)
            
            # Get bot capabilities text
            bot_name = "Luka Bot"  # Could be from settings
            
            # Create onboarding form
            fields = [
                {
                    "type": "text",
                    "name": "welcome_message",
                    "label": "Welcome Message",
                    "value": f"🎉 Welcome to {bot_name}!\n\nI'm your AI assistant for managing conversations, tasks, and knowledge bases. Here's what I can help you with:",
                    "readonly": True
                },
                {
                    "type": "text",
                    "name": "capabilities",
                    "label": "What I Can Do",
                    "value": "📋 Manage conversation threads and tasks\n🔍 Search through group history and knowledge\n📊 Summarize conversations and generate insights\n🗂️ Organize and categorize information",
                    "readonly": True
                },
                {
                    "type": "select",
                    "name": "language",
                    "label": "🌍 Choose Your Language",
                    "value": detected_lang,
                    "options": [
                        {"value": "en", "label": "English"},
                        {"value": "ru", "label": "Русский"}
                    ],
                    "required": True
                },
                {
                    "type": "text",
                    "name": "getting_started",
                    "label": "Getting Started",
                    "value": "Try these examples to get started:\n• \"What are my recent tasks?\"\n• \"Summarize this week's discussions\"\n• \"Search for information about...\"",
                    "readonly": True
                },
                {
                    "type": "button",
                    "name": "complete_onboarding",
                    "label": "🚀 Get Started",
                    "variant": "primary"
                },
                {
                    "type": "button",
                    "name": "browse_groups",
                    "label": "🏘️ Setup Groups (Optional)",
                    "variant": "secondary"
                }
            ]
            
            return {
                "type": "formRequest",
                "form_id": f"onboarding_{user_id}_{int(time.time())}",
                "title": f"🎉 Welcome to {bot_name}!",
                "description": "Let's get you set up with personalized features",
                "fields": fields,
                "metadata": {
                    "command": "start",
                    "user_type": "new_user",
                    "user_id": user_id,
                    "onboarding": True,
                    "detected_language": detected_lang
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating onboarding welcome: {e}")
            return self._error_response(
                f"Onboarding setup failed: {str(e)}",
                "ONBOARDING_ERROR"
            )

    async def _handle_tasks_command(
        self,
        user_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle 'tasks' command - show task management form."""
        tasks = await self.task_adapter.get_user_tasks(user_id)
        
        # Create form fields for each task
        fields = []
        for task in tasks:
            task_name = task.get('name', 'Unknown Task')
            task_id = task.get('id', 'unknown')
            fields.append({
                "type": "button",
                "name": f"task_{task_id}",
                "label": f"📋 {task_name}",
                "variant": "secondary",
                "metadata": {
                    "task_id": task_id,
                    "task_name": task_name,
                    "process_id": task.get('process_instance_id'),
                    "created": task.get('created')
                }
            })
        
        # Add filter options
        fields.append({
            "type": "button",
            "name": "filter_all",
            "label": "📄 All Tasks",
            "variant": "outline"
        })
        
        fields.append({
            "type": "button",
            "name": "filter_pending",
            "label": "⏳ Pending",
            "variant": "outline"
        })
        
        fields.append({
            "type": "button",
            "name": "refresh",
            "label": "🔄 Refresh",
            "variant": "primary"
        })
        
        return {
            "type": "formRequest",
            "form_id": f"tasks_{int(time.time())}",
            "title": "📋 Task Management",
            "description": f"You have {len(tasks)} active tasks",
            "fields": fields,
            "metadata": {
                "command": "tasks",
                "task_count": len(tasks)
            }
        }
    
    async def _handle_search_command(
        self,
        user_id: Optional[int],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle 'search' command - search knowledge bases."""
        if not parameters or "query" not in parameters:
            return self._error_response(
                "Search query is required",
                "MISSING_PARAMETER"
            )
        
        query = parameters.get("query", "")
        kb_id = parameters.get("kb_id")
        
        if not kb_id:
            return self._error_response(
                "Knowledge base ID is required",
                "MISSING_PARAMETER"
            )
        
        results = await self.catalog_adapter.search_knowledge_base(
            kb_id=kb_id,
            query=query,
            user_id=user_id,
            max_results=parameters.get("max_results", 5),
            search_method=parameters.get("method", "text")
        )
        
        return {
            "type": "commandResult",
            "command": "search",
            "success": True,
            "message": f"Found {len(results)} results",
            "data": {
                "query": query,
                "kb_id": kb_id,
                "results": results,
                "count": len(results)
            },
            "timestamp": int(time.time() * 1000)
        }
    
    async def _handle_catalog_command(
        self,
        user_id: Optional[int],
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle 'catalog' command - show knowledge base catalog form."""
        kbs = await self.catalog_adapter.list_knowledge_bases(
            user_id=user_id,
            include_stats=parameters.get("include_stats", False) if parameters else False
        )
        
        # Create form fields for each knowledge base
        fields = []
        for kb in kbs:
            fields.append({
                "type": "button",
                "name": f"kb_{kb.get('id', 'unknown')}",
                "label": f"📚 {kb.get('title', 'Unknown KB')}",
                "variant": "secondary",
                "metadata": {
                    "kb_id": kb.get('id'),
                    "kb_title": kb.get('title'),
                    "message_count": kb.get('message_count', 0)
                }
            })
        
        # Add search field
        fields.append({
            "type": "text",
            "name": "search_query",
            "label": "Search in catalog",
            "placeholder": "Enter search terms...",
            "required": False
        })
        
        fields.append({
            "type": "button",
            "name": "search",
            "label": "🔍 Search",
            "variant": "primary"
        })
        
        return {
            "type": "formRequest",
            "form_id": f"catalog_{int(time.time())}",
            "title": "📚 Knowledge Base Catalog",
            "description": f"Browse {len(kbs)} available knowledge bases",
            "fields": fields,
            "metadata": {
                "command": "catalog",
                "kb_count": len(kbs)
            }
        }
    
    async def _handle_profile_command(
        self,
        user_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle 'profile' command - get user profile."""
        try:
            from luka_bot.services.user_profile_service import get_user_profile_service
            
            profile_service = get_user_profile_service()
            profile = await profile_service.get_profile(user_id)
            
            if not profile:
                return self._error_response(
                    "Profile not found",
                    "PROFILE_NOT_FOUND"
                )
            
            return {
                "type": "commandResult",
                "command": "profile",
                "success": True,
                "message": "Profile retrieved successfully",
                "data": {
                    "profile": {
                        "user_id": profile.user_id,
                        "username": profile.username,
                        "first_name": profile.first_name,
                        "last_name": profile.last_name,
                        "language": profile.language,
                        "created_at": profile.created_at.isoformat() if profile.created_at else None,
                        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
                    }
                },
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"❌ Error handling profile command: {e}")
            return self._error_response(
                f"Failed to retrieve profile: {str(e)}",
                "PROFILE_ERROR"
            )
    
    async def _handle_groups_command(
        self,
        user_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle 'groups' command - show group management form."""
        try:
            from luka_bot.services.group_service import get_group_service
            
            group_service = await get_group_service()
            links = await group_service.list_user_groups(user_id, active_only=True)
            
            # Create form fields for each group
            fields = []
            for link in links:
                try:
                    metadata = await group_service.get_cached_group_metadata(link.group_id)
                    group_title = metadata.group_title if metadata else f"Group {link.group_id}"
                    
                    fields.append({
                        "type": "button",
                        "name": f"group_{link.group_id}",
                        "label": f"🏘️ {group_title}",
                        "variant": "secondary",
                        "metadata": {
                            "group_id": link.group_id,
                            "group_title": group_title,
                            "is_active": link.is_active,
                            "joined_at": link.joined_at.isoformat() if link.joined_at else None
                        }
                    })
                except Exception as e:
                    logger.warning(f"Failed to load metadata for group {link.group_id}: {e}")
                    fields.append({
                        "type": "button",
                        "name": f"group_{link.group_id}",
                        "label": f"🏘️ Group {link.group_id}",
                        "variant": "secondary",
                        "metadata": {
                            "group_id": link.group_id,
                            "group_title": f"Group {link.group_id}",
                            "is_active": link.is_active
                        }
                    })
            
            # Add management options
            fields.append({
                "type": "button",
                "name": "join_group",
                "label": "➕ Join New Group",
                "variant": "primary"
            })
            
            fields.append({
                "type": "button",
                "name": "refresh",
                "label": "🔄 Refresh",
                "variant": "outline"
            })
            
            return {
                "type": "formRequest",
                "form_id": f"groups_{int(time.time())}",
                "title": "🏘️ Group Management",
                "description": f"You are a member of {len(links)} groups",
                "fields": fields,
                "metadata": {
                    "command": "groups",
                    "group_count": len(links)
                }
            }
        except Exception as e:
            logger.error(f"❌ Error handling groups command: {e}")
            return self._error_response(
                f"Failed to retrieve groups: {str(e)}",
                "GROUPS_ERROR"
            )
    
    async def _handle_scope_toggle_command(
        self,
        user_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle 'scope_toggle' command - toggle group selection in KB scope."""
        try:
            group_id = parameters.get("group_id") if parameters else None
            if not group_id:
                return self._error_response(
                    "Group ID is required for scope toggle",
                    "MISSING_GROUP_ID"
                )
            
            from luka_bot.services.user_kb_scope_service import get_user_kb_scope_service
            
            scope_service = get_user_kb_scope_service()
            current_scope = await scope_service.get_user_scope(user_id)
            
            # Toggle the group in the scope
            selected_groups = list(current_scope.selected_groups or [])
            if group_id in selected_groups:
                selected_groups.remove(group_id)
                action = "removed"
            else:
                if len(selected_groups) >= 10:
                    return self._error_response(
                        "Maximum 10 groups can be selected",
                        "SCOPE_LIMIT_EXCEEDED"
                    )
                selected_groups.append(group_id)
                action = "added"
            
            # Update the scope
            updated_scope = await scope_service.update_user_scope(
                user_id=user_id,
                selected_groups=selected_groups
            )
            
            return {
                "type": "stateUpdate",
                "status": "complete",
                "metadata": {
                    "message": f"Group {group_id} {action} from knowledge base scope",
                    "scope_updated": True,
                    "selected_groups": selected_groups,
                    "group_id": group_id,
                    "action": action
                }
            }
        except Exception as e:
            logger.error(f"❌ Error handling scope_toggle command: {e}")
            return self._error_response(
                f"Failed to toggle scope: {str(e)}",
                "SCOPE_TOGGLE_ERROR"
            )
    
    async def _handle_workflow_command(
        self,
        user_id: int,
        workflow_key: str,
        parameters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle workflow command - trigger Camunda BPMN process.
        
        Args:
            user_id: User ID
            workflow_key: Process definition key
            parameters: Process variables
        
        Returns:
            Command result with process instance info
        """
        try:
            logger.info(f"🔄 Starting workflow: {workflow_key}, user={user_id}")
            
            # Convert parameters to Camunda variable format
            variables = {}
            if parameters:
                for key, value in parameters.items():
                    var_type = "String"
                    if isinstance(value, bool):
                        var_type = "Boolean"
                    elif isinstance(value, int):
                        var_type = "Integer"
                    elif isinstance(value, float):
                        var_type = "Double"
                    
                    variables[key] = {
                        "value": value,
                        "type": var_type
                    }
            
            # Start process instance
            process_instance = await self.camunda_service.start_process(
                telegram_user_id=user_id,
                process_key=workflow_key,
                variables=variables,
                business_key=f"user_{user_id}_{int(time.time())}"
            )
            
            if process_instance:
                logger.info(f"✅ Workflow started: {process_instance.id}")
                return {
                    "type": "commandResult",
                    "command": f"workflow:{workflow_key}",
                    "success": True,
                    "message": "Workflow started successfully",
                    "data": {
                        "process_instance_id": str(process_instance.id),
                        "process_definition_key": workflow_key,
                        "business_key": process_instance.business_key
                    },
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return self._error_response(
                    "Failed to start workflow",
                    "WORKFLOW_START_FAILED"
                )
        
        except ValueError as e:
            # Handle missing Camunda credentials gracefully
            if "No Camunda credentials" in str(e):
                logger.warning(f"⚠️ User {user_id} has no Camunda credentials: {e}")
                return self._error_response(
                    "User authentication required. Please ensure you are properly registered in the system.",
                    "AUTHENTICATION_REQUIRED"
                )
            else:
                logger.error(f"❌ Error starting workflow {workflow_key}: {e}")
                return self._error_response(
                    f"Workflow execution failed: {str(e)}",
                    "WORKFLOW_ERROR"
                )
        except Exception as e:
            logger.error(f"❌ Error starting workflow {workflow_key}: {e}")
            return self._error_response(
                f"Workflow execution failed: {str(e)}",
                "WORKFLOW_ERROR"
            )
    
    async def _handle_start_exploring(
        self,
        user_id: Optional[int],
        parameters: Optional[Dict[str, Any]],
        is_guest: bool = False,
        request_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Handle start exploring command - send initial prompt to LLM.
        """
        try:
            # Detect language from request headers or parameters
            detected_lang = "en"
            if request_headers:
                accept_lang = request_headers.get("accept-language", "")
                if "ru" in accept_lang.lower():
                    detected_lang = "ru"
            elif parameters and parameters.get("language"):
                detected_lang = parameters.get("language", "en")

            # Create language-appropriate initial prompt
            if detected_lang == "ru":
                initial_prompt = "Привет! Я готов исследовать возможности Luka Bot. Расскажи мне, как ты можешь помочь с управлением Telegram сообществами?"
            else:
                initial_prompt = "Hello! I'm ready to start exploring Luka Bot. Can you tell me how you can help with managing Telegram communities?"

            return {
                "type": "chatMessage",
                "role": "user",
                "content": initial_prompt,
                "language": detected_lang,
                "metadata": {
                    "command": "start_exploring",
                    "auto_generated": True,
                    "language": detected_lang
                },
                "timestamp": int(time.time() * 1000)
            }
        except Exception as e:
            logger.error(f"❌ Error handling start exploring: {e}")
            return self._error_response(
                f"Start exploring failed: {str(e)}",
                "START_EXPLORING_ERROR"
            )

    def _error_response(self, message: str, code: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "type": "error",
            "code": code,
            "message": message,
            "timestamp": int(time.time() * 1000)
        }
    
    def list_available_commands(self, is_guest: bool = False) -> Dict[str, Any]:
        """
        List available commands for user.
        
        Args:
            is_guest: Whether user is a guest
        
        Returns:
            List of available commands
        """
        commands = []
        
        for cmd_name, config in COMMAND_WORKFLOWS.items():
            # Skip auth-required commands for guests
            if config.requires_auth and is_guest:
                continue
            
            if config.show_in_menu:
                commands.append({
                    "command": config.command,
                    "description": config.description,
                    "requires_auth": config.requires_auth,
                    "has_workflow": config.workflow_key is not None
                })
        
        return {
            "commands": commands,
            "count": len(commands),
            "is_guest": is_guest
        }


# Singleton instance
_command_adapter: Optional[CommandAdapter] = None


def get_command_adapter() -> CommandAdapter:
    """Get or create CommandAdapter singleton."""
    global _command_adapter
    if _command_adapter is None:
        _command_adapter = CommandAdapter()
        logger.info("✅ CommandAdapter singleton created")
    return _command_adapter

