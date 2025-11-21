#!/usr/bin/env bash
# =============================================================================
# Luka Agent CLI Wrapper
# =============================================================================
# This script runs the luka_agent CLI with proper environment setup
#
# Usage:
#   ./luka-agent.sh list
#   ./luka-agent.sh validate general_luka
#   ./luka-agent.sh test general_luka "Hello, who are you?"
#   ./luka-agent.sh info crypto_analyst
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║             Luka Agent CLI - Standalone Mode               ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

print_usage() {
    cat << EOF
Usage: ./luka-agent.sh <command> [args...]

Commands:
  list                    List all available sub-agents
  validate <agent_id>     Validate sub-agent configuration
  test <agent_id> <msg>   Test sub-agent with a message (mock, no LLM)
  run <agent_id> <msg>    Run sub-agent with actual LLM invocation
      [OPTIONS]
  info <agent_id>         Show detailed sub-agent information
  help, --help, -h        Show this help message

Run Command Options:
  --model <model>         Override LLM model
                          Examples: gpt-4o, llama3.2, claude-sonnet-4
                          Default: From .env (DEFAULT_LLM_MODEL) or llama3.2

  --provider <provider>   Override LLM provider
                          Options: ollama, openai, anthropic
                          Default: From .env (DEFAULT_LLM_PROVIDER) or ollama

  --memory <type>         Checkpointer type for state persistence
                          Options: memory (in-memory), redis (persistent)
                          Default: memory (no Redis required)

  --with-suggestions      Enable suggestions generation
                          (Disabled by default in CLI mode)

Examples:
  # List and validate
  ./luka-agent.sh list
  ./luka-agent.sh validate general_luka
  ./luka-agent.sh info general_luka

  # Test without LLM
  ./luka-agent.sh test general_luka "Hello, who are you?"

  # Run with defaults (in-memory, env settings)
  ./luka-agent.sh run general_luka "What can you help me with?"

  # Override model and provider
  ./luka-agent.sh run general_luka "Hello" --model gpt-4o --provider openai

  # Use Redis for state persistence
  ./luka-agent.sh run general_luka "Hello" --memory redis

  # Enable suggestions
  ./luka-agent.sh run general_luka "Hello" --with-suggestions

  # Combine multiple options
  ./luka-agent.sh run general_luka "Hello" \\
    --model claude-sonnet-4 \\
    --provider anthropic \\
    --memory redis \\
    --with-suggestions

Environment Configuration:
  Create a .env file in the luka_agent directory with:

  # LLM Settings
  OLLAMA_URL=http://localhost:11434/v1
  DEFAULT_LLM_PROVIDER=ollama
  DEFAULT_LLM_MODEL=llama3.2
  DEFAULT_LLM_TEMPERATURE=0.7

  # Memory/Checkpointer
  LUKA_USE_MEMORY_CHECKPOINTER=true  # true = in-memory, false = Redis

  # Redis (only if using Redis checkpointer)
  REDIS_HOST=localhost
  REDIS_PORT=6379

  # Tools
  CLI_ENABLED_TOOLS=knowledge_base,sub_agent,youtube,image_description,support

  See .env.example for complete configuration options.

Requirements:
  - Python 3.10+ installed
  - Required packages: langgraph, langchain-core, langchain-openai, etc.
  - Run: pip install -r requirements.txt

For more information:
  - See CLI_USAGE.md for detailed documentation
  - See README.md for architecture and development guide

EOF
}

check_python() {
    log_info "Checking Python..."

    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Prefer python3, fall back to python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_success "Found Python $PYTHON_VERSION"
}

check_dependencies() {
    log_info "Checking dependencies..."

    # Check for all required luka_agent packages
    if $PYTHON_CMD -c "import langgraph, langchain_core, langchain_ollama, loguru, yaml, redis, elasticsearch" 2>/dev/null; then
        log_success "All required packages are installed"
        return 0
    else
        log_warning "Some required packages are missing"
        echo ""
        echo "Would you like to install them now? (y/n)"
        read -r response

        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            log_info "Installing dependencies from $SCRIPT_DIR/requirements.txt..."
            $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt"

            if [ $? -eq 0 ]; then
                log_success "Dependencies installed successfully!"
                return 0
            else
                log_error "Failed to install dependencies"
                exit 1
            fi
        else
            log_error "Cannot proceed without dependencies"
            echo ""
            echo "To install manually:"
            echo "  cd $SCRIPT_DIR"
            echo "  pip install -r requirements.txt"
            echo ""
            exit 1
        fi
    fi
}

run_cli() {
    log_info "Running luka_agent CLI..."
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Set PYTHONPATH to include project root
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # Run the CLI with passed arguments
    $PYTHON_CMD -m luka_agent.cli "$@"

    local exit_code=$?

    echo ""
    echo "═══════════════════════════════════════════════════════════════"

    return $exit_code
}

# =============================================================================
# Main Script
# =============================================================================

# Print header
print_header

# Check if help requested or no args
if [ $# -eq 0 ] || [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    print_usage
    exit 0
fi

# Step 1: Check Python
check_python

# Step 2: Check dependencies
check_dependencies

# Step 3: Run the CLI with all passed arguments
echo ""
if run_cli "$@"; then
    echo ""
    log_success "Completed successfully!"
    echo ""
    exit 0
else
    echo ""
    log_error "Command failed"
    echo ""
    exit 1
fi
