#!/usr/bin/env python3
"""
luka_agent CLI Tool

Commands:
    list                            - List all available sub-agents
    validate <agent_id>             - Validate sub-agent configuration
    test <agent_id> <msg>           - Test sub-agent with a message (mock, no LLM)
    run <agent_id> <msg> [options]  - Run sub-agent with actual LLM invocation
    info <agent_id>                 - Show sub-agent details
    help, --help, -h                - Show this help message

Run Command Options:
    --model <model>       Override LLM model
                          Examples: gpt-4o, llama3.2, claude-sonnet-4
                          Default: From .env (DEFAULT_LLM_MODEL) or llama3.2

    --provider <provider> Override LLM provider
                          Options: ollama, openai, anthropic
                          Default: From .env (DEFAULT_LLM_PROVIDER) or ollama

    --memory <type>       Checkpointer type for state persistence
                          Options: memory (in-memory), redis (persistent)
                          Default: memory (no Redis required)

    --with-suggestions    Enable suggestions generation
                          (Disabled by default in CLI mode)

Usage Examples:
    # List and validate
    python -m luka_agent.cli list
    python -m luka_agent.cli validate general_luka
    python -m luka_agent.cli info general_luka

    # Test without LLM
    python -m luka_agent.cli test general_luka "Hello, who are you?"

    # Run with defaults (in-memory, env settings)
    python -m luka_agent.cli run general_luka "What can you help me with?"

    # Override model and provider
    python -m luka_agent.cli run general_luka "Hello" --model gpt-4o --provider openai

    # Use Redis for state persistence
    python -m luka_agent.cli run general_luka "Hello" --memory redis

    # Enable suggestions
    python -m luka_agent.cli run general_luka "Hello" --with-suggestions

    # Combine multiple options
    python -m luka_agent.cli run general_luka "Hello" \
        --model claude-sonnet-4 \
        --provider anthropic \
        --memory redis \
        --with-suggestions

Environment Configuration:
    Create a .env file in the luka_agent directory with:

    # LLM Settings
    OLLAMA_URL=http://localhost:11434/v1
    DEFAULT_LLM_PROVIDER=ollama
    DEFAULT_LLM_MODEL=llama3.2

    # Memory/Checkpointer
    LUKA_USE_MEMORY_CHECKPOINTER=true  # true = in-memory, false = Redis

    # Redis (only if using Redis checkpointer)
    REDIS_HOST=localhost
    REDIS_PORT=6379

    # Tools
    CLI_ENABLED_TOOLS=knowledge_base,sub_agent,youtube,image_description,support

    See .env.example for complete configuration options.

For More Information:
    - CLI_USAGE.md - Detailed CLI documentation
    - README.md - Architecture and development guide
"""

import sys
import asyncio
import os
from pathlib import Path
from typing import Optional

from loguru import logger

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded environment from {env_path}")
except ImportError:
    pass  # python-dotenv not installed

# Configure logger for CLI
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <level>{message}</level>",
    level=log_level,
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

        print("LLM Configuration (from environment):")
        print(f"  Provider: {os.getenv('DEFAULT_LLM_PROVIDER', 'ollama')}")
        print(f"  Model: {os.getenv('DEFAULT_LLM_MODEL', 'llama3.2')}")
        print(f"  Temperature: {os.getenv('DEFAULT_LLM_TEMPERATURE', '0.7')}")
        print(f"  Max Tokens: {os.getenv('DEFAULT_LLM_MAX_TOKENS', '2000')}")
        print(f"  Streaming: {os.getenv('DEFAULT_LLM_STREAMING', 'true')}")
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

        # LLM configuration from environment
        print("LLM Configuration (from environment):")
        print(f"  Provider: {os.getenv('DEFAULT_LLM_PROVIDER', 'ollama')}")
        print(f"  Model: {os.getenv('DEFAULT_LLM_MODEL', 'llama3.2')}")
        print(f"  Temperature: {os.getenv('DEFAULT_LLM_TEMPERATURE', '0.7')}")
        print()

        logger.success("✅ Test setup complete!")
        logger.info(
            "This is a mock test showing configuration. "
            "Use 'run' command to invoke actual LLM."
        )

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)


async def run_agent(agent_id: str, message: str, model_override: str = None, provider_override: str = None, with_suggestions: bool = False, memory_type: str = "memory"):
    """Run sub-agent with actual LLM invocation

    Args:
        agent_id: Sub-agent ID to run
        message: User message
        model_override: Optional LLM model override (e.g., "gpt-4o", "llama3.2")
        provider_override: Optional LLM provider override (e.g., "openai", "ollama")
        with_suggestions: Whether to generate suggestions (default: False for CLI)
        memory_type: Checkpointer type: "memory" (default) or "redis"
    """
    from luka_agent import get_unified_agent_graph, create_initial_state
    from langchain_core.messages import AIMessage, ToolMessage

    try:
        logger.info(f"Running sub-agent: {agent_id}")

        if model_override:
            logger.info(f"🔧 Model override: {model_override}")
        if provider_override:
            logger.info(f"🔧 Provider override: {provider_override}")

        # Get CLI-enabled tools from environment
        cli_enabled_tools_str = os.getenv("CLI_ENABLED_TOOLS", "")
        if cli_enabled_tools_str:
            cli_enabled_tools = [tool.strip() for tool in cli_enabled_tools_str.split(",")]
        else:
            # Default: no tools enabled in CLI mode (will error if sub-agent needs any)
            cli_enabled_tools = []

        # Create initial state
        state = create_initial_state(
            user_message=message,
            user_id=12345,  # CLI test user
            thread_id="cli_thread",
            platform="worker",  # CLI runs as worker (non-interactive)
            language="en",
            sub_agent_id=agent_id,
            enabled_tools=cli_enabled_tools if cli_enabled_tools else None,  # Use sub-agent default if not specified
            generate_suggestions=with_suggestions,  # Optional suggestions for CLI (default: False)
        )

        # Validate that all sub-agent tools are enabled in CLI
        if cli_enabled_tools:
            sub_agent_tools = set(state["enabled_tools"])
            cli_tools = set(cli_enabled_tools)
            missing_tools = sub_agent_tools - cli_tools

            if missing_tools:
                logger.error(
                    f"Sub-agent '{agent_id}' requires tools that are not enabled in CLI_ENABLED_TOOLS: {missing_tools}"
                )
                logger.error(f"Sub-agent needs: {sub_agent_tools}")
                logger.error(f"CLI allows: {cli_tools}")
                logger.error(f"Please add {missing_tools} to CLI_ENABLED_TOOLS in .env or disable them in the sub-agent config")
                sys.exit(1)

        # Apply model/provider from environment defaults (if set) or CLI overrides
        # Priority: CLI override > ENV default > sub-agent default

        if model_override:
            # CLI override has highest priority
            state["llm_model"] = model_override
        else:
            # Use env default if provided, otherwise keep sub-agent default
            env_model = os.getenv("DEFAULT_LLM_MODEL")
            if env_model:
                state["llm_model"] = env_model

        if provider_override:
            # CLI override has highest priority
            state["llm_provider"] = provider_override
        else:
            # Use env default if provided, otherwise keep sub-agent default
            env_provider = os.getenv("DEFAULT_LLM_PROVIDER")
            if env_provider:
                state["llm_provider"] = env_provider

        logger.info(f"Invoking {agent_id} with message: \"{message}\"")
        logger.info(f"Using LLM: {state['llm_provider']}/{state['llm_model']}")
        logger.info(f"Using checkpointer: {memory_type}")
        print()
        print("=" * 70)
        print(f"🤖 {state['sub_agent_metadata']['name']} {state['sub_agent_metadata']['icon']}")
        print("=" * 70)
        print()
        print(f"👤 User: {message}")
        print(f"🧠 LLM: {state['llm_provider']}/{state['llm_model']}")
        print(f"💾 Memory: {memory_type}")
        print()

        # Get graph and invoke (use_memory=True for "memory", False for "redis")
        use_memory = memory_type.lower() == "memory"
        graph = await get_unified_agent_graph(use_memory=use_memory)
        config = {"configurable": {"thread_id": "cli_thread"}}

        # Stream events from graph
        print(f"🤖 {state['sub_agent_metadata']['name']}: ", end="", flush=True)

        final_state = None
        async for event in graph.astream(state, config, stream_mode="updates"):
            # Extract messages from updates
            for node_name, node_output in event.items():
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.content:
                                # Print AI response content
                                print(msg.content, end="", flush=True)
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                # Show tool calls
                                print()
                                print()
                                for tool_call in msg.tool_calls:
                                    print(f"  🔧 Calling tool: {tool_call['name']}")
                        elif isinstance(msg, ToolMessage):
                            # Show tool results
                            print(f"     ✓ Result: {msg.content[:100]}...")

            # Store final state
            final_state = node_output

        print()
        print()

        # Show suggestions if available
        if final_state and "conversation_suggestions" in final_state:
            suggestions = final_state["conversation_suggestions"]
            if suggestions:
                print("💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")
                print()

        print("=" * 70)
        logger.success("✅ Response complete!")

    except Exception as e:
        logger.error(f"❌ Run failed: {e}")
        import traceback
        traceback.print_exc()
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

    elif command == "run":
        if len(sys.argv) < 4:
            logger.error('Usage: python -m luka_agent.cli run <agent_id> "message" [--model MODEL] [--provider PROVIDER] [--with-suggestions] [--memory TYPE]')
            sys.exit(1)

        agent_id = sys.argv[2]
        message = sys.argv[3]

        # Parse optional model/provider overrides and flags
        model_override = None
        provider_override = None
        with_suggestions = False
        memory_type = "memory"  # Default to in-memory checkpointer

        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--model" and i + 1 < len(sys.argv):
                model_override = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--provider" and i + 1 < len(sys.argv):
                provider_override = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--memory" and i + 1 < len(sys.argv):
                memory_type = sys.argv[i + 1]
                if memory_type.lower() not in ["memory", "redis"]:
                    logger.error(f"Invalid memory type: {memory_type}. Must be 'memory' or 'redis'")
                    sys.exit(1)
                i += 2
            elif sys.argv[i] == "--with-suggestions":
                with_suggestions = True
                i += 1
            else:
                logger.warning(f"Unknown argument: {sys.argv[i]}")
                i += 1

        asyncio.run(run_agent(agent_id, message, model_override, provider_override, with_suggestions, memory_type))

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
