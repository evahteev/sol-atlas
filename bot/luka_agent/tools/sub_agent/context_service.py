"""
Workflow context service for Luka bot.
Provides rich workflow summaries and step guidance for dialog agents.
"""

from typing import Dict, Optional
from loguru import logger

from luka_agent.tools.sub_agent.discovery_service import (
    WorkflowDiscoveryService,
    WorkflowDefinition,
    get_workflow_discovery_service,
)


class WorkflowContextService:
    """Service for providing workflow context to Luka agents."""

    def __init__(self, discovery_service: Optional[WorkflowDiscoveryService] = None):
        self._discovery_service = discovery_service or get_workflow_discovery_service()
        self._context_cache: Dict[str, str] = {}

    async def ensure_discovery_initialized(self) -> None:
        """Initialize discovery service if not already run."""
        if self._discovery_service and not self._discovery_service.is_discovery_completed():
            await self._discovery_service.initialize()

    async def get_workflow_context(self, domain: str, include_documentation: bool = True) -> Optional[str]:
        """Get comprehensive workflow context for LLM agents."""
        if not self._discovery_service:
            logger.warning("No discovery service available for workflow context")
            return None

        await self.ensure_discovery_initialized()

        cache_key = f"{domain}:{'full' if include_documentation else 'basic'}"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]

        workflow = self._discovery_service.get_workflow(domain)
        if not workflow:
            logger.warning(f"Workflow '{domain}' not found")
            return None

        context = workflow.get_full_context() if include_documentation else self._generate_basic_context(workflow)
        self._context_cache[cache_key] = context
        logger.debug(f"Generated workflow context for '{domain}': {len(context)} characters")

        return context

    def _generate_basic_context(self, workflow: WorkflowDefinition) -> str:
        """Generate basic workflow context without documentation."""
        context_parts = [
            f"# {workflow.name}",
            f"Domain: {workflow.domain}",
            f"Description: {workflow.description}",
        ]

        if workflow.estimated_duration:
            context_parts.append(f"Duration: {workflow.estimated_duration}")

        persona = workflow.persona
        if persona:
            context_parts.append(f"Role: {persona.get('role', 'Assistant')}")
            context_parts.append(f"Style: {persona.get('style', 'Professional')}")

        steps = workflow.tool_chain.get("steps", [])
        if steps:
            context_parts.append(f"\nSteps ({len(steps)}):")
            for i, step in enumerate(steps, 1):
                context_parts.append(f"{i}. {step.get('name', f'Step {i}')}")

        return "\n".join(context_parts)

    async def get_all_workflows_summary(self) -> str:
        """Get summary of all available workflows for LLM context."""
        if not self._discovery_service:
            return "No workflow discovery service available."

        await self.ensure_discovery_initialized()

        workflows = self._discovery_service.get_all_workflows()
        if not workflows:
            return "No workflows currently available."

        summary_parts = ["# Available Workflows\n"]

        for domain, workflow in workflows.items():
            summary_parts.append(f"## {workflow.name} (`{domain}`)")
            summary_parts.append(f"**Description:** {workflow.description}")

            if workflow.estimated_duration:
                summary_parts.append(f"**Duration:** {workflow.estimated_duration}")

            persona = workflow.persona
            if persona:
                summary_parts.append(f"**Role:** {persona.get('role', 'Assistant')}")

            steps = workflow.tool_chain.get("steps", [])
            summary_parts.append(f"**Steps:** {len(steps)} workflow steps")

            tools = workflow.validation.get("required_tools", [])
            if tools:
                summary_parts.append(f"**Tools:** {', '.join(tools)}")

            summary_parts.append("")

        return "\n".join(summary_parts)

    async def get_workflow_for_user_intent(self, user_query: str) -> Optional[str]:
        """Suggest workflow based on user query/intent."""
        if not self._discovery_service:
            return None

        await self.ensure_discovery_initialized()

        workflows = self._discovery_service.get_all_workflows()
        if not workflows:
            return None

        query_lower = user_query.lower()
        workflow_keywords = {
            "development": ["develop", "project", "plan", "architecture", "code", "programming", "software"],
            "psychology": ["reflect", "goal", "personal", "growth", "therapy", "coaching", "values"],
            "defi_onboarding": ["defi", "wallet", "crypto", "dex", "onboard"],
        }

        best_match = None
        best_score = 0

        for domain, keywords in workflow_keywords.items():
            if domain not in workflows:
                continue
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > best_score:
                best_score = score
                best_match = domain

        if best_match:
            return await self.get_workflow_context(best_match, include_documentation=True)

        return None

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._context_cache.clear()
        logger.debug("Workflow context cache cleared")

    async def get_workflow_step_guidance(self, domain: str, step_id: str) -> Optional[str]:
        """Get detailed guidance for a specific workflow step."""
        if not self._discovery_service:
            return None

        await self.ensure_discovery_initialized()

        workflow = self._discovery_service.get_workflow(domain)
        if not workflow:
            return None

        steps = workflow.tool_chain.get("steps", [])
        target_step = next((step for step in steps if step.get("id") == step_id), None)
        if not target_step:
            logger.warning(f"Step '{step_id}' not found in workflow '{domain}'")
            return None

        guidance_parts = [
            f"# Step: {target_step.get('name', step_id)}",
            f"**Type:** {target_step.get('type', 'unknown')}",
            f"**Instruction:** {target_step.get('instruction', 'No instruction provided')}",
        ]

        inputs = target_step.get("inputs", []) or target_step.get("required_inputs", [])
        if inputs:
            if isinstance(inputs[0], dict):
                input_names = [inp.get("name", "input") for inp in inputs]
                guidance_parts.append(f"**Inputs:** {', '.join(input_names)}")
            else:
                guidance_parts.append(f"**Inputs:** {', '.join(inputs)}")

        outputs = target_step.get("outputs", []) or target_step.get("artifacts", [])
        if outputs:
            if isinstance(outputs[0], dict):
                output_names = [out.get("name", "output") for out in outputs]
                guidance_parts.append(f"**Outputs:** {', '.join(output_names)}")
            else:
                guidance_parts.append(f"**Outputs:** {', '.join(outputs)}")

        tools = target_step.get("tools", [])
        if tools:
            guidance_parts.append(f"**Tools:** {', '.join(tools)}")

        persona = workflow.persona
        if persona:
            guidance_parts.append("\n**Persona Guidance:**")
            guidance_parts.append(f"Approach as: {persona.get('role', 'Assistant')}")
            guidance_parts.append(f"Style: {persona.get('style', 'Professional')}")

        return "\n".join(guidance_parts)

    def get_discovery_service(self) -> Optional[WorkflowDiscoveryService]:
        """Expose underlying discovery service."""
        return self._discovery_service


_workflow_context_service: Optional[WorkflowContextService] = None


def get_workflow_context_service() -> WorkflowContextService:
    """Get or create workflow context service singleton."""
    global _workflow_context_service

    if _workflow_context_service is None:
        _workflow_context_service = WorkflowContextService()
        logger.info("✅ WorkflowContextService singleton created")

    return _workflow_context_service
