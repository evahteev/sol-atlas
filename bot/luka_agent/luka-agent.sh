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
  list                                 List all available sub-agents
  validate <agent_id>                  Validate sub-agent configuration
  test <agent_id> <msg>                Test sub-agent with a message (mock, no LLM)
  run <agent_id> <msg> [--model M]     Run sub-agent with actual LLM invocation
                       [--provider P]
  info <agent_id>                      Show detailed sub-agent information
  help                                 Show this help message

Run Options:
  --model <model>       Override LLM model (e.g., gpt-4o, llama3.2)
  --provider <provider> Override LLM provider (ollama, openai, anthropic)

Examples:
  ./luka-agent.sh list
  ./luka-agent.sh validate general_luka
  ./luka-agent.sh test general_luka "Hello, who are you?"
  ./luka-agent.sh run general_luka "What can you help me with?"
  ./luka-agent.sh run general_luka "Hello" --model gpt-4o --provider openai
  ./luka-agent.sh info general_luka

Environment Variables (optional):
  OLLAMA_URL               Ollama API URL (default: http://localhost:11434)

Requirements:
  - Python 3.10+ with packages: langgraph, langchain, loguru, pydantic, yaml
  - Or: Run from the bot's main conda/venv environment

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
