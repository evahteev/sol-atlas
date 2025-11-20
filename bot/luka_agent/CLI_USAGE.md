# Luka Agent CLI - Quick Start Guide

## Easy Setup & Usage

### Option 1: Using the Wrapper Script (Recommended)

The `luka-agent.sh` wrapper handles everything automatically:

```bash
# Make it executable (first time only)
chmod +x luka-agent.sh

# List all available sub-agents
./luka-agent.sh list

# Validate a sub-agent configuration
./luka-agent.sh validate general_luka

# Test a sub-agent with a message (mock, no LLM)
./luka-agent.sh test general_luka "Hello, who are you?"

# Run a sub-agent with actual LLM invocation
./luka-agent.sh run general_luka "What can you help me with?"

# Show detailed info about a sub-agent
./luka-agent.sh info general_luka
```

### Option 2: Direct Python (If in correct environment)

```bash
# Make sure you're in the conda/venv with dependencies installed
python -m luka_agent.cli list
python -m luka_agent.cli validate general_luka
python -m luka_agent.cli test general_luka "Hello"
python -m luka_agent.cli info general_luka
```

## Commands

### `list` - List Available Sub-Agents

Shows all sub-agents with their names, IDs, and descriptions.

```bash
./luka-agent.sh list
```

**Output:**
```
🤖  Luka (general_luka)
   General-purpose AI assistant for conversation, knowledge search...

📈  Crypto Analyst (crypto_analyst)
   Specialized agent for cryptocurrency market analysis...
```

### `validate <agent_id>` - Validate Configuration

Checks if a sub-agent's configuration is valid (YAML structure, system prompt, etc.).

```bash
./luka-agent.sh validate general_luka
```

**Output:**
```
Agent: Luka 🤖
ID: general_luka
Version: 1.0.0
Description: General-purpose AI assistant...

Role: Helpful AI Assistant + Knowledge Manager
Enabled Tools: knowledge_base, sub_agent, youtube, image_description, support
Knowledge Bases: user-kb-{user_id}

LLM Configuration (from environment):
  Provider: ollama
  Model: gpt-oss
  Temperature: 0.7
  Max Tokens: 2000
  Streaming: true

System Prompt: 14310 characters
Principles: 6

✓ Configuration valid for 'general_luka'
```

### `test <agent_id> <message>` - Test Sub-Agent (Mock)

Shows the configuration that would be used (doesn't invoke actual LLM).

```bash
./luka-agent.sh test general_luka "Hello, who are you?"
```

**Output:**
```
TESTING: Luka 🤖
User Message: Hello, who are you?

System Prompt (preview):
# System Prompt for Luka
You are **Luka**, Helpful AI Assistant + Knowledge Manager...

Available Tools: knowledge_base, sub_agent, youtube, image_description, support
LLM Configuration: ollama/gpt-oss (from environment)
```

### `run <agent_id> <message>` - Run Sub-Agent with LLM

Invokes the actual LLM and returns a real response.

```bash
./luka-agent.sh run general_luka "What can you help me with?"
```

**Output:**
```
🤖 Luka 🤖
═════════════════════════════════════════
👤 User: What can you help me with?

🤖 Luka: I'm Luka, your AI assistant! I can help you with...
[actual LLM response]

💡 Suggestions:
  • Tell me more
  • What else can you do?
  • Thanks!
```

#### Using Tools from CLI

The general_luka agent has access to several tools including image description:

**Image Description Example:**
```bash
./luka-agent.sh run general_luka "Please describe this image: https://picsum.photos/id/237/400/300"
```

**Output:**
```
🤖 Luka 🤖
═════════════════════════════════════════
👤 User: Please describe this image: https://picsum.photos/id/237/400/300

  🔧 Calling tool: describe_image
     ✓ Result: The image features a black Labrador puppy...

🤖 Luka: Let me describe the image for you.

- **Subject**: A black Labrador puppy with light brown eyes...
- **Pose**: Sitting on a wooden deck, looking directly at the camera...
- **Composition**: Puppy centered, drawing focus to its eyes...
- **Background**: Blurred, likely an overcast sky...
- **Mood/Style**: Realistic, candid photograph...

💡 Suggestions:
  • Could you describe the background?
  • What color is the puppy's collar?
  • Show me a different picture.
```

**Other Tool Examples:**
```bash
# Knowledge base search
./luka-agent.sh run general_luka "Search my knowledge base for notes about Python"

# YouTube transcript
./luka-agent.sh run general_luka "Get the transcript of this video: https://youtube.com/watch?v=..."

# Sub-agent execution
./luka-agent.sh run general_luka "Help me with DeFi onboarding"
```

### `info <agent_id>` - Detailed Information

Shows comprehensive information about a sub-agent.

```bash
./luka-agent.sh info general_luka
```

**Output:**
```
═══════════════════════════════════════════
🤖  Luka - General AI Assistant
═══════════════════════════════════════════

ID: general_luka
Version: 1.0.0
...
```

## Requirements

### System Requirements
- Python 3.10+ (3.11 recommended)
- Docker & Docker Compose (for development with Elasticsearch & Redis)
- Ollama (for local LLM and vision models) OR OpenAI/Anthropic API keys

### Python Packages
All required packages are listed in `requirements.txt`:
- `langgraph` - Graph execution engine
- `langchain-core` - LangChain core
- `langchain-ollama` - Ollama integration (LLM + vision)
- `langchain-openai` - OpenAI integration (optional)
- `langchain-anthropic` - Anthropic integration (optional)
- `elasticsearch` - Elasticsearch client (for knowledge_base tool)
- `redis` - Redis client (for state persistence)
- `httpx` - HTTP client (for image downloading)
- `loguru` - Logging
- `pydantic` - Data validation
- `pyyaml` - YAML parsing
- `python-dotenv` - Environment configuration

### Installation

**Option 1: Install from luka_agent directory (recommended for development)**
```bash
cd luka_agent
pip install -r requirements.txt
```

**Option 2: Install from bot directory (if using full bot setup)**
```bash
cd bot
pip install -r requirements.txt
```

**Option 3: Use virtual environment**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
cd luka_agent
pip install -r requirements.txt
```

### Development Infrastructure Setup

Start Elasticsearch and Redis for local development:

```bash
cd luka_agent

# Start services in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services provided:**
- **Elasticsearch**: `http://localhost:9200` (for knowledge_base tool)
- **Redis**: `localhost:6379` (for state checkpointing)

**Health check:**
```bash
# Test Elasticsearch
curl http://localhost:9200

# Test Redis
redis-cli ping
```

## Environment Configuration

### Using .env File (Recommended)

Create a `.env` file in the `luka_agent` directory:

```bash
# Copy the example file
cp .env.example .env

# Edit with your settings
nano .env
```

**Example .env:**
```bash
# ============================================================================
# LLM Provider Settings
# ============================================================================
# Ollama Configuration
OLLAMA_URL=http://localhost:11434

# Default LLM Configuration (used by all sub-agents)
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.2
DEFAULT_LLM_TEMPERATURE=0.7
DEFAULT_LLM_MAX_TOKENS=2000
DEFAULT_LLM_STREAMING=true

# OpenAI Configuration (optional)
# OPENAI_API_KEY=sk-...
# DEFAULT_LLM_PROVIDER=openai
# DEFAULT_LLM_MODEL=gpt-4o-mini

# Anthropic Configuration (optional)
# ANTHROPIC_API_KEY=sk-ant-...

# ============================================================================
# Vision Model Settings (for image_description tool)
# ============================================================================
DEFAULT_VISION_MODEL=llava
VISION_ENABLED=true

# ============================================================================
# Tool Configuration
# ============================================================================
# Comma-separated list of enabled tools for CLI runs
CLI_ENABLED_TOOLS=knowledge_base,sub_agent,youtube,image_description,support

# ============================================================================
# Other Settings
# ============================================================================
# Elasticsearch (for knowledge_base tool)
ELASTICSEARCH_URL=http://localhost:9200

# Log level
LOG_LEVEL=INFO
```

The CLI automatically loads `.env` if it exists.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| **LLM Configuration** | | |
| `DEFAULT_LLM_PROVIDER` | LLM provider (ollama, openai, anthropic) | `ollama` |
| `DEFAULT_LLM_MODEL` | Model name | `llama3.2` |
| `DEFAULT_LLM_TEMPERATURE` | Temperature (0.0-2.0) | `0.7` |
| `DEFAULT_LLM_MAX_TOKENS` | Max output tokens | `2000` |
| `DEFAULT_LLM_STREAMING` | Enable streaming | `true` |
| `OLLAMA_URL` | Ollama API URL | `http://localhost:11434` |
| `OPENAI_API_KEY` | OpenAI API key | (optional) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (optional) |
| **Vision Configuration** | | |
| `DEFAULT_VISION_MODEL` | Vision model for image description | `llama` |
| `VISION_ENABLED` | Enable image description tool | `true` |
| **Tools** | | |
| `CLI_ENABLED_TOOLS` | Comma-separated list of enabled tools | See .env.example |
| **Other** | | |
| `ELASTICSEARCH_URL` | Elasticsearch URL (knowledge_base tool) | `http://localhost:9200` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |

**Manual export (without .env):**
```bash
export OLLAMA_URL=http://localhost:11434
./luka-agent.sh run general_luka "Hello"
```

## Troubleshooting

### Error: "Required packages are missing"

**Solution:** Install dependencies
```bash
cd /path/to/bot
pip install -r requirements.txt
```

### Error: "Python 3 is not installed"

**Solution:** Install Python 3.10+
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11

# Or download from https://www.python.org/
```

### Warning: "luka_bot settings not available"

**This is normal** when running in standalone mode. The CLI works without luka_bot configuration by using fallback settings (MemorySaver, environment variables).

### Error: "Sub-agent config not found"

**Solution:** Check sub-agent exists
```bash
ls -la sub_agents/
# Should see directories like: general_luka/, crypto_analyst/, etc.
```

## Examples

### Quick Validation Workflow

```bash
# 1. List all sub-agents
./luka-agent.sh list

# 2. Validate one
./luka-agent.sh validate general_luka

# 3. Test it
./luka-agent.sh test general_luka "What can you help me with?"

# 4. Get detailed info
./luka-agent.sh info general_luka
```

### Creating a New Sub-Agent

```bash
# 1. Copy template
cp -r sub_agents/TEMPLATE sub_agents/my_agent

# 2. Edit config.yaml
nano sub_agents/my_agent/config.yaml
# Update: id, name, description, tools, etc.

# 3. Create system prompt
nano sub_agents/my_agent/system_prompt.md

# 4. Validate
./luka-agent.sh validate my_agent

# 5. Test
./luka-agent.sh test my_agent "Hello"
```

## Integration Usage

### Import as Package

```python
from luka_agent import (
    get_unified_agent_graph,
    create_initial_state,
    hydrate_state_with_sub_agent,
)

# Use in your application
graph = await get_unified_agent_graph()
state = create_initial_state(
    user_message="Hello",
    user_id=123,
    thread_id="thread_123",
    platform="telegram",
    language="en",
)

result = await graph.ainvoke(
    state,
    config={"configurable": {"thread_id": "thread_123"}}
)
```

## Support

For issues or questions:
1. Check [README.md](./README.md) - Architecture and implementation details
2. Check [LUKA_AGENT_PIVOT_ARCHITECTURE.md](./LUKA_AGENT_PIVOT_ARCHITECTURE.md) - BMAD-compatible design
3. Check [sub_agents/README.md](./sub_agents/README.md) - Sub-agent development guide
4. Check [tools/README.md](./tools/README.md) - Tool development guide

## Quick Reference

| Command | Description |
|---------|-------------|
| `./luka-agent.sh list` | List all sub-agents |
| `./luka-agent.sh validate <id>` | Validate configuration |
| `./luka-agent.sh test <id> "<msg>"` | Test with message (mock, no LLM) |
| `./luka-agent.sh run <id> "<msg>"` | Run with actual LLM invocation |
| `./luka-agent.sh info <id>` | Detailed information |
| `./luka-agent.sh help` | Show help |

**Tip:** The wrapper automatically detects your Python environment and runs the CLI with proper PYTHONPATH settings. Just make sure dependencies are installed!
