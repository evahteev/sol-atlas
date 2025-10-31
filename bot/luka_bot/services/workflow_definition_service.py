"""
Workflow definition validation service for Luka bot dialog workflows.
Ported from bot_server implementation with adjustments for Luka architecture.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml
from loguru import logger
from pydantic import ValidationError as PydanticValidationError

from luka_bot.schemas.workflow_definition import WorkflowDefinitionSchema, StepType
from luka_bot.core.loader import redis_client


class ValidationError(Exception):
    """Custom validation error with detailed information."""

    def __init__(self, message: str, errors: List[Dict[str, Any]] = None, line_number: int = None):
        super().__init__(message)
        self.errors = errors or []
        self.line_number = line_number
        self.message = message


class WorkflowDefinitionService:
    """Service for validating workflow definitions using Pydantic schemas."""

    VALIDATION_CACHE_TTL = 3600  # 1 hour cache TTL for validation results
    PERFORMANCE_CACHE_TTL = 86400  # 24 hours for stable workflows

    def __init__(self, redis_cache=None):
        """Initialize workflow definition service."""
        self._redis_cache = redis_cache or redis_client
        self._validation_stats = {
            "total_validated": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "cache_hits": 0,
            "validation_duration": 0.0,
        }

    async def validate_workflow_file(
        self,
        domain: str,
        config_path: Path,
        use_cache: bool = True,
    ) -> Tuple[bool, Optional[WorkflowDefinitionSchema], List[Dict[str, Any]]]:
        """
        Validate a workflow definition file.

        Args:
            domain: Workflow domain name
            config_path: Path to the config.yaml file
            use_cache: Whether to use cached validation results

        Returns:
            Tuple of (is_valid, validated_schema, errors)
        """
        start_time = asyncio.get_event_loop().time()

        # Ensure config_path is a Path object
        if isinstance(config_path, str):
            config_path = Path(config_path)

        try:
            # Check cache first
            if use_cache and self._redis_cache:
                cached_result = await self._get_cached_validation(domain, config_path)
                if cached_result:
                    self._validation_stats["cache_hits"] += 1
                    return cached_result

            # Read and parse YAML
            config_content = await self._read_yaml_file(config_path)
            config_data = yaml.safe_load(config_content)

            if not config_data:
                error = {
                    "type": "empty_file",
                    "message": "Workflow configuration file is empty",
                    "domain": domain,
                    "file": str(config_path),
                }
                await self._cache_validation_result(domain, config_path, (False, None, [error]))
                return False, None, [error]

            # Perform validation
            is_valid, validated_schema, errors = await self._validate_config_data(domain, config_data, config_path)

            # Update statistics
            self._validation_stats["total_validated"] += 1
            if is_valid:
                self._validation_stats["successful_validations"] += 1
            else:
                self._validation_stats["failed_validations"] += 1

            # Cache result
            if use_cache:
                await self._cache_validation_result(domain, config_path, (is_valid, validated_schema, errors))

            duration = asyncio.get_event_loop().time() - start_time
            self._validation_stats["validation_duration"] += duration

            logger.debug(
                f"Validated workflow {domain} in {duration:.3f}s: "
                f"{'✓' if is_valid else '✗'} ({len(errors)} errors)"
            )

            return is_valid, validated_schema, errors

        except Exception as e:
            logger.error(f"Unexpected error validating workflow {domain}: {e}")
            error = {
                "type": "validation_error",
                "message": f"Unexpected validation error: {str(e)}",
                "domain": domain,
                "file": str(config_path),
            }
            return False, None, [error]

    async def _validate_config_data(
        self,
        domain: str,
        config_data: Dict[str, Any],
        config_path: Path,
    ) -> Tuple[bool, Optional[WorkflowDefinitionSchema], List[Dict[str, Any]]]:
        """Validate configuration data using Pydantic schema."""

        errors = []

        try:
            # Basic structure validation
            structural_errors = await self._validate_structure(domain, config_data)
            errors.extend(structural_errors)

            if any(err.get("level") == "error" for err in structural_errors):
                # If structure has blocking errors, don't proceed with Pydantic validation
                return False, None, errors

            # Pydantic schema validation
            try:
                validated_schema = WorkflowDefinitionSchema(**config_data)

                # Semantic validation
                semantic_errors = await self._validate_semantics(domain, validated_schema)
                errors.extend(semantic_errors)

                # Tool compatibility validation
                tool_errors = await self._validate_tool_compatibility(domain, validated_schema)
                errors.extend(tool_errors)

                # Performance validation
                performance_warnings = await self._validate_performance(domain, validated_schema)
                errors.extend(performance_warnings)

                is_valid = len([e for e in errors if e.get("level") == "error"]) == 0

                return is_valid, validated_schema, errors

            except PydanticValidationError as e:
                # Convert Pydantic validation errors to our format
                pydantic_errors = self._convert_pydantic_errors(domain, e, str(config_path))
                errors.extend(pydantic_errors)
                return False, None, errors

        except Exception as e:
            error = {
                "type": "schema_validation_error",
                "level": "error",
                "message": f"Schema validation failed: {str(e)}",
                "domain": domain,
                "file": str(config_path),
            }
            errors.append(error)
            return False, None, errors

    async def _validate_structure(self, domain: str, config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate basic workflow structure."""
        errors = []

        # Check required top-level keys
        if "workflow" not in config_data:
            errors.append(
                {
                    "type": "missing_key",
                    "level": "error",
                    "message": "Missing required 'workflow' key at root level",
                    "domain": domain,
                    "suggestion": "Add 'workflow:' section to your configuration",
                }
            )
            return errors

        workflow_config = config_data["workflow"]

        # Check required workflow sections
        required_sections = ["metadata", "persona", "tool_chain", "validation"]
        for section in required_sections:
            if section not in workflow_config:
                errors.append(
                    {
                        "type": "missing_section",
                        "level": "error",
                        "message": f"Missing required workflow.{section} section",
                        "domain": domain,
                        "suggestion": f"Add workflow.{section} to your configuration",
                    }
                )

        # Provide warnings for optional sections
        optional_sections = ["instructions", "resources", "metadata"]
        for section in optional_sections:
            if section not in workflow_config:
                errors.append(
                    {
                        "type": "missing_optional_section",
                        "level": "warning",
                        "message": f"Optional workflow.{section} section is missing",
                        "domain": domain,
                        "suggestion": f"Consider adding workflow.{section} for richer context",
                    }
                )

        return errors

    async def _validate_semantics(
        self,
        domain: str,
        validated_schema: WorkflowDefinitionSchema,
    ) -> List[Dict[str, Any]]:
        """Perform semantic validation of workflow configuration."""
        errors = []
        workflow = validated_schema.workflow

        # Validate persona expertise matches domain keywords
        persona = workflow.persona
        if persona.expertise_areas:
            domain_keywords = workflow.metadata.domain.split("_")
            matching_keywords = [kw for kw in persona.expertise_areas if kw.replace("-", "_") in domain_keywords]
            if not matching_keywords:
                errors.append(
                    {
                        "type": "persona_domain_mismatch",
                        "level": "warning",
                        "message": "Persona expertise areas do not reference workflow domain keywords",
                        "domain": domain,
                        "suggestion": "Consider aligning persona expertise_areas with workflow domain for better relevance",
                    }
                )

        # Validate step sequence coverage
        steps = workflow.tool_chain.steps
        if steps:
            # Check first step is conversational for dialog workflows
            first_step = steps[0]
            if first_step.type != StepType.CONVERSATIONAL:
                errors.append(
                    {
                        "type": "first_step_not_conversational",
                        "level": "warning",
                        "message": "First workflow step is not conversational",
                        "domain": domain,
                        "suggestion": "Consider starting with a conversational step for better user engagement",
                    }
                )

            # Check final step success criteria alignment
            final_step = steps[-1]
            if final_step.type == StepType.EXTERNAL_INTEGRATION and workflow.validation.success_criteria:
                errors.append(
                    {
                        "type": "final_step_external",
                        "level": "warning",
                        "message": "Final step delegates to external integration",
                        "domain": domain,
                        "suggestion": "Ensure success criteria include external completion verification",
                    }
                )

        return errors

    async def _validate_tool_compatibility(
        self,
        domain: str,
        validated_schema: WorkflowDefinitionSchema,
    ) -> List[Dict[str, Any]]:
        """Validate workflow tool requirements."""
        errors = []

        available_tools: List[str] = []

        try:
            # Lazy import to avoid circular dependency during startup
            from luka_bot.services.tool_registry import get_available_tool_names  # type: ignore

            maybe_tools = get_available_tool_names()
            if asyncio.iscoroutine(maybe_tools):
                available_tools = await maybe_tools
            else:
                available_tools = maybe_tools or []
        except Exception:
            # Tool registry optional during early integration; skip compatibility enforcement
            available_tools = []

        required_tools = validated_schema.workflow.validation.required_tools
        missing_tools = [tool for tool in required_tools if tool not in available_tools]

        if missing_tools:
            errors.append(
                {
                    "type": "missing_tools",
                    "level": "warning",
                    "message": f"Required tools not registered: {missing_tools}",
                    "domain": domain,
                    "suggestion": "Ensure these tools are registered or update workflow.validation.required_tools",
                }
            )

        return errors

    async def _validate_performance(
        self,
        domain: str,
        validated_schema: WorkflowDefinitionSchema,
    ) -> List[Dict[str, Any]]:
        """Evaluate workflow performance characteristics."""
        warnings = []

        steps = validated_schema.workflow.tool_chain.steps
        if len(steps) > 20:
            warnings.append(
                {
                    "type": "long_workflow",
                    "level": "warning",
                    "message": f"Workflow has {len(steps)} steps; consider simplifying for better UX",
                    "domain": domain,
                }
            )

        tool_steps = [step for step in steps if step.type == StepType.TOOL_ASSISTED]
        if len(tool_steps) > 10:
            warnings.append(
                {
                    "type": "tool_heavy_workflow",
                    "level": "warning",
                    "message": f"Workflow has {len(tool_steps)} tool-assisted steps; ensure tool rate limits are acceptable",
                    "domain": domain,
                }
            )

        return warnings

    def _convert_pydantic_errors(
        self,
        domain: str,
        error: PydanticValidationError,
        file_path: str,
    ) -> List[Dict[str, Any]]:
        """Convert Pydantic validation errors to structured format."""
        converted = []
        for err in error.errors():
            converted.append(
                {
                    "type": err.get("type", "validation_error"),
                    "level": "error",
                    "message": err.get("msg", "Validation error"),
                    "domain": domain,
                    "file": file_path,
                    "location": ".".join(str(loc) for loc in err.get("loc", [])),
                }
            )
        return converted

    async def _read_yaml_file(self, path: Path) -> str:
        """Read YAML file asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, path.read_text)

    async def _get_cached_validation(
        self,
        domain: str,
        config_path: Path,
    ) -> Optional[Tuple[bool, Optional[WorkflowDefinitionSchema], List[Dict[str, Any]]]]:
        """Retrieve cached validation result from Redis."""
        if not self._redis_cache:
            return None

        cache_key = self._get_cache_key(domain, config_path)

        try:
            cached_data = await self._redis_cache.get(cache_key)
        except Exception as exc:  # pragma: no cover - redis optional
            logger.debug(f"Skipping workflow validation cache due to Redis error: {exc}")
            self._redis_cache = None
            return None

        if cached_data:
            try:
                import json

                data = json.loads(cached_data)
                if data.get("schema"):
                    validated_schema = WorkflowDefinitionSchema(**data["schema"])
                else:
                    validated_schema = None
                return data["is_valid"], validated_schema, data.get("errors", [])
            except Exception as e:
                logger.warning(f"Failed to deserialize cached validation result for {domain}: {e}")
                return None

        return None

    async def _cache_validation_result(
        self,
        domain: str,
        config_path: Path,
        result: Tuple[bool, Optional[WorkflowDefinitionSchema], List[Dict[str, Any]]],
    ) -> None:
        """Cache validation result in Redis."""
        if not self._redis_cache:
            return

        cache_key = self._get_cache_key(domain, config_path)
        is_valid, schema, errors = result

        try:
            import json

            payload = {
                "is_valid": is_valid,
                "schema": schema.model_dump(mode="json") if schema else None,
                "errors": errors,
            }

            try:
                await self._redis_cache.setex(
                    cache_key,
                    self.VALIDATION_CACHE_TTL,
                    json.dumps(payload),
                )
            except Exception as exc:  # pragma: no cover - redis optional
                logger.debug(f"Unable to cache workflow validation result: {exc}")
                self._redis_cache = None
        except Exception as e:
            logger.warning(f"Failed to cache validation result for {domain}: {e}")

    def _get_cache_key(self, domain: str, config_path: Path) -> str:
        """Generate cache key for workflow validation."""
        return f"workflow_validation:{domain}:{config_path}"

    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return self._validation_stats.copy()

    def format_validation_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format validation errors for human-readable output."""
        if not errors:
            return "No validation errors found."

        formatted: List[str] = []
        error_groups: Dict[str, List[Dict[str, Any]]] = {"error": [], "warning": [], "info": []}

        for error in errors:
            level = error.get("level", "error")
            error_groups.setdefault(level, []).append(error)

        for level, level_errors in error_groups.items():
            if not level_errors:
                continue

            formatted.append(f"\n{level.upper()}S ({len(level_errors)}):")
            for error in level_errors:
                formatted.append(f"  • {error.get('message', 'Unknown issue')}")
                if error.get("suggestion"):
                    formatted.append(f"    → {error['suggestion']}")

        return "\n".join(formatted)


# Singleton
_workflow_definition_service: Optional[WorkflowDefinitionService] = None


def get_workflow_definition_service() -> WorkflowDefinitionService:
    """Get or create workflow definition service singleton."""
    global _workflow_definition_service

    if _workflow_definition_service is None:
        _workflow_definition_service = WorkflowDefinitionService()
        logger.info("✅ WorkflowDefinitionService singleton created")

    return _workflow_definition_service
