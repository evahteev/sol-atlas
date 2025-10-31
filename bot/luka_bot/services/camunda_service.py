"""
Camunda Engine integration service for luka_bot.
Manages Camunda connections, process instances, and tasks.
"""
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from camunda_client.clients.engine.client import CamundaEngineClient
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas.response import (
    TaskSchema,
    ProcessInstanceSchema,
    ProcessVariablesSchema
)
from camunda_client.clients.engine.schemas import GetTasksFilterSchema
from camunda_client.exceptions import CamundaClientError
from luka_bot.core.config import settings
import httpx


@dataclass
class CamundaUserMapping:
    """Maps Telegram user to Camunda credentials"""
    telegram_id: int
    camunda_user_id: str
    camunda_password: str


class CamundaService:
    """Singleton service for Camunda operations"""
    
    _instance: Optional['CamundaService'] = None
    
    def __init__(self):
        self._client: Optional[CamundaEngineClient] = None
        self._transport = httpx.AsyncHTTPTransport(
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self._user_mappings: Dict[int, CamundaUserMapping] = {}
        # Cache clients per user to reuse sessions and prevent resource leaks
        self._clients: Dict[int, CamundaEngineClient] = {}
        
    @classmethod
    def get_instance(cls) -> 'CamundaService':
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("✅ CamundaService singleton created")
        return cls._instance
    
    async def _get_client(self, telegram_user_id: int) -> CamundaEngineClient:
        """Get or create cached Camunda client for user"""
        # Return cached client if exists
        if telegram_user_id in self._clients:
            return self._clients[telegram_user_id]
        
        # Get or create user mapping
        mapping = await self._get_or_create_user_mapping(telegram_user_id)
        
        auth_data = AuthData(
            username=mapping.camunda_user_id,
            password=mapping.camunda_password
        )
        
        # Create and cache new client
        client = CamundaEngineClient(
            base_url=settings.ENGINE_URL,
            auth_data=auth_data,
            transport=self._transport
        )
        self._clients[telegram_user_id] = client
        
        logger.debug(f"🔧 Created Camunda client for user {telegram_user_id}")
        return client
    
    async def close_all_clients(self):
        """Close all cached clients (call on shutdown)"""
        for user_id, client in list(self._clients.items()):
            try:
                await client.close()
                logger.debug(f"🔒 Closed Camunda client for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to close client for user {user_id}: {e}")
        self._clients.clear()
    
    async def _get_or_create_user_mapping(self, telegram_user_id: int) -> CamundaUserMapping:
        """
        Get or create Camunda user mapping.
        
        Priority order:
        1. In-memory cache (fastest)
        2. Session cache (fast, from Flow API)
        3. UserProfile (fallback, persistent storage)
        """
        # Check in-memory cache first
        if telegram_user_id in self._user_mappings:
            return self._user_mappings[telegram_user_id]
        
        # Try session cache (from Flow API auth middleware)
        from luka_bot.services.user_session_cache import get_cached_user_info
        user_info = await get_cached_user_info(telegram_user_id)
        
        if user_info:
            camunda_user_id = user_info.get("camunda_user_id")
            camunda_key = user_info.get("camunda_key")
            
            if camunda_user_id and camunda_key:
                mapping = CamundaUserMapping(
                    telegram_id=telegram_user_id,
                    camunda_user_id=camunda_user_id,
                    camunda_password=camunda_key
                )
                self._user_mappings[telegram_user_id] = mapping
                
                logger.info(
                    f"🔐 Created Camunda mapping from session cache: "
                    f"Telegram {telegram_user_id} → Camunda {camunda_user_id}"
                )
                return mapping
        
        # Fallback to UserProfile (persistent storage)
        from luka_bot.services.user_profile_service import get_user_profile_service
        profile_service = get_user_profile_service()
        profile = await profile_service.get_user_profile(telegram_user_id)
        
        if profile and profile.camunda_user_id and profile.camunda_key:
            mapping = CamundaUserMapping(
                telegram_id=telegram_user_id,
                camunda_user_id=profile.camunda_user_id,
                camunda_password=profile.camunda_key
            )
            self._user_mappings[telegram_user_id] = mapping
            
            logger.info(
                f"🔐 Created Camunda mapping from UserProfile: "
                f"Telegram {telegram_user_id} → Camunda {profile.camunda_user_id}"
            )
            return mapping
        
        # Last resort: Fetch directly from Flow API (e.g., for guest user)
        logger.info(f"🔍 Fetching user {telegram_user_id} from Flow API...")
        try:
            from flow_client.clients.flow.client import FlowClient
            
            async with FlowClient(
                base_url=settings.FLOW_API_URL,
                sys_key=settings.FLOW_API_SYS_KEY
            ) as flow_client:
                user_data = await flow_client.get_user(telegram_user_id=telegram_user_id)
                
                if user_data and user_data.camunda_user_id and user_data.camunda_key:
                    mapping = CamundaUserMapping(
                        telegram_id=telegram_user_id,
                        camunda_user_id=user_data.camunda_user_id,
                        camunda_password=user_data.camunda_key
                    )
                    self._user_mappings[telegram_user_id] = mapping
                    
                    # Cache in UserProfile for next time
                    from luka_bot.models.user_profile import UserProfile
                    from datetime import datetime
                    
                    profile = UserProfile(
                        user_id=telegram_user_id,  # UserProfile only has user_id, not telegram_user_id
                        username=user_data.username or f"user_{telegram_user_id}",
                        first_name=getattr(user_data, 'first_name', None),
                        last_name=getattr(user_data, 'last_name', None),
                        language=getattr(user_data, 'language_code', 'en') or 'en',
                        camunda_user_id=user_data.camunda_user_id,
                        camunda_key=user_data.camunda_key,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    await profile_service.save_profile(profile)
                    
                    logger.info(
                        f"🔐 Created Camunda mapping from Flow API: "
                        f"Telegram {telegram_user_id} → Camunda {user_data.camunda_user_id}"
                    )
                    logger.info(f"💾 Cached credentials in UserProfile for future use")
                    return mapping
        except Exception as e:
            logger.warning(f"⚠️  Could not fetch from Flow API: {e}")
        
        # No credentials found anywhere
        logger.error(f"❌ No Camunda credentials for user {telegram_user_id}")
        raise ValueError(
            f"User {telegram_user_id} has no Camunda credentials. "
            "Credentials should be provided via Flow API authentication. "
            "Please ensure:\n"
            "1. User is registered in Flow API\n"
            "2. Flow API has assigned Camunda credentials\n"
            "3. FlowAuthMiddleware is registered and functioning"
        )
    
    async def start_process(
        self,
        telegram_user_id: int,
        process_key: str,
        business_key: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> ProcessInstanceSchema:
        """Start a BPMN process for user"""
        client = await self._get_client(telegram_user_id)
        
        # Convert variables to Camunda format
        logger.debug(f"📤 Raw variables for process {process_key}: {variables}")
        camunda_vars = self._format_variables(variables or {})
        logger.debug(f"📤 Formatted Camunda variables: {camunda_vars}")
        
        try:
            process_instance = await client.start_process(
                process_key=process_key,
                business_key=business_key,
                variables=camunda_vars
            )
            logger.info(
                f"🚀 Started process {process_key} for user {telegram_user_id}: {process_instance.id} "
                f"with {len(variables or {})} variables (business_key={business_key})"
            )
            return process_instance
        except Exception as e:
            logger.error(f"❌ Failed to start process {process_key}: {e}")
            raise
    
    async def correlate_message(
        self,
        telegram_user_id: int,
        message_data: Dict[str, Any],
        message_type: str,
        kb_doc_id: str
    ) -> bool:
        """
        Send message to Camunda via correlation with ES document ID.
        
        Args:
            telegram_user_id: Telegram user ID
            message_data: Message data with thread context
            message_type: Message type (GROUP_MESSAGE, DM_MESSAGE, ASSISTANT_MESSAGE)
            kb_doc_id: Document ID for ES reference
            
        Returns:
            True if successful
        """
        try:
            client = await self._get_client(telegram_user_id)
            camunda_variables = self._format_message_variables(message_data, message_type, kb_doc_id)
            
            from camunda_client.clients.engine.schemas import SendCorrelationMessageSchema
            schema = SendCorrelationMessageSchema(
                message_name=message_type,
                business_key=self._build_business_key(message_data),
                process_variables=camunda_variables
            )
            
            await client.send_correlation_message(schema)
            logger.info(f"📤 Correlated {message_type} message {kb_doc_id} to Camunda")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to correlate {message_type} message {kb_doc_id}: {e}")
            return False
    
    async def get_user_tasks(
        self,
        telegram_user_id: int,
        process_definition_key: Optional[str] = None
    ) -> List[TaskSchema]:
        """
        Get tasks assigned to user, optionally filtered by process definition.
        
        When process_definition_key="chatbot_start", includes tasks from direct
        sub-processes where the root is the user's chatbot_start instance.

        Args:
            telegram_user_id: Telegram user ID
            process_definition_key: Optional process key (e.g., "chatbot_start")

        Returns:
            List of tasks matching the criteria
        """
        client = await self._get_client(telegram_user_id)
        mapping = self._user_mappings[telegram_user_id]

        # Special handling for chatbot_start: include sub-process tasks
        if process_definition_key == "chatbot_start":
            process_instances = await self._get_chatbot_start_process_instances(
                telegram_user_id, client
            )
            
            if not process_instances:
                logger.debug(f"📋 No chatbot_start process found for user {telegram_user_id}")
                return []
            
            # Collect tasks from all process instances (root + sub-processes)
            all_tasks = []
            for process_instance in process_instances:
                filter_schema = GetTasksFilterSchema(
                    assignee=mapping.camunda_user_id,
                    process_instance_id=process_instance.id
                )
                tasks = await client.get_tasks(schema=filter_schema)
                all_tasks.extend(tasks)
            
            logger.debug(
                f"📋 Retrieved {len(all_tasks)} tasks for user {telegram_user_id} "
                f"from chatbot_start and {len(process_instances) - 1} sub-processes"
            )
            return list(all_tasks)
        
        # Standard filtering for other processes or no filter
        filter_schema = GetTasksFilterSchema(
            assignee=mapping.camunda_user_id,
            process_definition_key=process_definition_key
        )
        tasks = await client.get_tasks(schema=filter_schema)

        if process_definition_key:
            logger.debug(
                f"📋 Retrieved {len(tasks)} tasks for user {telegram_user_id} "
                f"from process {process_definition_key}"
            )
        else:
            logger.debug(f"📋 Retrieved {len(tasks)} tasks for user {telegram_user_id}")

        return list(tasks)
    
    async def _get_chatbot_start_process_instances(
        self, 
        telegram_user_id: int, 
        client
    ) -> List[ProcessInstanceSchema]:
        """
        Get chatbot_start root process and its direct sub-processes.
        
        Returns list containing: [root_instance, sub_instance_1, sub_instance_2, ...]
        """
        from camunda_client.clients.engine.schemas.query import ProcessInstanceQuerySchema
        
        business_key = f"{telegram_user_id}-chatbot-start"
        
        # Get root chatbot_start process
        root_query = ProcessInstanceQuerySchema(
            process_definition_key="chatbot_start",
            business_key=business_key,
            active=True
        )
        root_instances = await client.get_process_instances(root_query)
        
        if not root_instances:
            return []
        
        root_instance = root_instances[0]
        process_instances = [root_instance]
        
        # Get direct sub-processes
        sub_query = ProcessInstanceQuerySchema(
            super_process_instance=str(root_instance.id),
            active=True
        )
        sub_instances = await client.get_process_instances(sub_query)
        process_instances.extend(sub_instances)
        
        logger.debug(
            f"Found {len(process_instances)} process instances: "
            f"1 root + {len(sub_instances)} sub-processes"
        )
        
        return process_instances
    
    async def get_process_instance_by_business_key(
        self,
        telegram_user_id: int,
        business_key: str,
        active_only: bool = True
    ) -> Optional[ProcessInstanceSchema]:
        """
        Get process instance by business key.
        
        Args:
            telegram_user_id: Telegram user ID (for authentication)
            business_key: Business key to search for (e.g., "import_-1001902150742_922705")
            active_only: Only return active (non-suspended) instances
        
        Returns:
            ProcessInstanceSchema if found, None otherwise
        """
        from camunda_client.clients.engine.schemas.query import ProcessInstanceQuerySchema
        
        client = await self._get_client(telegram_user_id)
        
        query = ProcessInstanceQuerySchema(
            business_key=business_key,
            active=active_only
        )
        
        try:
            instances = await client.get_process_instances(params=query)
            
            if instances:
                instance = instances[0]
                logger.info(
                    f"📍 Found existing process instance: {instance.id} "
                    f"(business_key={business_key})"
                )
                return instance
            else:
                logger.debug(f"No active process found for business_key={business_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying process instances: {e}")
            return None
    
    async def get_task(self, telegram_user_id: int, task_id: str) -> Optional[TaskSchema]:
        """Get specific task by ID"""
        client = await self._get_client(telegram_user_id)
        return await client.get_task(task_id)
    
    async def get_task_variables(
        self,
        telegram_user_id: int,
        task_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get form variables for task.
        
        Returns:
            List of variable dicts with keys: name, value, type, writable, valueInfo
            Returns empty list if task has no form (404 error).
        """
        client = await self._get_client(telegram_user_id)
        
        try:
            # get_task_form_variables returns dict[str, VariableValueSchema]
            variables_dict = await client.get_task_form_variables(task_id)
        except CamundaClientError as e:
            # Check if it's a "no form" error (404)
            if e.status_code == 404:
                # Check error message to confirm it's a "no form" case
                error_str = str(e)
                if "No matching rendered form" in error_str or "rendered form" in error_str.lower():
                    logger.debug(f"📝 Task {task_id} has no form - returning empty variables")
                    return []
            # Re-raise other errors
            raise
        except Exception as e:
            # Check for 404 in string representation as fallback
            error_str = str(e)
            if "404" in error_str and "No matching rendered form" in error_str:
                logger.debug(f"📝 Task {task_id} has no form - returning empty variables")
                return []
            # Re-raise other errors
            raise
        
        # Convert dict to list format expected by TaskService
        # All variables from form are writable (they're input fields)
        variables_list = []
        for var_name, var_data in variables_dict.items():
            var_dict = {
                "name": var_name,
                "value": var_data.value,
                "type": var_data.type,
                "label": var_data.label or "",  # Include label from form parsing
                "writable": True,  # All form inputs are writable
                "valueInfo": var_data.value_info or {}
            }
            variables_list.append(var_dict)
        
        logger.debug(f"📝 Retrieved {len(variables_list)} variables for task {task_id}")
        return variables_list
    
    async def get_process_definition(
        self,
        telegram_user_id: int,
        process_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get process definition details (name, description, etc.).
        
        Returns:
            Dict with process definition details or None if not found
        """
        from camunda_client.clients.engine.schemas.query import ProcessDefinitionQuerySchema
        
        client = await self._get_client(telegram_user_id)
        try:
            # Query for process definition by key (latest version)
            query = ProcessDefinitionQuerySchema(
                key=process_key,
                latest_version=True
            )
            definitions = await client.get_process_definitions(query)
            
            if not definitions:
                raise ValueError(f"No process definition found for key: {process_key}")
            
            # Get the first (and should be only) result
            definition = definitions[0]
            
            # Extract name from definition
            raw_name = definition.name if hasattr(definition, 'name') else None
            
            # If name is the same as key or not set, format the key into a readable name
            if not raw_name or raw_name == process_key:
                # Transform snake_case or kebab-case to Title Case
                # "chatbot_group_import_history" → "Chatbot Group Import History"
                display_name = process_key.replace('_', ' ').replace('-', ' ').title()
            else:
                display_name = raw_name
            
            # Extract relevant fields
            result = {
                "id": definition.id if hasattr(definition, 'id') else None,
                "key": definition.key if hasattr(definition, 'key') else process_key,
                "name": display_name,
                "raw_name": raw_name,  # Keep original for debugging
                "description": definition.description if hasattr(definition, 'description') else None,
                "version": definition.version if hasattr(definition, 'version') else None,
            }
            
            logger.debug(f"📋 Process definition loaded: {display_name}")
            return result
            
        except Exception as e:
            logger.warning(f"Could not fetch process definition for {process_key}: {e}")
            # Fallback: format key into readable name
            display_name = process_key.replace('_', ' ').replace('-', ' ').title()
            return {
                "key": process_key,
                "name": display_name,
                "description": None
            }
    
    async def get_start_form_variables(
        self,
        telegram_user_id: int,
        process_key: str
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get start form variables for process definition.
        
        Returns:
            Tuple of (variables_list, error_message)
            - If successful: (variables, None)
            - If no start form: ([], None)
            - If error: ([], error_message)
        
        Each variable dict contains: name, value, type, label, valueInfo
        """
        client = await self._get_client(telegram_user_id)
        try:
            # get_process_definition_start_form returns a dict[str, VariableValueSchema]
            # where VariableValueSchema has attributes: value, type, label, value_info
            variables_dict = await client.get_process_definition_start_form(process_key)
            
            # Convert dict to list format, preserving labels
            # var_data is ALWAYS a VariableValueSchema object (not a dict)
            variables_list = []
            for var_name, var_data in variables_dict.items():
                var_dict = {
                    "name": var_name,
                    "value": var_data.value,
                    "type": var_data.type,
                    "label": var_data.label or '',
                    "valueInfo": var_data.value_info or {}
                }
                variables_list.append(var_dict)
            
            logger.info(f"📝 Retrieved {len(variables_list)} start form variables for {process_key}")
            return (variables_list, None)
        except Exception as e:
            error_str = str(e)
            
            # Extract response data if present (for better debugging)
            response_data = None
            if "RESPONSE DATA:" in error_str:
                try:
                    # Extract the response data part
                    response_part = error_str.split("RESPONSE DATA:")[1].strip()
                    # Try to parse as JSON for better formatting
                    import json
                    if response_part.startswith("b'") or response_part.startswith('b"'):
                        # It's a bytes string representation
                        response_part = response_part[2:-1]  # Remove b' and '
                    response_data = json.loads(response_part)
                except:
                    pass
            
            # Check if it's a real error (500) vs. just no form (404)
            if "500" in error_str or "Internal Server Error" in error_str:
                logger.error(
                    f"❌ Camunda 500 Error fetching start form for process '{process_key}':\n"
                    f"   Error: {e}\n"
                    f"   Response Data: {json.dumps(response_data, indent=2) if response_data else 'N/A'}"
                )
                
                # Create user-friendly error message
                if response_data and isinstance(response_data, dict):
                    error_detail = response_data.get('error', 'Internal Server Error')
                    error_path = response_data.get('path', 'Unknown')
                    user_msg = f"Camunda server error: {error_detail} (path: {error_path})"
                else:
                    user_msg = f"Camunda server error: {error_str[:100]}"
                
                return ([], user_msg)
            else:
                logger.debug(f"No start form for process {process_key}: {e}")
                return ([], None)
    
    async def complete_task(
        self,
        telegram_user_id: int,
        task_id: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> None:
        """Complete a task with variables"""
        client = await self._get_client(telegram_user_id)
        
        logger.debug(f"📤 Raw variables for task {task_id}: {variables}")
        camunda_vars = self._format_variables(variables or {})
        logger.debug(f"📤 Formatted Camunda variables: {camunda_vars}")
        
        # Wrap variables in Camunda's expected format
        # Per OpenAPI spec: CompleteTaskDto requires variables to be wrapped
        payload = {"variables": camunda_vars}
        logger.debug(f"📤 Complete task payload: {payload}")
        
        await client.complete_task(task_id, variables=payload)
        logger.info(f"✅ Completed task {task_id} for user {telegram_user_id} with {len(variables or {})} variables")
    
    def _format_variables(self, variables: Dict[str, Any]) -> Dict:
        """Format variables for Camunda"""
        from camunda_client.types_ import VariableValueSchema
        
        formatted = {}
        for key, value in variables.items():
            if isinstance(value, bool):
                var_schema = VariableValueSchema(value=value, type="Boolean")
            elif isinstance(value, int):
                var_schema = VariableValueSchema(value=value, type="Long")
            elif isinstance(value, float):
                var_schema = VariableValueSchema(value=value, type="Double")
            else:
                var_schema = VariableValueSchema(value=str(value), type="String")
            
            # Convert to dict for JSON serialization
            formatted[key] = var_schema.model_dump()
        
        return formatted
    
    def _format_message_variables(self, message_data: Dict[str, Any], message_type: str, kb_doc_id: str) -> Dict:
        """
        Format message data for Camunda with enhanced fields for async processing, tool selection, and billing.
        
        Args:
            message_data: Enhanced message data with thread context
            message_type: Message type (GROUP_MESSAGE, DM_MESSAGE, ASSISTANT_MESSAGE)
            kb_doc_id: Document ID for ES reference
            
        Returns:
            Formatted Camunda variables
        """
        # Build enhanced message variables for async processing
        variables = {
            # === Core Identity Fields ===
            "form_chatName": self._get_chat_name(message_data),
            "form_question": message_data.get("message_text", ""),
            "config_chatID": str(message_data.get("group_id", message_data.get("user_id", ""))),
            "config_chatHumanName": message_data.get("group_name", message_data.get("sender_name", "")),  # Group name for groups, sender name for DMs
            "config_threadID": message_data.get("thread_id", ""),  # Telegram's message_thread_id for supergroup topics
            "form_replyMessageType": self._get_reply_message_type(message_type),
            
            # === NEW: Document ID for ES Reference ===
            "form_documentId": kb_doc_id,  # KEY FIELD - links to ES document
            
            # === NEW: Enhanced Message Info (JSON string) ===
            "form_tgMessageInfo": self._build_telegram_message_info(message_data, kb_doc_id),
            
            # === NEW: Tool Selection & Processing Hints ===
            "config_enabledTools": ",".join(message_data.get("enabled_tools", [])),
            "config_disabledTools": ",".join(message_data.get("disabled_tools", [])),
            "config_knowledgeBases": ",".join(message_data.get("knowledge_bases", [])),
            
            # === NEW: LLM Configuration ===
            "config_llmProvider": message_data.get("llm_provider", ""),
            "config_modelName": message_data.get("model_name", ""),
            "config_systemPrompt": message_data.get("system_prompt", ""),
            
            # === NEW: Billing & Usage Tracking ===
            "billing_userId": str(message_data.get("user_id", "")),
            "billing_messageType": message_data.get("role", "user"),
            "billing_timestamp": message_data.get("message_date", ""),
            
            # === NEW: Agent Configuration ===
            "config_agentName": message_data.get("agent_name", ""),
            "config_agentDescription": message_data.get("agent_description", ""),
            "config_threadLanguage": message_data.get("thread_language", "en"),
            
            # === NEW: Conversation Context ===
            "context_messageCount": message_data.get("message_count", 0),
            "context_conversationSummary": message_data.get("conversation_summary", ""),
            
            # === NEW: Thread Context ===
            "thread_type": message_data.get("thread_type", "dm"),
            "thread_owner_id": str(message_data.get("thread_owner_id", "")),
            "thread_name": message_data.get("thread_name", ""),
            
            # === NEW: Process Tracking ===
            "process_instance_id": message_data.get("process_instance_id", ""),
            "active_workflows": ",".join(message_data.get("active_workflows", [])),
        }
        
        return self._format_variables(variables)
    
    def _build_business_key(self, message_data: Dict[str, Any]) -> str:
        """
        Build business key for Camunda correlation.
        
        Format: group-{group_id}[-{thread_id}] or dm-{user_id}
        
        Args:
            message_data: Message data
            
        Returns:
            Business key string
        """
        if "group_id" in message_data:
            group_id = message_data["group_id"]
            thread_id = message_data.get("thread_id")
            if thread_id:
                return f"group-{group_id}-{thread_id}"
            else:
                return f"group-{group_id}"
        else:
            user_id = message_data.get("user_id", "")
            return f"dm-{user_id}"
    
    def _build_telegram_message_info(self, message_data: Dict[str, Any], kb_doc_id: str) -> str:
        """
        Build enhanced Telegram message info JSON with kb_doc_id and extended fields.
        
        Args:
            message_data: Enhanced message data with thread context
            kb_doc_id: Document ID for ES reference
            
        Returns:
            JSON string with comprehensive Telegram message info
        """
        import json
        
        # Determine message type based on reply context
        tg_message_type = "tgReply" if message_data.get("reply_to_message_id") else "tgMessage"
        
        info = {
            # === Original Fields ===
            "tg_message_text": message_data.get("message_text", ""),
            "tg_message_author_camunda_user_id": str(message_data.get("user_id", "")),
            "tg_message_type": tg_message_type,
            "tg_parent_message_text": message_data.get("parent_message_text"),
            "tg_parent_message_id": message_data.get("parent_message_id"),
            "tg_parent_message_user_tg_id": message_data.get("parent_message_user_id"),
            "tg_chat_ID": str(message_data.get("group_id", message_data.get("user_id", ""))),
            "tg_chat_human_name": message_data.get("sender_name", ""),
            "tg_chat_topic_id": message_data.get("telegram_topic_id"),  # Telegram's native topic ID
            
            # === NEW: Document References ===
            "kb_doc_id": kb_doc_id,  # KEY: ES document ID for worker reference
            "elasticsearch_index": message_data.get("_index_name"),  # Which ES index
            
            # === NEW: Message Metadata ===
            "telegram_message_id": message_data.get("_telegram_message_id"),  # Original Telegram message ID
            "message_date": message_data.get("message_date"),
            "media_type": message_data.get("media_type", "text"),  # text, photo, voice, etc.
            
            # === NEW: Mentions & Entities ===
            "mentions": message_data.get("mentions", []),  # @mentions
            "hashtags": message_data.get("hashtags", []),  # #hashtags
            "urls": message_data.get("urls", []),  # Extracted URLs
            
            # === NEW: Thread Context ===
            "thread_id": message_data.get("thread_id"),  # Luka's internal thread UUID
            "thread_type": message_data.get("thread_type", "dm"),  # dm, group, supergroup
            "thread_owner_id": str(message_data.get("thread_owner_id", "")),
            "thread_name": message_data.get("thread_name", ""),
            
            # === NEW: Agent & LLM Configuration ===
            "agent_name": message_data.get("agent_name", ""),
            "agent_description": message_data.get("agent_description", ""),
            "llm_provider": message_data.get("llm_provider", ""),
            "model_name": message_data.get("model_name", ""),
            "system_prompt": message_data.get("system_prompt", ""),
            
            # === NEW: Tool Configuration ===
            "enabled_tools": message_data.get("enabled_tools", []),
            "disabled_tools": message_data.get("disabled_tools", []),
            "knowledge_bases": message_data.get("knowledge_bases", []),
            
            # === NEW: Conversation Context ===
            "thread_language": message_data.get("thread_language", "en"),
            "conversation_summary": message_data.get("conversation_summary", ""),
            "message_count": message_data.get("message_count", 0),
            
            # === NEW: Process Tracking ===
            "process_instance_id": message_data.get("process_instance_id", ""),
            "active_workflows": message_data.get("active_workflows", []),
            
            # === NEW: Billing Context ===
            "billing_userId": str(message_data.get("user_id", "")),
            "billing_messageType": message_data.get("role", "user"),
            "billing_timestamp": message_data.get("message_date", ""),
        }
        
        return json.dumps(info)
    
    async def _build_enhanced_message_data(self, message_data: Dict[str, Any], thread: Optional["Thread"]) -> Dict[str, Any]:
        """
        Add thread context to message data.
        
        Args:
            message_data: Base message data
            thread: Optional Thread object with context
            
        Returns:
            Enhanced message data with thread context
        """
        enhanced_data = message_data.copy()
        
        if thread:
            enhanced_data.update({
                "thread_type": thread.thread_type,
                "thread_owner_id": str(thread.owner_id),
                "thread_name": thread.name,
                "agent_name": thread.agent_name or "",
                "agent_description": thread.agent_description or "",
                "llm_provider": thread.llm_provider or "",
                "model_name": thread.model_name or "",
                "system_prompt": thread.system_prompt or "",
                "enabled_tools": thread.enabled_tools or [],
                "disabled_tools": thread.disabled_tools or [],
                "knowledge_bases": thread.knowledge_bases or [],
                "thread_language": thread.language or "",
                "conversation_summary": thread.conversation_summary or "",
                "message_count": thread.message_count or 0,
                "process_instance_id": thread.process_instance_id or "",
                "active_workflows": thread.active_workflows or []
            })
        
        return enhanced_data
    
    def _get_chat_name(self, message_data: Dict[str, Any]) -> str:
        """Get chat name for Camunda form field."""
        if "group_id" in message_data:
            return f"group-{message_data['group_id']}"
        else:
            return "dm"
    
    def _get_reply_message_type(self, message_type: str) -> str:
        """Convert message type to Camunda reply message type."""
        type_mapping = {
            "GROUP_MESSAGE": "MESSAGE",
            "DM_MESSAGE": "DM", 
            "ASSISTANT_MESSAGE": "ASSISTANT"
        }
        return type_mapping.get(message_type, "MESSAGE")


# Singleton accessor
def get_camunda_service() -> CamundaService:
    """Get CamundaService singleton"""
    return CamundaService.get_instance()

