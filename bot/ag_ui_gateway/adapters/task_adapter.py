"""
Task Adapter for AG-UI Protocol

Converts Camunda tasks to AG-UI FormRequest events and handles submissions.
"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import uuid
import time
from loguru import logger

# Lazy imports to avoid circular dependencies
# Use TYPE_CHECKING for type hints only
if TYPE_CHECKING:
    from luka_bot.models.process_models import TaskVariables
# from luka_bot.services.camunda_service import get_camunda_service
# from luka_bot.services.task_service import TaskService


class AGUIFormProtocol:
    """
    AG-UI protocol form-related event types.
    
    Based on AG-UI protocol specification.
    """
    
    @staticmethod
    def form_request(
        form_id: str,
        title: str,
        description: str,
        fields: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create formRequest event.
        
        Args:
            form_id: Unique form identifier (task_id)
            title: Form title (task name)
            description: Form description
            fields: List of form field definitions
            metadata: Optional metadata (process info, etc.)
        
        Returns:
            AG-UI protocol form request event
        """
        return {
            "type": "formRequest",
            "formId": form_id,
            "title": title,
            "description": description,
            "fields": fields,
            "metadata": metadata or {},
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def form_submitted(form_id: str, success: bool = True, message: Optional[str] = None) -> Dict[str, Any]:
        """
        Create formSubmitted event.
        
        Args:
            form_id: Form identifier
            success: Whether submission succeeded
            message: Optional success/error message
        
        Returns:
            AG-UI protocol form submitted event
        """
        return {
            "type": "formSubmitted",
            "formId": form_id,
            "success": success,
            "message": message or ("Form submitted successfully" if success else "Form submission failed"),
            "timestamp": int(time.time() * 1000)
        }
    
    @staticmethod
    def state_update(status: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create stateUpdate event.
        
        Args:
            status: Current status (pending, complete, error)
            metadata: Optional metadata
        
        Returns:
            AG-UI protocol state update event
        """
        return {
            "type": "stateUpdate",
            "status": status,
            "metadata": metadata or {},
            "timestamp": int(time.time() * 1000)
        }


class TaskAdapter:
    """
    Adapter for converting Camunda tasks to AG-UI FormRequest events.
    
    Wraps luka_bot's TaskService and CamundaService to provide
    AG-UI protocol compatible task management.
    """
    
    def __init__(self):
        # Lazy initialization to avoid circular imports
        self._camunda_service = None
        self._task_service = None
    
    def _ensure_services(self):
        """Lazy load services to avoid circular imports."""
        if self._camunda_service is None:
            from luka_bot.services.camunda_service import get_camunda_service
            from luka_bot.services.task_service import TaskService
            self._camunda_service = get_camunda_service()
            self._task_service = TaskService.get_instance()
    
    @property
    def camunda_service(self):
        """Get Camunda service (lazy loaded)."""
        self._ensure_services()
        return self._camunda_service
    
    @property
    def task_service(self):
        """Get Task service (lazy loaded)."""
        self._ensure_services()
        return self._task_service
    
    def _categorize_variables(self, raw_variables: List) -> "TaskVariables":
        """
        Categorize task variables into different types.
        
        Based on luka_bot's TaskService logic:
        - text_* → Text display (read-only)
        - s3_* + writable → File upload
        - action_* + writable → Action button
        - writable → Form input
        - not writable → Text display
        
        Args:
            raw_variables: Raw variables from Camunda
        
        Returns:
            Categorized TaskVariables
        """
        text_vars = []
        action_vars = []
        form_vars = []
        s3_vars = []
        
        for var in raw_variables:
            var_dict = var.model_dump() if hasattr(var, 'model_dump') else var
            var_name = var_dict.get("name", "")
            var_writable = var_dict.get("writable", False)
            
            # Text variables (highest priority)
            if var_name.startswith("text_"):
                text_vars.append(var_dict)
            # S3 file upload variables
            elif var_name.startswith("s3_") and var_writable:
                s3_vars.append(var_dict)
            # Action variables
            elif var_name.startswith("action_") and var_writable:
                action_vars.append(var_dict)
            # Form variables (writable, not action or s3)
            elif var_writable:
                form_vars.append(var_dict)
            # Other read-only variables → text
            else:
                text_vars.append(var_dict)
        
        # Lazy import to avoid circular dependency
        from luka_bot.models.process_models import TaskVariables
        
        return TaskVariables(
            text_vars=text_vars,
            action_vars=action_vars,
            form_vars=form_vars,
            s3_vars=s3_vars
        )
    
    def _convert_to_form_fields(self, variables: "TaskVariables") -> List[Dict[str, Any]]:
        """
        Convert categorized variables to AG-UI form field definitions.
        
        Args:
            variables: Categorized task variables
        
        Returns:
            List of AG-UI form field definitions
        """
        fields = []
        
        # Text variables (display only)
        for var in variables.text_vars:
            fields.append({
                "id": var.get("name"),
                "type": "text",
                "label": var.get("name").replace("text_", "").replace("_", " ").title(),
                "value": str(var.get("value", "")),
                "readonly": True
            })
        
        # Form variables (input fields)
        for var in variables.form_vars:
            var_name = var.get("name", "")
            var_value = var.get("value")
            var_type = var.get("type", "String")
            
            # Determine field type based on variable type
            field_type = "text"
            if var_type == "Boolean":
                field_type = "checkbox"
            elif var_type == "Integer" or var_type == "Long":
                field_type = "number"
            elif var_type == "Date":
                field_type = "date"
            
            fields.append({
                "id": var_name,
                "type": field_type,
                "label": var_name.replace("_", " ").title(),
                "value": var_value,
                "required": True,
                "readonly": False
            })
        
        # S3 file upload variables
        for var in variables.s3_vars:
            fields.append({
                "id": var.get("name"),
                "type": "file",
                "label": var.get("name").replace("s3_", "").replace("_", " ").title(),
                "value": None,
                "required": True,
                "readonly": False,
                "accept": "*/*"  # Accept all file types
            })
        
        # Action variables (buttons)
        for var in variables.action_vars:
            fields.append({
                "id": var.get("name"),
                "type": "button",
                "label": var.get("name").replace("action_", "").replace("_", " ").title(),
                "value": var.get("value"),
                "action": "submit"
            })
        
        return fields
    
    async def get_user_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all tasks for a user.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            List of task summaries
        """
        try:
            tasks = await self.camunda_service.get_user_tasks(user_id)
            
            task_list = []
            for task in tasks:
                task_list.append({
                    "id": task.id,
                    "name": task.name,
                    "description": task.description or "",
                    "created": task.created.isoformat() if task.created else None,
                    "due": task.due.isoformat() if task.due else None,
                    "assignee": task.assignee,
                    "process_instance_id": str(task.process_instance_id)
                })
            
            logger.info(f"📋 Retrieved {len(task_list)} tasks for user {user_id}")
            return task_list
            
        except Exception as e:
            # Gracefully handle errors (e.g., no Camunda credentials, guest users)
            logger.warning(f"⚠️  Could not get tasks for user {user_id}: {e}")
            logger.debug(f"   This is normal for guest users or users without Camunda access")
            return []  # Return empty list instead of failing
    
    async def get_task_form(self, user_id: int, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task as AG-UI FormRequest event.
        
        Args:
            user_id: Telegram user ID
            task_id: Camunda task ID
        
        Returns:
            AG-UI FormRequest event or None if task not found
        """
        try:
            # Get task details
            task = await self.camunda_service.get_task(user_id, task_id)
            if not task:
                logger.warning(f"⚠️  Task {task_id} not found for user {user_id}")
                return None
            
            # Get task variables
            raw_variables = await self.camunda_service.get_task_variables(user_id, task_id)
            variables = self._categorize_variables(raw_variables)
            
            logger.info(
                f"📋 Task {task_id} ({task.name}): "
                f"{len(variables.text_vars)} text, "
                f"{len(variables.action_vars)} action, "
                f"{len(variables.form_vars)} form, "
                f"{len(variables.s3_vars)} s3"
            )
            
            # Convert to form fields
            fields = self._convert_to_form_fields(variables)
            
            # Get process definition name
            process_definition_name = None
            try:
                client = await self.camunda_service._get_client(user_id)
                process_instance = await client.get_process_instance(
                    str(task.process_instance_id)
                )
                if process_instance:
                    process_definition_name = process_instance.process_definition_name
            except Exception as e:
                logger.debug(f"Could not fetch process definition name: {e}")
            
            # Build metadata
            metadata = {
                "task_id": task_id,
                "process_instance_id": str(task.process_instance_id),
                "process_definition_name": process_definition_name,
                "assignee": task.assignee,
                "created": task.created.isoformat() if task.created else None,
                "due": task.due.isoformat() if task.due else None
            }
            
            # Return AG-UI FormRequest event
            return AGUIFormProtocol.form_request(
                form_id=task_id,
                title=task.name,
                description=task.description or "",
                fields=fields,
                metadata=metadata
            )
            
        except Exception as e:
            logger.warning(f"⚠️  Could not get task form {task_id} for user {user_id}: {e}")
            logger.debug(f"   This is normal for guest users or users without Camunda access")
            return None
    
    async def submit_task_form(
        self,
        user_id: int,
        task_id: str,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit task form to Camunda.
        
        Args:
            user_id: Telegram user ID
            task_id: Camunda task ID
            form_data: Form data (field_id -> value mapping)
        
        Returns:
            AG-UI formSubmitted event
        """
        try:
            logger.info(f"📤 Submitting task {task_id} for user {user_id}")
            
            # Convert form data to Camunda variable format
            variables = {}
            for field_id, value in form_data.items():
                # Skip action buttons (they're not variables to submit)
                if field_id.startswith("action_"):
                    continue
                
                # Determine variable type
                var_type = "String"
                if isinstance(value, bool):
                    var_type = "Boolean"
                elif isinstance(value, int):
                    var_type = "Integer"
                elif isinstance(value, float):
                    var_type = "Double"
                
                variables[field_id] = {
                    "value": value,
                    "type": var_type
                }
            
            # Submit to Camunda
            success = await self.camunda_service.complete_task(
                user_id=user_id,
                task_id=task_id,
                variables=variables
            )
            
            if success:
                logger.info(f"✅ Task {task_id} completed successfully")
                return AGUIFormProtocol.form_submitted(
                    form_id=task_id,
                    success=True,
                    message="Task completed successfully"
                )
            else:
                logger.error(f"❌ Task {task_id} completion failed")
                return AGUIFormProtocol.form_submitted(
                    form_id=task_id,
                    success=False,
                    message="Task completion failed"
                )
            
        except Exception as e:
            logger.error(f"❌ Error submitting task {task_id}: {e}")
            return AGUIFormProtocol.form_submitted(
                form_id=task_id,
                success=False,
                message=f"Error: {str(e)}"
            )


# Singleton instance
_task_adapter: Optional[TaskAdapter] = None


def get_task_adapter() -> TaskAdapter:
    """Get or create TaskAdapter singleton."""
    global _task_adapter
    if _task_adapter is None:
        _task_adapter = TaskAdapter()
        logger.info("✅ TaskAdapter singleton created")
    return _task_adapter

