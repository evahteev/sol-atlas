"""
Process Definition Cache Service.

Loads and caches process definitions from Camunda at bot startup.
Used to dynamically enable/disable features based on deployed processes.
"""
from typing import Optional, Dict, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class ProcessDefinitionInfo:
    """Cached process definition metadata"""
    key: str
    name: str
    description: Optional[str]
    version: int
    id: str


class ProcessDefinitionCache:
    """
    Singleton cache for process definitions.

    Loaded once at bot startup from Camunda, used to:
    - Check if a process exists before trying to start it
    - Get process metadata (name, description) without API calls
    - Conditionally enable UI elements based on deployed processes
    """

    _instance: Optional['ProcessDefinitionCache'] = None

    def __init__(self):
        self._definitions: Dict[str, ProcessDefinitionInfo] = {}
        self._loaded: bool = False

    @classmethod
    def get_instance(cls) -> 'ProcessDefinitionCache':
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("✅ ProcessDefinitionCache singleton created")
        return cls._instance

    async def load_definitions(self, telegram_user_id: int) -> None:
        """
        Load all process definitions from Camunda.

        Args:
            telegram_user_id: Any valid user ID for authentication

        Note:
            This should be called once at bot startup.
            Uses system admin credentials for loading definitions.
        """
        from camunda_client.clients.engine.client import CamundaEngineClient
        from camunda_client.clients.dto import AuthData
        from camunda_client.clients.engine.schemas.query import ProcessDefinitionQuerySchema
        from luka_bot.core.config import settings
        import httpx

        try:
            # Use system admin credentials for loading process definitions
            auth_data = AuthData(
                username=settings.ENGINE_USERNAME,
                password=settings.ENGINE_PASSWORD
            )
            
            transport = httpx.AsyncHTTPTransport(
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            
            client = CamundaEngineClient(
                base_url=settings.ENGINE_URL,
                auth_data=auth_data,
                transport=transport
            )

            # Query for all latest versions of process definitions
            query = ProcessDefinitionQuerySchema(
                latest_version=True,
                active=True  # Only active (not suspended) definitions
            )

            definitions = await client.get_process_definitions(query)

            # Cache each definition
            for definition in definitions:
                # Extract name (with fallback formatting)
                raw_name = definition.name if hasattr(definition, 'name') else None
                process_key = definition.key if hasattr(definition, 'key') else None

                if not process_key:
                    logger.warning(f"Skipping definition without key: {definition}")
                    continue

                # Format name if not set or same as key
                if not raw_name or raw_name == process_key:
                    display_name = process_key.replace('_', ' ').replace('-', ' ').title()
                else:
                    display_name = raw_name

                # Cache definition info
                info = ProcessDefinitionInfo(
                    key=process_key,
                    name=display_name,
                    description=definition.description if hasattr(definition, 'description') else None,
                    version=definition.version if hasattr(definition, 'version') else 1,
                    id=definition.id if hasattr(definition, 'id') else process_key
                )

                self._definitions[process_key] = info
                logger.debug(f"📦 Cached process definition: {process_key} (v{info.version}) - {display_name}")

            self._loaded = True
            logger.info(f"✅ Loaded {len(self._definitions)} process definitions from Camunda")

            # Log available definitions
            if self._definitions:
                logger.info(f"📋 Available processes: {', '.join(self._definitions.keys())}")
            else:
                logger.warning("⚠️  No process definitions found in Camunda")
            
            # Clean up the client
            await client.close()

        except Exception as e:
            logger.error(f"❌ Failed to load process definitions from Camunda: {e}")
            logger.warning("⚠️  Process-based features will be disabled")
            self._loaded = False

    def is_loaded(self) -> bool:
        """Check if definitions have been loaded"""
        return self._loaded

    def has_process(self, process_key: str) -> bool:
        """
        Check if a process definition exists.

        Args:
            process_key: Process definition key (e.g., "chatbot_start")

        Returns:
            True if process exists in Camunda
        """
        return process_key in self._definitions

    def get_process_info(self, process_key: str) -> Optional[ProcessDefinitionInfo]:
        """
        Get cached process definition info.

        Args:
            process_key: Process definition key

        Returns:
            ProcessDefinitionInfo if exists, None otherwise
        """
        return self._definitions.get(process_key)

    def get_all_processes(self) -> List[ProcessDefinitionInfo]:
        """Get all cached process definitions"""
        return list(self._definitions.values())

    def get_process_name(self, process_key: str) -> str:
        """
        Get formatted process name.

        Args:
            process_key: Process definition key

        Returns:
            Display name if cached, formatted key otherwise
        """
        info = self._definitions.get(process_key)
        if info:
            return info.name

        # Fallback: format key
        return process_key.replace('_', ' ').replace('-', ' ').title()

    def get_chatbot_processes(self) -> List[ProcessDefinitionInfo]:
        """
        Get all chatbot_* process definitions.

        Returns:
            List of chatbot processes (chatbot_start, chatbot_profile, chatbot_groups, etc.)
        """
        return [
            info for key, info in self._definitions.items()
            if key.startswith('chatbot_')
        ]


def get_process_definition_cache() -> ProcessDefinitionCache:
    """Get ProcessDefinitionCache singleton"""
    return ProcessDefinitionCache.get_instance()
