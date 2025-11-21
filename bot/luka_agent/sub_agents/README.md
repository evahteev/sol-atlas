# Sub-Agents - Specialized AI Personalities

**YAML-based, BMAD-compatible AI personalities that run on both Telegram and Web platforms.**

---

## What Are Sub-Agents?

Sub-agents are specialized AI personalities with unique expertise, tools, and communication styles. Instead of one general-purpose bot, sub-agents let you create domain experts that users can switch between.

### Think of it like this:

- **general_luka** 🤖 - Your friendly general assistant (knows a bit about everything)
- **crypto_analyst** 📈 - Crypto market expert (deep crypto knowledge, specialized tools)
- **your_agent** 🎯 - Your domain specialist (your expertise, your tools)

### Key Features

```
✅ Specialized Expertise    - Each agent has unique knowledge domain
✅ Custom Tool Access        - Different agents use different tools
✅ Unique Personalities      - Role-specific communication styles
✅ Platform-Agnostic         - Works on Telegram & Web
✅ BMAD-Compatible           - Standard agent definition format
✅ Auto-Switching            - Can switch agents based on keywords
```

### Architecture

```
my_agent/
├── config.yaml           # Agent definition (who, what, how)
├── system_prompt.md      # LLM instructions
├── prompts/              # Optional language variants (en.md, ru.md)
└── README.md             # Optional developer docs
```

---

## Quick Start

### List Available Agents

```bash
python -m luka_agent.cli list

# Output:
# 🤖 general_luka - General AI Assistant
# 📈 crypto_analyst - Crypto Market Expert
```

### Create a New Agent

```bash
# 1. Copy template
cp -r TEMPLATE my_agent

# 2. Edit config
cd my_agent
# - Edit config.yaml (identity, tools, KB)
# - Edit system_prompt.md (instructions)

# 3. Validate
python -m luka_agent.cli validate my_agent

# 4. Deploy
python -m luka_bot  # Restart to load new agent
```

### Test an Agent

```bash
# Validate configuration
python -m luka_agent.cli validate crypto_analyst

# Show details
python -m luka_agent.cli info crypto_analyst

# Test config (does NOT invoke LLM)
python -m luka_agent.cli test crypto_analyst "Hello"
```

---

## Documentation

### 📘 Want to Create a Sub-Agent?

**→ [SUB_AGENT_DEV_GUIDE.md](./SUB_AGENT_DEV_GUIDE.md)** - Complete development guide

**What's inside:**
- Step-by-step agent creation
- Configuration reference (all YAML fields)
- System prompt writing guide
- Template variables
- Testing and validation
- Troubleshooting

**Start here if:** You want to build a new specialized agent.

---

### 🏗️ Want to Understand the Architecture?

**→ [FINAL_ARCHITECTURE.md](./FINAL_ARCHITECTURE.md)** - Architecture overview

**What's inside:**
- File structure and purposes
- BMAD compatibility details
- Design decisions (why YAML-only, why separate files)
- Comparison with BMAD Method
- Migration guide

**Start here if:** You want to understand how it works internally.

---

### 📝 Want a Template to Copy?

**→ [TEMPLATE/](./TEMPLATE/)** - Starter template

**What's inside:**
- config.yaml with inline comments
- system_prompt.md with examples
- README.md template

**Start here if:** You want to copy-paste and customize.

---

### 🎯 Want to See Real Examples?

**→ [general_luka/](./general_luka/)** - General Assistant Pattern

- Broad tool access (KB, YouTube, Support, Sub-agent)
- Multiple use cases
- Default fallback agent
- Local LLM (Ollama)
- Lower temperature (0.7, balanced)

**→ [crypto_analyst/](./crypto_analyst/)** - Domain Specialist Pattern

- Specialized tools (token_info, swap_executor)
- Domain KBs (crypto-tweets, defi-protocols)
- Advanced LLM (GPT-4o)
- Lower temperature (0.4, factual)
- Intent triggers (auto-switch on "crypto", "token", "price")

**Start here if:** You want to see real working examples.

---

## How It Works

### 1. Define Your Agent (config.yaml)

```yaml
agent:
  metadata:
    id: "crypto_analyst"
    name: "Crypto Analyst"
    icon: "📈"

  persona:
    role: "Crypto Market Expert"
    identity: "You are a crypto analyst..."
    communication_style: "Data-driven, analytical"
    principles:
      - "ALWAYS cite data sources"
      - "NEVER give financial advice"

luka_extensions:
  enabled_tools:
    - "knowledge_base"
    - "token_info"

  knowledge_bases:
    - "user-kb-{user_id}"
    - "crypto-tweets"

  llm_config:
    provider: "openai"
    model: "gpt-4o"
    temperature: 0.4
```

### 2. Write Instructions (system_prompt.md)

```markdown
You are **{agent_name}** {metadata.icon}, {persona.role}.

## Your Identity
{persona.identity}

## Tools Available
### 📊 token_info
When user asks about prices, use this tool...

## Examples
**User:** "What's the price of SOL?"
**You:** [Example response]
```

### 3. Validate & Deploy

```bash
python -m luka_agent.cli validate crypto_analyst
python -m luka_bot  # Restart
```

### 4. Users Can Switch Agents

```
User: "Tell me about Solana price"
→ Auto-switches to crypto_analyst (intent trigger: "price")

User: "Help me plan a trip"
→ Suggests trip_planner agent

User: "General question"
→ Uses general_luka (default)
```

---

## Current Agents

| Agent | Icon | Purpose | Tools | LLM | KB |
|-------|------|---------|-------|-----|-----|
| **general_luka** | 🤖 | Default general assistant | KB, YouTube, Support, Sub-agent | Ollama llama3.2 | User KB |
| **crypto_analyst** | 📈 | Crypto market expert | KB, Token Info, Swap, YouTube | OpenAI GPT-4o | User KB + Crypto KBs |

---

## Key Concepts

### BMAD Core (Portable)

The `agent` section follows the BMAD Method format, making agents portable across BMAD-compatible systems:

```yaml
agent:
  metadata:     # Who is this agent?
  persona:      # How does it behave?
  menu:         # Quick actions
```

### Luka Extensions (Platform-Specific)

The `luka_extensions` section adds luka-specific features:

```yaml
luka_extensions:
  enabled_tools:     # Which tools can it use?
  knowledge_bases:   # Which KBs can it search?
  llm_config:        # Which LLM provider?
  capabilities:      # What are its boundaries?
```

### Template Variables

System prompts support dynamic content:

```markdown
You are **{agent_name}** ({metadata.icon})
User: {user_name}
Platform: {platform}
Language: {language}
```

### Language Variants (i18n)

Support multiple languages:

```yaml
system_prompt:
  base: "system_prompt.md"
  language_variants:
    en: "prompts/en.md"
    ru: "prompts/ru.md"
```

### Auto-Switching

Agents can be activated by keywords:

```yaml
intent_triggers:
  - "crypto"
  - "token"
  - "price"
```

When user mentions these words → auto-switch to this agent.

---

## Use Cases

### Pattern 1: General Assistant

**When:** Default conversational agent

**Config:**
- Ollama (local, free)
- Temperature: 0.7 (balanced)
- Tools: General (KB, YouTube, Support)
- KB: User-only

**Example:** general_luka

---

### Pattern 2: Domain Specialist

**When:** Expert in specific field

**Config:**
- OpenAI GPT-4o (advanced reasoning)
- Temperature: 0.4 (factual, deterministic)
- Tools: Domain-specific + general
- KB: User + domain KBs
- Intent triggers: Auto-switch keywords

**Example:** crypto_analyst

---

## Development Workflow

```bash
# 1. Create from template
cp -r TEMPLATE finance_advisor

# 2. Define identity (who is this agent?)
cd finance_advisor
# Edit config.yaml:
#  - metadata (id, name, icon)
#  - persona (role, style, principles)
#  - tools (which ones?)
#  - KBs (which indices?)

# 3. Write instructions (how should it behave?)
# Edit system_prompt.md:
#  - Identity with template variables
#  - Tool usage examples
#  - Example interactions
#  - Edge cases

# 4. Validate
python -m luka_agent.cli validate finance_advisor

# 5. Test configuration
python -m luka_agent.cli test finance_advisor "Hello"

# 6. Deploy and test
python -m luka_bot
# Test via Telegram or Web interface

# 7. Iterate
# - Monitor behavior
# - Update system_prompt.md
# - Validate and redeploy
```

---

## Best Practices

### ✅ DO

- Start with TEMPLATE
- Write specific personas (not "helpful assistant")
- Provide 3-5 example interactions in system_prompt.md
- Use ALWAYS/NEVER for critical rules
- Test on both Telegram and Web
- Enable only relevant tools
- Set appropriate temperature:
  - 0.3-0.5 for factual agents (data analysis)
  - 0.7-0.9 for creative agents (brainstorming)
- Use template variables for dynamic content
- Version your agents (1.0.0 → 1.1.0 → 2.0.0)

### ❌ DON'T

- Enable all tools (be selective)
- Use generic personas
- Skip system prompt examples
- Write overly long prompts (>2500 words)
- Reference platform-specific features
- Skip validation before deploying
- Forget to document in README.md

---

## CLI Reference

```bash
# List all agents
python -m luka_agent.cli list

# Validate agent configuration
python -m luka_agent.cli validate <agent_id>

# Show agent details
python -m luka_agent.cli info <agent_id>

# Test configuration (config validation only)
python -m luka_agent.cli test <agent_id> "test message"
```

**Note:** The `test` command validates configuration only. For real testing, deploy to luka_bot/ag_ui_gateway and test via Telegram/Web.

---

## File Structure

```
luka_agent/sub_agents/
├── README.md                    # ← You are here
├── SUB_AGENT_DEV_GUIDE.md       # Complete development guide
├── FINAL_ARCHITECTURE.md        # Architecture documentation
├── loader.py                    # SubAgentLoader implementation
│
├── TEMPLATE/                    # Template for new agents
│   ├── config.yaml
│   ├── system_prompt.md
│   └── README.md
│
├── general_luka/                # Example: General assistant
│   ├── config.yaml
│   ├── system_prompt.md
│   ├── prompts/
│   │   ├── en.md
│   │   └── ru.md
│   └── README.md
│
└── crypto_analyst/              # Example: Domain specialist
    ├── config.yaml
    ├── system_prompt.md
    └── README.md
```

---

## Integration

Sub-agents work with:

- **luka_bot** - Telegram bot runtime
- **ag_ui_gateway** - Web chat runtime
- **luka_agent tools** - Shared tool layer
- **Elasticsearch** - Knowledge base search
- **Ollama / OpenAI** - LLM providers

---

## Next Steps

### New to Sub-Agents?

1. Read [SUB_AGENT_DEV_GUIDE.md](./SUB_AGENT_DEV_GUIDE.md) (comprehensive guide)
2. Look at [general_luka/](./general_luka/) (simple example)
3. Look at [crypto_analyst/](./crypto_analyst/) (specialist example)
4. Copy [TEMPLATE/](./TEMPLATE/) and customize
5. Validate with CLI
6. Deploy and test

### Want to Understand the Design?

1. Read [FINAL_ARCHITECTURE.md](./FINAL_ARCHITECTURE.md)
2. Understand BMAD compatibility
3. Learn about file purposes
4. Review design decisions

### Want to See the Code?

- **Loader**: `loader.py` - Loads and validates agents
- **CLI**: `../../cli.py` - Testing commands
- **Tools**: `../../tools/` - Tool layer
- **Tests**: `../../tests/test_sub_agent_tools.py`

---

## Support

**Documentation:**
- [SUB_AGENT_DEV_GUIDE.md](./SUB_AGENT_DEV_GUIDE.md) - Complete guide
- [FINAL_ARCHITECTURE.md](./FINAL_ARCHITECTURE.md) - Architecture details
- [CLAUDE.md](../../CLAUDE.md) - Project overview

**Examples:**
- [general_luka/](./general_luka/) - General assistant
- [crypto_analyst/](./crypto_analyst/) - Domain specialist
- [TEMPLATE/](./TEMPLATE/) - Starter template

**Tools:**
- `python -m luka_agent.cli --help`

---

**Ready to create specialized AI personalities?**

**→ Start with [SUB_AGENT_DEV_GUIDE.md](./SUB_AGENT_DEV_GUIDE.md) 🚀**
