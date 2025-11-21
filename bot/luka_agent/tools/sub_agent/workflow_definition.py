"""
Pydantic schema definitions for Luka dialog workflows.
Ported from bot_server with adjustments for Luka bot architecture.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class StepType(str, Enum):
    """Available step types for workflow execution."""
    CONVERSATIONAL = "conversational"
    TOOL_ASSISTED = "tool_assisted"
    EXTERNAL_INTEGRATION = "external_integration"
    CONDITIONAL = "conditional"


class WorkflowMetadata(BaseModel):
    """Workflow metadata with required and optional fields."""
    domain: str = Field(..., description="Workflow domain (development, psychology, etc.)")
    name: str = Field(..., description="Human-readable workflow name")
    version: str = Field(..., description="Version for change management")
    description: str = Field(..., description="Workflow purpose and outcomes")
    entry_conditions: Optional[List[str]] = Field(
        default_factory=list,
        description="Prerequisites for workflow execution"
    )
    estimated_duration: Optional[str] = Field(
        None,
        description="Expected completion time (e.g., '20-30 minutes')"
    )

    @field_validator('domain')
    def validate_domain(cls, v):
        """Validate domain follows naming conventions."""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Domain must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()

    @field_validator('version')
    def validate_version(cls, v):
        """Validate version follows semantic versioning."""
        import re
        if not re.match(r'^\d+\.\d+(\.\d+)?$', v):
            raise ValueError("Version must follow semantic versioning (e.g., '1.0' or '1.0.0')")
        return v


class WorkflowPersona(BaseModel):
    """Conversational persona configuration for domain-specific style."""
    role: str = Field(..., description="Conversational persona (e.g., 'Technical Architect')")
    style: str = Field(..., description="Conversation style and tone")
    expertise_areas: Optional[List[str]] = Field(
        default_factory=list,
        description="Domain expertise keywords"
    )

    @field_validator('role')
    def validate_role(cls, v):
        """Ensure role is meaningful."""
        if len(v.strip()) < 3:
            raise ValueError("Role must be at least 3 characters long")
        return v.strip()

    @field_validator('style')
    def validate_style(cls, v):
        """Ensure style is descriptive."""
        if len(v.strip()) < 10:
            raise ValueError("Style description must be at least 10 characters long")
        return v.strip()


class StepInput(BaseModel):
    """Input specification for workflow steps."""
    name: str = Field(..., description="Input parameter name")
    type: str = Field(..., description="Input data type (string, number, object, etc.)")
    required: bool = Field(True, description="Whether this input is required")
    description: Optional[str] = Field(None, description="Input description")
    default: Optional[Any] = Field(None, description="Default value if not provided")
    source: Optional[str] = Field(None, description="Source of the input (previous_step, user_input, context)")


class StepOutput(BaseModel):
    """Output specification for workflow steps."""
    name: str = Field(..., description="Output artifact name")
    type: str = Field(..., description="Output data type")
    description: Optional[str] = Field(None, description="Output description")
    format: Optional[str] = Field(None, description="Output format specification")
    required: bool = Field(True, description="Whether this output is always generated")


class StepConditional(BaseModel):
    """Conditional execution logic for workflow steps."""
    condition: str = Field(..., description="Condition expression to evaluate")
    true_step: Optional[str] = Field(None, description="Step ID to execute if condition is true")
    false_step: Optional[str] = Field(None, description="Step ID to execute if condition is false")
    variables: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Variables available for condition evaluation"
    )


class WorkflowStep(BaseModel):
    """Individual step in a workflow tool chain."""
    id: str = Field(..., description="Unique step identifier")
    name: str = Field(..., description="Human-readable step name")
    type: StepType = Field(..., description="Step execution type")
    instruction: str = Field(..., description="Step execution guidance")
    required_inputs: Optional[List[str]] = Field(
        default_factory=list,
        description="Inputs needed from previous steps (legacy field)"
    )
    inputs: Optional[List[StepInput]] = Field(
        default_factory=list,
        description="Detailed input specifications"
    )
    outputs: Optional[List[StepOutput]] = Field(
        default_factory=list,
        description="Detailed output specifications"
    )
    tools: Optional[List[str]] = Field(
        default_factory=list,
        description="Bot tools to invoke"
    )
    integration: Optional[str] = Field(
        None,
        description="External system integration (e.g., 'camunda')"
    )
    process_key: Optional[str] = Field(
        None,
        description="Process key for external integrations"
    )
    artifacts: Optional[List[str]] = Field(
        default_factory=list,
        description="Outputs generated by step (legacy field)"
    )
    conditional: Optional[StepConditional] = Field(
        None,
        description="Conditional execution logic"
    )
    timeout: Optional[int] = Field(
        None,
        description="Step timeout in seconds"
    )
    retry_count: Optional[int] = Field(
        0,
        description="Number of retry attempts on failure"
    )

    @field_validator('id')
    def validate_id(cls, v):
        """Ensure step ID follows naming conventions."""
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', v):
            raise ValueError("Step ID must start with lowercase letter and contain only lowercase letters, numbers, and underscores")
        return v

    @field_validator('instruction')
    def validate_instruction(cls, v):
        """Ensure instruction is meaningful."""
        if len(v.strip()) < 10:
            raise ValueError("Step instruction must be at least 10 characters long")
        return v.strip()

    @model_validator(mode='after')
    def validate_step_configuration(self):
        """Validate step configuration based on type."""
        step_type = self.type
        tools = self.tools or []
        integration = self.integration
        conditional = self.conditional

        if step_type == StepType.TOOL_ASSISTED and not tools:
            raise ValueError("tool_assisted steps must specify at least one tool")

        if step_type == StepType.EXTERNAL_INTEGRATION and not integration:
            raise ValueError("external_integration steps must specify integration type")

        if step_type == StepType.CONDITIONAL and not conditional:
            raise ValueError("conditional steps must specify conditional logic")

        return self


class WorkflowToolChain(BaseModel):
    """Tool chain definition with sequential workflow steps."""
    steps: List[WorkflowStep] = Field(..., description="Sequential workflow steps")

    @field_validator('steps')
    def validate_steps(cls, v):
        """Validate step sequence and dependencies."""
        if not v:
            raise ValueError("Tool chain must have at least one step")

        # Check for duplicate step IDs
        step_ids = [step.id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("All step IDs must be unique")

        # Validate step dependencies
        available_artifacts = set()
        for step in v:
            # Check required inputs are available from previous steps
            for required_input in step.required_inputs or []:
                if required_input not in available_artifacts and required_input not in ["user_input", "context"]:
                    raise ValueError(f"Step '{step.id}' requires input '{required_input}' not provided by previous steps")

            # Add this step's artifacts to available set
            available_artifacts.update(step.artifacts or [])

        return v


class WorkflowValidation(BaseModel):
    """Validation configuration for workflow execution."""
    required_tools: List[str] = Field(..., description="Bot tools that must be available")
    prerequisites: Optional[List[str]] = Field(
        default_factory=list,
        description="System or user prerequisites"
    )
    success_criteria: List[str] = Field(..., description="Workflow completion validation")

    @field_validator('required_tools')
    def validate_required_tools(cls, v):
        """Validate required tools list."""
        # Empty list is valid - some workflows are purely conversational
        return v

    @field_validator('success_criteria')
    def validate_success_criteria(cls, v):
        """Ensure success criteria are defined."""
        if not v:
            raise ValueError("At least one success criterion must be specified")
        return v


class WorkflowDefinitionSchema(BaseModel):
    """Complete workflow definition schema."""
    workflow: 'WorkflowConfig' = Field(..., description="Main workflow configuration")

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True
    )


class WorkflowConfig(BaseModel):
    """Main workflow configuration container."""
    metadata: WorkflowMetadata = Field(..., description="Workflow metadata")
    persona: WorkflowPersona = Field(..., description="Conversational persona configuration")
    tool_chain: WorkflowToolChain = Field(..., description="Sequential workflow steps")
    validation: WorkflowValidation = Field(..., description="Validation requirements")

    @model_validator(mode='after')
    def validate_workflow_consistency(self):
        """Validate overall workflow consistency."""
        tool_chain = self.tool_chain
        validation = self.validation

        if not tool_chain or not validation:
            return self

        # Collect all tools used in steps
        used_tools = set()
        for step in tool_chain.steps:
            used_tools.update(step.tools or [])
            if step.integration:
                used_tools.add(f"{step.integration}_integration")

        # Check required tools are actually used
        required_tools = set(validation.required_tools)
        unused_tools = required_tools - used_tools
        if unused_tools:
            # This is a warning, not an error - tools might be used in other ways
            pass

        # Check used tools are declared as required
        undeclared_tools = used_tools - required_tools
        if undeclared_tools:
            # Some tools like basic conversation tools might not need declaration
            standard_tools = {"web_search", "knowledge_base", "support"}
            problematic_tools = undeclared_tools - standard_tools
            if problematic_tools:
                raise ValueError(f"Tools used in steps but not declared as required: {list(problematic_tools)}")

        return self


# Update forward references
WorkflowDefinitionSchema.model_rebuild()
