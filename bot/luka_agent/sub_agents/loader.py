"""
Sub-Agent Loader for luka_agent

Loads BMAD-compatible sub-agent configurations and system prompts.
Supports template variable substitution and multi-language prompts.

Usage:
    loader = SubAgentLoader()
    config = loader.load("general_luka")
    prompt = loader.load_system_prompt(config, language="en", template_vars={...})
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


class SubAgentConfig:
    """BMAD-compatible sub-agent configuration"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.raw = config_dict
        self.agent = config_dict.get("agent", {})
        self.luka_extensions = config_dict.get("luka_extensions", {})

    # BMAD Core Fields
    @property
    def metadata(self) -> Dict[str, Any]:
        return self.agent.get("metadata", {})

    @property
    def id(self) -> str:
        return self.metadata.get("id", "unknown")

    @property
    def name(self) -> str:
        return self.metadata.get("name", "Unknown Agent")

    @property
    def title(self) -> str:
        return self.metadata.get("title", self.name)

    @property
    def icon(self) -> str:
        return self.metadata.get("icon", "🤖")

    @property
    def version(self) -> str:
        return self.metadata.get("version", "1.0.0")

    @property
    def description(self) -> str:
        return self.metadata.get("description", "")

    @property
    def persona(self) -> Dict[str, Any]:
        return self.agent.get("persona", {})

    @property
    def role(self) -> str:
        return self.persona.get("role", "Assistant")

    @property
    def identity(self) -> str:
        return self.persona.get("identity", "")

    @property
    def communication_style(self) -> str:
        return self.persona.get("communication_style", "")

    @property
    def principles(self) -> List[str]:
        return self.persona.get("principles", [])

    @property
    def menu(self) -> List[Any]:
        return self.agent.get("menu", [])

    # Luka Extensions
    @property
    def system_prompt_config(self) -> Dict[str, Any]:
        return self.luka_extensions.get("system_prompt", {})

    @property
    def system_prompt_base(self) -> str:
        return self.system_prompt_config.get("base", "")

    @property
    def language_variants(self) -> Dict[str, str]:
        return self.system_prompt_config.get("language_variants", {})

    @property
    def template_vars(self) -> Dict[str, str]:
        return self.system_prompt_config.get("template_vars", {})

    @property
    def enabled_tools(self) -> List[str]:
        return self.luka_extensions.get("enabled_tools", [])

    @property
    def knowledge_bases(self) -> List[str]:
        return self.luka_extensions.get("knowledge_bases", [])

    @property
    def llm_config(self) -> Dict[str, Any]:
        return self.luka_extensions.get("llm_config", {})

    @property
    def capabilities(self) -> Dict[str, Any]:
        return self.luka_extensions.get("capabilities", {})

    @property
    def intent_triggers(self) -> List[str]:
        return self.luka_extensions.get("intent_triggers", [])

    def to_dict(self) -> Dict[str, Any]:
        """Return full config as dictionary"""
        return self.raw


class SubAgentLoader:
    """
    Loads sub-agent configurations from YAML files.

    Supports:
    - BMAD-compatible config structure
    - Template variable substitution
    - Multi-language system prompts
    - Configuration validation
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            base_path: Path to sub_agents directory. If None, uses current file's parent directory.
        """
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = Path(base_path)
        logger.debug(f"SubAgentLoader initialized with base_path: {self.base_path}")

    def list_available_agents(self) -> List[Dict[str, str]]:
        """
        List all available sub-agents.

        Returns:
            List of dicts with {id, name, description, icon}
        """
        agents = []

        for sub_dir in self.base_path.iterdir():
            if not sub_dir.is_dir():
                continue

            # Skip template and hidden directories
            if sub_dir.name.startswith(".") or sub_dir.name == "TEMPLATE":
                continue

            config_path = sub_dir / "config.yaml"
            if not config_path.exists():
                continue

            try:
                config = self.load(sub_dir.name)
                agents.append({
                    "id": config.id,
                    "name": config.name,
                    "description": config.description,
                    "icon": config.icon,
                })
            except Exception as e:
                logger.warning(f"Failed to load agent {sub_dir.name}: {e}")
                continue

        return agents

    def load(self, sub_agent_id: str) -> SubAgentConfig:
        """
        Load sub-agent configuration from YAML.

        Args:
            sub_agent_id: Sub-agent directory name (e.g., "general_luka")

        Returns:
            SubAgentConfig instance

        Raises:
            FileNotFoundError: If config.yaml doesn't exist
            ValueError: If config is invalid
        """
        config_path = self.base_path / sub_agent_id / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(
                f"Sub-agent config not found: {config_path}\n"
                f"Available agents: {[d.name for d in self.base_path.iterdir() if d.is_dir()]}"
            )

        logger.debug(f"Loading sub-agent config from: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_path}: {e}")

        # Validate structure
        self._validate_config(config_dict, sub_agent_id)

        config = SubAgentConfig(config_dict)
        logger.info(f"✅ Loaded sub-agent: {config.name} ({config.id}) v{config.version}")

        return config

    def load_system_prompt(
        self,
        config: SubAgentConfig,
        language: str = "en",
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Load and render system prompt with template variables.

        Args:
            config: SubAgentConfig instance
            language: Language code (e.g., "en", "ru")
            template_vars: Variables for template substitution

        Returns:
            Rendered system prompt string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Determine prompt file path
        prompt_path = self._get_prompt_path(config, language)

        if not prompt_path.exists():
            # Fall back to base prompt if language variant not found
            logger.warning(
                f"Language variant '{language}' not found for {config.id}, falling back to base prompt"
            )
            base_path = self.base_path / config.id / config.system_prompt_base.split("/")[-1]
            if not base_path.exists():
                raise FileNotFoundError(f"System prompt not found: {base_path}")
            prompt_path = base_path

        logger.debug(f"Loading system prompt from: {prompt_path}")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
        except Exception as e:
            raise FileNotFoundError(f"Failed to read system prompt from {prompt_path}: {e}")

        # Render template with variables
        rendered = self._render_template(template, config, template_vars or {})

        logger.debug(f"✅ Loaded system prompt for {config.id} ({language}): {len(rendered)} chars")

        return rendered

    def _get_prompt_path(self, config: SubAgentConfig, language: str) -> Path:
        """
        Get path to system prompt file for given language.

        Args:
            config: SubAgentConfig instance
            language: Language code

        Returns:
            Path to prompt file
        """
        # Check for language variant first
        if language in config.language_variants:
            variant_path = config.language_variants[language]
            # Convert relative path to absolute
            return self.base_path.parent / variant_path

        # Fall back to base prompt
        if config.system_prompt_base:
            return self.base_path.parent / config.system_prompt_base

        # Last resort: look for system_prompt.md in agent directory
        return self.base_path / config.id / "system_prompt.md"

    def _render_template(
        self,
        template: str,
        config: SubAgentConfig,
        runtime_vars: Dict[str, Any],
    ) -> str:
        """
        Render template with variable substitution.

        Supports:
        - {metadata.name} - Access config fields
        - {user_name} - Runtime variables
        - {persona.identity} - Multi-level access

        Args:
            template: Template string
            config: SubAgentConfig for metadata access
            runtime_vars: Runtime variables (user_name, platform, etc.)

        Returns:
            Rendered string
        """
        # Build variable context
        context = {
            "metadata": config.metadata,
            "persona": config.persona,
            "agent_name": config.name,
            **runtime_vars,
        }

        # Replace template variables
        def replace_var(match):
            var_path = match.group(1)
            value = self._get_nested_value(context, var_path)
            return str(value) if value is not None else match.group(0)

        # Pattern: {variable} or {object.field}
        rendered = re.sub(r"\{([a-zA-Z0-9_.]+)\}", replace_var, template)

        return rendered

    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from dict using dot notation.

        Examples:
            _get_nested_value({"a": {"b": 1}}, "a.b") → 1
            _get_nested_value({"x": 2}, "x") → 2

        Args:
            obj: Dictionary to search
            path: Dot-separated path (e.g., "persona.role")

        Returns:
            Value at path, or None if not found
        """
        parts = path.split(".")
        current = obj

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _validate_config(self, config_dict: Dict[str, Any], sub_agent_id: str) -> None:
        """
        Validate sub-agent configuration structure.

        Args:
            config_dict: Loaded YAML config
            sub_agent_id: Agent ID for error messages

        Raises:
            ValueError: If config is invalid
        """
        errors = []

        # Check BMAD core structure
        if "agent" not in config_dict:
            errors.append("Missing 'agent' section (BMAD core)")
        else:
            agent = config_dict["agent"]

            # Check metadata
            if "metadata" not in agent:
                errors.append("Missing 'agent.metadata' section")
            else:
                metadata = agent["metadata"]
                required_metadata = ["id", "name", "title", "icon", "version", "description"]
                for field in required_metadata:
                    if field not in metadata:
                        errors.append(f"Missing required field: agent.metadata.{field}")

                # Validate ID matches directory name
                if metadata.get("id") != sub_agent_id:
                    logger.warning(
                        f"Agent ID '{metadata.get('id')}' doesn't match directory name '{sub_agent_id}'"
                    )

            # Check persona
            if "persona" not in agent:
                errors.append("Missing 'agent.persona' section")
            else:
                persona = agent["persona"]
                required_persona = ["role", "identity", "communication_style", "principles"]
                for field in required_persona:
                    if field not in persona:
                        errors.append(f"Missing required field: agent.persona.{field}")

        # Check luka_extensions
        if "luka_extensions" not in config_dict:
            errors.append("Missing 'luka_extensions' section")
        else:
            extensions = config_dict["luka_extensions"]

            required_extensions = ["system_prompt", "enabled_tools", "knowledge_bases", "llm_config"]
            for field in required_extensions:
                if field not in extensions:
                    errors.append(f"Missing required field: luka_extensions.{field}")

            # Check system_prompt structure
            if "system_prompt" in extensions:
                sp = extensions["system_prompt"]
                if "base" not in sp:
                    errors.append("Missing required field: luka_extensions.system_prompt.base")

            # Check llm_config structure
            if "llm_config" in extensions:
                llm = extensions["llm_config"]
                required_llm = ["provider", "model", "temperature"]
                for field in required_llm:
                    if field not in llm:
                        errors.append(f"Missing required field: luka_extensions.llm_config.{field}")

        if errors:
            error_msg = f"Invalid config for sub-agent '{sub_agent_id}':\n"
            error_msg += "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

        logger.debug(f"✅ Config validation passed for {sub_agent_id}")


# Singleton instance
_loader: Optional[SubAgentLoader] = None


def get_sub_agent_loader(base_path: Optional[Path] = None) -> SubAgentLoader:
    """
    Get singleton SubAgentLoader instance.

    Args:
        base_path: Path to sub_agents directory (only used on first call)

    Returns:
        SubAgentLoader instance
    """
    global _loader
    if _loader is None:
        _loader = SubAgentLoader(base_path)
    return _loader
