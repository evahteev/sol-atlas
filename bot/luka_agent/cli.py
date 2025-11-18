#!/usr/bin/env python3
"""
luka_agent CLI Tool

Commands:
    list                    - List all available sub-agents
    validate <agent_id>     - Validate sub-agent configuration
    test <agent_id> <msg>   - Test sub-agent with a message
    info <agent_id>         - Show sub-agent details

Usage:
    python -m luka_agent.cli list
    python -m luka_agent.cli validate general_luka
    python -m luka_agent.cli test general_luka "Hello, who are you?"
    python -m luka_agent.cli info crypto_analyst
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# Configure logger for CLI
logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
)


def list_agents():
    """List all available sub-agents"""
    from luka_agent.sub_agents.loader import get_sub_agent_loader

    loader = get_sub_agent_loader()
    agents = loader.list_available_agents()

    if not agents:
        logger.error("No sub-agents found")
        return

    logger.info(f"Found {len(agents)} sub-agent(s):\n")

    for agent in agents:
        print(f"{agent['icon']}  {agent['name']} ({agent['id']})")
        print(f"   {agent['description']}")
        print()


def validate_agent(agent_id: str):
    """Validate sub-agent configuration"""
    from luka_agent.sub_agents.loader import get_sub_agent_loader

    loader = get_sub_agent_loader()

    try:
        logger.info(f"Validating sub-agent: {agent_id}")

        # Load config (validates structure)
        config = loader.load(agent_id)

        # Load system prompt
        prompt = loader.load_system_prompt(
            config,
            language="en",
            template_vars={
                "user_name": "Test User",
                "platform": "cli",
                "language": "en",
            },
        )

        # Print validation results
        logger.success(f"✅ Configuration valid for '{agent_id}'")
        print()
        print(f"Agent: {config.name} {config.icon}")
        print(f"ID: {config.id}")
        print(f"Version: {config.version}")
        print(f"Description: {config.description}")
        print()
        print(f"Role: {config.role}")
        print(f"Enabled Tools: {', '.join(config.enabled_tools)}")
        print(f"Knowledge Bases: {', '.join(config.knowledge_bases)}")
        print(f"LLM: {config.llm_config.get('provider')}/{config.llm_config.get('model')}")
        print(f"Temperature: {config.llm_config.get('temperature')}")
        print()
        print(f"System Prompt: {len(prompt)} characters")
        print(f"Principles: {len(config.principles)}")
        print()

        # Check for common issues
        warnings = []

        if not config.enabled_tools:
            warnings.append("No tools enabled")

        if not config.knowledge_bases:
            warnings.append("No knowledge bases configured")

        if not config.principles:
            warnings.append("No principles defined")

        if len(prompt) < 500:
            warnings.append("System prompt seems short (< 500 chars)")

        if len(prompt) > 20000:
            warnings.append("System prompt is very long (> 20k chars)")

        if warnings:
            logger.warning("Warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
            print()

        logger.success("Validation complete!")

    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ Validation failed:\n{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


def show_info(agent_id: str):
    """Show detailed information about sub-agent"""
    from luka_agent.sub_agents.loader import get_sub_agent_loader

    loader = get_sub_agent_loader()

    try:
        config = loader.load(agent_id)
        prompt = loader.load_system_prompt(
            config,
            language="en",
            template_vars={
                "user_name": "Test User",
                "platform": "cli",
                "language": "en",
            },
        )

        print("=" * 70)
        print(f"{config.icon}  {config.name} - {config.title}")
        print("=" * 70)
        print()

        print(f"ID: {config.id}")
        print(f"Version: {config.version}")
        print(f"Description: {config.description}")
        print()

        print("PERSONA")
        print("-" * 70)
        print(f"Role: {config.role}")
        print()
        print("Identity:")
        for line in config.identity.strip().split("\n"):
            print(f"  {line}")
        print()
        print(f"Communication Style: {config.communication_style}")
        print()

        print("Principles:")
        for i, principle in enumerate(config.principles, 1):
            print(f"  {i}. {principle}")
        print()

        print("CONFIGURATION")
        print("-" * 70)
        print(f"Enabled Tools ({len(config.enabled_tools)}):")
        for tool in config.enabled_tools:
            print(f"  - {tool}")
        print()

        print(f"Knowledge Bases ({len(config.knowledge_bases)}):")
        for kb in config.knowledge_bases:
            print(f"  - {kb}")
        print()

        print("LLM Configuration:")
        llm = config.llm_config
        print(f"  Provider: {llm.get('provider')}")
        print(f"  Model: {llm.get('model')}")
        print(f"  Temperature: {llm.get('temperature')}")
        print(f"  Max Tokens: {llm.get('max_tokens', 'default')}")
        print(f"  Streaming: {llm.get('streaming', True)}")
        print()

        if config.capabilities:
            print("CAPABILITIES")
            print("-" * 70)
            caps = config.capabilities

            if "data_access" in caps:
                data_access = caps["data_access"]
                if "allowed_kb_patterns" in data_access:
                    print("Allowed KB Patterns:")
                    for pattern in data_access["allowed_kb_patterns"]:
                        print(f"  ✅ {pattern}")
                if "forbidden_kb_patterns" in data_access:
                    print("Forbidden KB Patterns:")
                    for pattern in data_access["forbidden_kb_patterns"]:
                        print(f"  ❌ {pattern}")
                print()

            if "features" in caps:
                print("Features:")
                for feature, enabled in caps["features"].items():
                    icon = "✅" if enabled else "❌"
                    print(f"  {icon} {feature}")
                print()

        print("SYSTEM PROMPT")
        print("-" * 70)
        print(f"Size: {len(prompt)} characters")
        print(f"Base: {config.system_prompt_base}")
        if config.language_variants:
            print("Language Variants:")
            for lang, path in config.language_variants.items():
                print(f"  - {lang}: {path}")
        print()

        print("Preview (first 500 chars):")
        print("-" * 70)
        print(prompt[:500])
        if len(prompt) > 500:
            print("...")
        print()

        print("=" * 70)

    except Exception as e:
        logger.error(f"❌ Error loading agent info: {e}")
        sys.exit(1)


def test_agent(agent_id: str, message: str):
    """Test sub-agent with a message (mock LLM response)"""
    from luka_agent.sub_agents.loader import get_sub_agent_loader

    loader = get_sub_agent_loader()

    try:
        logger.info(f"Testing sub-agent: {agent_id}")

        # Load config and prompt
        config = loader.load(agent_id)
        prompt = loader.load_system_prompt(
            config,
            language="en",
            template_vars={
                "user_name": "Test User",
                "platform": "cli",
                "language": "en",
            },
        )

        logger.success(f"✅ Loaded {config.name}")
        print()

        # Display test setup
        print("=" * 70)
        print(f"TESTING: {config.name} {config.icon}")
        print("=" * 70)
        print()
        print(f"User Message: {message}")
        print()
        print("System Prompt (preview):")
        print("-" * 70)
        # Show first 1000 chars of system prompt
        print(prompt[:1000])
        if len(prompt) > 1000:
            print(f"... ({len(prompt) - 1000} more characters)")
        print()
        print("=" * 70)
        print()

        # Show what tools would be available
        print("Available Tools:")
        for tool in config.enabled_tools:
            print(f"  - {tool}")
        print()

        print("Knowledge Bases:")
        for kb in config.knowledge_bases:
            print(f"  - {kb}")
        print()

        # Mock LLM configuration that would be used
        print("LLM Configuration:")
        print(f"  Provider: {config.llm_config.get('provider')}")
        print(f"  Model: {config.llm_config.get('model')}")
        print(f"  Temperature: {config.llm_config.get('temperature')}")
        print()

        logger.success("✅ Test setup complete!")
        logger.info(
            "This is a mock test showing configuration. "
            "To test with actual LLM, integrate with luka_agent graph."
        )

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)


def print_usage():
    """Print usage information"""
    print(__doc__)


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_agents()

    elif command == "validate":
        if len(sys.argv) < 3:
            logger.error("Usage: python -m luka_agent.cli validate <agent_id>")
            sys.exit(1)
        agent_id = sys.argv[2]
        validate_agent(agent_id)

    elif command == "test":
        if len(sys.argv) < 4:
            logger.error('Usage: python -m luka_agent.cli test <agent_id> "message"')
            sys.exit(1)
        agent_id = sys.argv[2]
        message = sys.argv[3]
        test_agent(agent_id, message)

    elif command == "info":
        if len(sys.argv) < 3:
            logger.error("Usage: python -m luka_agent.cli info <agent_id>")
            sys.exit(1)
        agent_id = sys.argv[2]
        show_info(agent_id)

    elif command in ["--help", "-h", "help"]:
        print_usage()

    else:
        logger.error(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
