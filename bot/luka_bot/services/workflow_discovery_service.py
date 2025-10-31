"""
Workflow discovery service for Luka bot dialog workflows.
Discovers YAML workflow definitions, validates them, and exposes metadata.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterable
from datetime import datetime, timedelta
import yaml
from loguru import logger

from luka_bot.services.workflow_definition_service import (
    WorkflowDefinitionService,
    get_workflow_definition_service,
)


class WorkflowDefinition:
    """Container for workflow metadata, configuration, and documentation."""

    def __init__(
        self,
        domain: str,
        config: Dict[str, Any],
        validated_schema: Optional[Any] = None,
        documentation: Optional[str] = None,
    ):
        self.domain = domain
        self.config = config
        self.validated_schema = validated_schema
        self.documentation = documentation
        self.metadata = config.get("workflow", {}).get("metadata", {})
        self.name = self.metadata.get("name", domain)
        self.version = self.metadata.get("version", "1.0.0")
        self.description = self.metadata.get("description", "")
        self.estimated_duration = self.metadata.get("estimated_duration", "")
        self.tool_chain = config.get("workflow", {}).get("tool_chain", {})
        self.validation = config.get("workflow", {}).get("validation", {})
        self.persona = config.get("workflow", {}).get("persona", {})
        self.is_valid = validated_schema is not None

    def get_full_context(self) -> str:
        """Get complete workflow context for LLM including documentation."""
        context_parts = []

        # Basic workflow information
        context_parts.append(f"# Workflow: {self.name}")
        context_parts.append(f"**Domain:** {self.domain}")
        context_parts.append(f"**Version:** {self.version}")
        context_parts.append(f"**Description:** {self.description}")
        if self.estimated_duration:
            context_parts.append(f"**Duration:** {self.estimated_duration}")

        # Persona information
        persona = self.persona
        if persona:
            context_parts.append("\n## Conversational Persona")
            context_parts.append(f"**Role:** {persona.get('role', 'Assistant')}")
            context_parts.append(f"**Style:** {persona.get('style', 'Professional')}")
            expertise = persona.get("expertise_areas", [])
            if expertise:
                context_parts.append(f"**Expertise:** {', '.join(expertise)}")

        # Tool chain overview
        steps = self.tool_chain.get("steps", [])
        if steps:
            context_parts.append(f"\n## Workflow Steps ({len(steps)} steps)")
            for i, step in enumerate(steps, 1):
                step_name = step.get("name", f"Step {i}")
                step_type = step.get("type", "unknown")
                context_parts.append(f"{i}. **{step_name}** ({step_type})")

        # Validation requirements
        validation = self.validation
        if validation:
            tools = validation.get("required_tools", [])
            if tools:
                context_parts.append(f"\n**Required Tools:** {', '.join(tools)}")

            criteria = validation.get("success_criteria", [])
            if criteria:
                context_parts.append(f"**Success Criteria:** {'; '.join(criteria)}")

        # Rich documentation if available
        if self.documentation:
            context_parts.append(f"\n## Detailed Documentation\n{self.documentation}")

        return "\n".join(context_parts)

    def __repr__(self):
        return f"<WorkflowDefinition domain={self.domain} name={self.name} version={self.version}>"


class WorkflowDiscoveryService:
    """Service for discovering and registering workflow definitions from filesystem."""

    WORKFLOW_BASE_PATHS: Iterable[Path] = (
        Path("luka_bot/agents/tools/workflows"),
        Path("dialog-workflows/workflows"),
        Path("bot_server/agents/tools/workflows"),
    )
    CONFIG_FILENAME = "config.yaml"
    DOCUMENTATION_FILENAME = "README.md"
    DISCOVERY_TIMEOUT = 2.0  # seconds

    def __init__(self, validation_service: Optional[WorkflowDefinitionService] = None):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._discovery_completed = False
        self._discovery_start_time: Optional[float] = None
        self._discovery_duration: Optional[float] = None
        self._cached_workflows: Dict[str, WorkflowDefinition] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)
        self._validation_service = validation_service or get_workflow_definition_service()
        self._validation_errors: Dict[str, List[Dict[str, Any]]] = {}

    async def discover_workflows(self) -> Dict[str, WorkflowDefinition]:
        """
        Scan workflow directories and discover workflow definitions.
        Returns dictionary keyed by workflow domain.
        """
        self._discovery_start_time = asyncio.get_event_loop().time()

        try:
            if self._is_cache_valid():
                logger.debug("Using cached workflow definitions for Luka workflows")
                return self._cached_workflows

            logger.info("Starting workflow discovery process for Luka bot")
            self._workflows.clear()
            self._validation_errors.clear()

            discovery_tasks = []
            for base_path in self._iter_existing_paths():
                for domain_dir in base_path.iterdir():
                    if not domain_dir.is_dir() or domain_dir.name.startswith("."):
                        continue

                    config_path = domain_dir / self.CONFIG_FILENAME
                    if config_path.exists():
                        task = asyncio.create_task(self._load_workflow_definition(domain_dir.name, config_path))
                        discovery_tasks.append(task)

            if discovery_tasks:
                await asyncio.wait_for(asyncio.gather(*discovery_tasks, return_exceptions=True), timeout=self.DISCOVERY_TIMEOUT)

            self._discovery_duration = asyncio.get_event_loop().time() - self._discovery_start_time
            logger.info(
                f"Workflow discovery completed in {self._discovery_duration:.2f}s "
                f"with {len(self._workflows)} workflow(s) available"
            )

            self._cached_workflows = self._workflows.copy()
            self._cache_timestamp = datetime.now()
            self._discovery_completed = True
            return self._workflows

        except asyncio.TimeoutError:
            self._discovery_duration = self.DISCOVERY_TIMEOUT
            logger.warning(
                f"Workflow discovery timeout after {self.DISCOVERY_TIMEOUT}s. "
                f"Loaded {len(self._workflows)} workflows before timeout"
            )
            return self._workflows
        except Exception as e:
            logger.error(f"Error during workflow discovery: {e}")
            return {}

    def _iter_existing_paths(self) -> Iterable[Path]:
        """Yield base paths that exist on disk."""
        for path in self.WORKFLOW_BASE_PATHS:
            if path.exists():
                yield path

    async def _load_workflow_definition(self, domain: str, config_path: Path) -> None:
        """Load and validate a single workflow definition."""
        try:
            is_valid, validated_schema, errors = await self._validation_service.validate_workflow_file(
                domain, config_path, use_cache=True
            )
            self._validation_errors[domain] = errors

            if errors:
                error_count = len([e for e in errors if e.get("level") == "error"])
                warning_count = len([e for e in errors if e.get("level") == "warning"])
                if error_count > 0:
                    logger.error(
                        f"Workflow {domain} validation failed with {error_count} errors, {warning_count} warnings"
                    )
                    if logger.level <= 10:
                        logger.debug(
                            f"Validation errors for {domain}:\n"
                            f"{self._validation_service.format_validation_errors(errors)}"
                        )
                elif warning_count:
                    logger.warning(f"Workflow {domain} has {warning_count} validation warnings")

            if not is_valid:
                logger.warning(f"Skipping invalid workflow: {domain}")
                return

            loop = asyncio.get_event_loop()
            config_content = await loop.run_in_executor(None, config_path.read_text)
            config = yaml.safe_load(config_content)
            documentation = await self._load_workflow_documentation(config_path.parent)

            workflow = WorkflowDefinition(domain, config, validated_schema, documentation)
            self._workflows[domain] = workflow
            logger.debug(f"Loaded workflow definition: {workflow}")

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error for workflow {domain}: {e}")
            self._validation_errors[domain] = [
                {
                    "type": "yaml_error",
                    "level": "error",
                    "message": f"YAML parse error: {str(e)}",
                    "domain": domain,
                }
            ]
        except Exception as e:
            logger.error(f"Error loading workflow {domain}: {e}")
            self._validation_errors[domain] = [
                {
                    "type": "loading_error",
                    "level": "error",
                    "message": f"Loading error: {str(e)}",
                    "domain": domain,
                }
            ]

    async def _load_workflow_documentation(self, domain_path: Path) -> Optional[str]:
        """Load README documentation for workflow if present."""
        readme_path = domain_path / self.DOCUMENTATION_FILENAME
        if not readme_path.exists():
            return None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, readme_path.read_text)

    def _is_cache_valid(self) -> bool:
        """Check if cached discovery results are still valid."""
        if not self._cache_timestamp or not self._cached_workflows:
            return False
        return datetime.now() - self._cache_timestamp < self._cache_ttl

    def get_workflow(self, domain: str) -> Optional[WorkflowDefinition]:
        """Get a specific workflow by domain."""
        return self._workflows.get(domain)

    def get_all_workflows(self) -> Dict[str, WorkflowDefinition]:
        """Get all discovered workflows."""
        return self._workflows.copy()

    async def initialize(self) -> bool:
        """Initialize discovery service by running discovery."""
        try:
            await self.discover_workflows()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WorkflowDiscoveryService: {e}")
            return False

    async def get_available_workflows(self) -> Dict[str, WorkflowDefinition]:
        """Alias for get_all_workflows used by other services."""
        return self.get_all_workflows()

    def get_workflow_domains(self) -> List[str]:
        """List all workflow domains discovered."""
        return list(self._workflows.keys())

    def is_discovery_completed(self) -> bool:
        """Return True if discovery has run at least once."""
        return self._discovery_completed

    def get_discovery_stats(self) -> Dict[str, Any]:
        """Collect discovery and validation statistics."""
        validation_stats = (
            self._validation_service.get_validation_stats() if self._validation_service else {}
        )

        total_domains_found = len(self._validation_errors)
        valid_workflows = len([w for w in self._workflows.values() if w.is_valid])
        invalid_workflows = total_domains_found - valid_workflows

        return {
            "completed": self._discovery_completed,
            "workflow_count": len(self._workflows),
            "discovery_duration": self._discovery_duration,
            "domains": self.get_workflow_domains(),
            "cache_valid": self._is_cache_valid(),
            "cache_timestamp": self._cache_timestamp.isoformat() if self._cache_timestamp else None,
            "validation": {
                "total_domains_found": total_domains_found,
                "valid_workflows": valid_workflows,
                "invalid_workflows": invalid_workflows,
                "validation_service_stats": validation_stats,
            },
        }

    def get_validation_errors(self, domain: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get validation errors for workflows."""
        if domain:
            return {domain: self._validation_errors.get(domain, [])}
        return self._validation_errors.copy()

    def get_validation_report(self) -> str:
        """Generate human-readable validation report."""
        if not self._validation_errors:
            return "No workflow validation results available."

        report: List[str] = ["Workflow Validation Report", "=" * 30, ""]

        for domain, errors in self._validation_errors.items():
            workflow = self._workflows.get(domain)
            status = "✓ VALID" if workflow and workflow.is_valid else "✗ INVALID"
            report.append(f"{domain}: {status}")

            if errors:
                formatted_errors = self._validation_service.format_validation_errors(errors)
                report.append(formatted_errors)
            else:
                report.append("  No validation issues found.")

            report.append("")

        return "\n".join(report)


# Singleton accessor ---------------------------------------------------------

_workflow_discovery_service: Optional[WorkflowDiscoveryService] = None


def get_workflow_discovery_service() -> WorkflowDiscoveryService:
    """Get or create workflow discovery service singleton."""
    global _workflow_discovery_service

    if _workflow_discovery_service is None:
        _workflow_discovery_service = WorkflowDiscoveryService()
        logger.info("✅ WorkflowDiscoveryService singleton created")

    return _workflow_discovery_service
