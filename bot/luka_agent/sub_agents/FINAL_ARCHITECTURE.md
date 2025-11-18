# Sub-Agent Architecture - Final Structure ✅

**Date:** 2025-11-18
**Status:** Simplified YAML-only architecture aligned with BMAD

---

## Architecture Overview

### File Structure (BMAD-Aligned)

```
luka_agent/sub_agents/
├── TEMPLATE/                    # Template for new agents
│   ├── config.yaml             # BMAD agent definition + luka extensions
│   ├── system_prompt.md        # Agent system prompt template
│   └── README.md               # Developer instructions
│
├── general_luka/               # Example: General assistant
│   ├── config.yaml
│   ├── system_prompt.md
│   ├── prompts/                # Optional: Language variants
│   │   ├── en.md
│   │   └── ru.md
│   └── README.md
│
└── crypto_analyst/             # Example: Specialist agent
    ├── config.yaml
    ├── system_prompt.md
    └── README.md
```

---

## File Purposes

### 1. config.yaml (REQUIRED)

**Purpose:** Agent definition and configuration

**Contents:**
- **BMAD Core Section** (compatible with BMAD Method):
  - `agent.metadata` - id, name, title, icon, version, description
  - `agent.persona` - role, identity, communication_style, principles
  - `agent.menu` - Quick action buttons (tool, command, agent, workflow)

- **Luka Extensions** (luka-specific integration):
  - `luka_extensions.system_prompt` - Path to system_prompt.md with language variants
  - `luka_extensions.enabled_tools` - List of available tools
  - `luka_extensions.knowledge_bases` - KB indices to search
  - `luka_extensions.llm_config` - LLM provider, model, temperature
  - `luka_extensions.capabilities` - Data access boundaries and features
  - `luka_extensions.dependencies` - Optional: agents for delegation
  - `luka_extensions.intent_triggers` - Optional: keywords for auto-switching

**Format:** Pure YAML (BMAD-compatible)

**Example:**
```yaml
# BMAD Core
agent:
  metadata:
    id: "my_agent"
    name: "My Agent"
    title: "My Specialized Agent"
    icon: "🤖"
    version: "1.0.0"
    description: "Brief description"

  persona:
    role: "Specific Role + Expertise"
    identity: |
      You are [Name], a [role].
      You help with [capabilities].
    communication_style: "Tone and style"
    principles:
      - "ALWAYS [action] because [reason]"
      - "NEVER [action] because [reason]"

  menu:
    - label: "🔍 Action Label"
      description: "What this does"
      action:
        type: "tool"
        tool: "tool_name"

# Luka Extensions
luka_extensions:
  system_prompt:
    base: "sub_agents/my_agent/system_prompt.md"
    language_variants:
      en: "sub_agents/my_agent/prompts/en.md"
      ru: "sub_agents/my_agent/prompts/ru.md"
    template_vars:
      agent_name: "{metadata.name}"
      user_name: "{user.name}"
      platform: "{state.platform}"
      language: "{state.language}"

  enabled_tools:
    - "knowledge_base"
    - "sub_agent"
    - "youtube"
    - "support"

  knowledge_bases:
    - "user-kb-{user_id}"

  llm_config:
    provider: "ollama"
    model: "llama3.2"
    temperature: 0.7
    max_tokens: 2000
    streaming: true

  capabilities:
    data_access:
      allowed_kb_patterns: ["user-kb-*", "public-*"]
      forbidden_kb_patterns: ["admin-*"]
    features:
      can_create_threads: true
      can_execute_workflows: true
      can_search_external: false
      can_modify_user_data: false

  # Optional: For auto-switching
  intent_triggers:
    - "keyword1"
    - "keyword2"
```

---

### 2. system_prompt.md (REQUIRED)

**Purpose:** Agent's system prompt template

**Contents:**
- Identity (uses {persona.identity} from config)
- Communication style (uses {persona.communication_style})
- Core principles
- Available tools documentation
- Example interactions
- Edge case handling
- Platform-specific instructions

**Format:** Markdown with template variables

**Template Variables:**
- `{agent_name}` - From metadata.name
- `{persona.identity}` - From persona.identity
- `{persona.communication_style}` - From persona.communication_style
- `{user_name}` - Runtime: user's name
- `{platform}` - Runtime: "telegram" or "web"
- `{language}` - Runtime: user's language

**Loading Process:**
```python
# 1. Load config.yaml
config = yaml.load("config.yaml")

# 2. Load system prompt template
prompt_template = read("system_prompt.md")

# 3. Render with variables
prompt = prompt_template.format(
    agent_name=config["agent"]["metadata"]["name"],
    persona_identity=config["agent"]["persona"]["identity"],
    persona_communication_style=config["agent"]["persona"]["communication_style"],
    user_name=state["user_name"],
    platform=state["platform"],
    language=state["language"]
)
```

---

### 3. README.md (RECOMMENDED)

**Purpose:** Developer documentation for this specific agent

**Contents:**
- Agent overview and purpose
- Customization instructions
- Testing guidelines
- Deployment notes
- Domain-specific context
- Known issues and limitations

**Audience:** Developers maintaining this agent

**Example:**
```markdown
# Crypto Analyst Agent

Specialized agent for cryptocurrency market analysis.

## Overview
- Real-time token data via DexGuru API
- Market analysis from crypto knowledge bases
- DeFi protocol insights

## Customization
- Update token data sources in config.yaml
- Add new crypto KBs to knowledge_bases
- Customize analysis templates in templates/

## Testing
```bash
python -m luka_agent.cli test crypto_analyst "What's ETH price?"
```
```

---

## Comparison: BMAD vs Luka Agent

### BMAD Approach (Pure)

```yaml
# Single file: agent.yaml
agent:
  metadata:
    id: "agent-id"
    name: "Agent Name"
  persona:
    role: "Role"
    identity: "Description"
  menu:
    - trigger: "command"
      action: "action"
  prompts: []
```

**Characteristics:**
- ✅ Everything in one YAML file
- ✅ Simple and portable
- ❌ No system prompt separation
- ❌ No integration settings (tools, KBs, LLM)

---

### Luka Agent Approach (Enhanced)

```yaml
# config.yaml - BMAD core + luka extensions
agent:
  metadata: {...}    # BMAD compatible
  persona: {...}     # BMAD compatible
  menu: [...]        # BMAD compatible

luka_extensions:
  system_prompt:
    base: "system_prompt.md"      # Separate system prompt
    language_variants: {...}      # i18n support
    template_vars: {...}          # Dynamic rendering
  enabled_tools: [...]            # Luka-specific
  knowledge_bases: [...]          # Luka-specific
  llm_config: {...}               # Luka-specific
  capabilities: {...}             # Luka-specific
  dependencies:                   # Optional agent delegation
    agents: [...]
  intent_triggers: [...]          # Optional auto-switching
```

**Characteristics:**
- ✅ BMAD core compatible (agent section)
- ✅ Extended with luka-specific features
- ✅ Separate system prompt template with i18n
- ✅ Integration settings (tools, KBs, LLM)
- ✅ Dynamic prompt rendering with template variables
- ✅ Hybrid approach: compatible + enhanced

---

## Creating a New Sub-Agent

### Quick Start

```bash
# 1. Copy template
cp -r luka_agent/sub_agents/TEMPLATE luka_agent/sub_agents/my_agent

# 2. Edit config.yaml
cd luka_agent/sub_agents/my_agent
# Replace all [PLACEHOLDERS] with your values

# 3. Edit system_prompt.md
# Customize identity, tools, examples

# 4. Edit README.md (optional)
# Add agent-specific documentation

# 5. Validate
python -m luka_agent.cli validate my_agent

# 6. Test
python -m luka_agent.cli test my_agent "Hello"

# 7. Deploy
# Restart luka_bot or ag_ui_gateway
```

### Customization Checklist

**config.yaml:**
- [ ] agent.metadata - id, name, title, icon, description
- [ ] agent.persona - role, identity, communication_style, principles
- [ ] agent.menu - Quick action buttons (if needed)
- [ ] luka_extensions.enabled_tools - Select relevant tools
- [ ] luka_extensions.knowledge_bases - Configure KBs
- [ ] luka_extensions.llm_config - Choose LLM and settings
- [ ] luka_extensions.capabilities - Set data access boundaries

**system_prompt.md:**
- [ ] Identity section - Who the agent is
- [ ] Communication style - How it communicates
- [ ] Core principles - Guiding rules
- [ ] Tool documentation - Each enabled tool
- [ ] Example interactions - 3-5 scenarios
- [ ] Edge cases - How to handle special situations

**README.md:**
- [ ] Agent overview - Purpose and capabilities
- [ ] Customization guide - Domain-specific notes
- [ ] Testing examples - How to test this agent

---

## BMAD Compatibility Matrix

| Feature | BMAD Format | Luka Agent | Status |
|---------|-------------|------------|--------|
| **Core Structure** | | | |
| agent.metadata | ✅ YAML | ✅ YAML | ✅ Compatible |
| agent.persona | ✅ YAML | ✅ YAML | ✅ Compatible |
| agent.menu | ✅ YAML | ✅ YAML | ✅ Compatible |
| agent.prompts | ✅ YAML | ⚠️ Separate file | ⚠️ Enhanced |
| **Format** | | | |
| Single .yaml file | ✅ | ❌ | ⚠️ Split for clarity |
| Separate system prompt | ❌ | ✅ | ✅ Enhancement |
| Language variants | ❌ | ✅ | ✅ Enhancement |
| Template variables | ❌ | ✅ | ✅ Enhancement |
| **Extensions** | | | |
| enabled_tools | ❌ | ✅ | ✅ Luka-specific |
| knowledge_bases | ❌ | ✅ | ✅ Luka-specific |
| llm_config | ❌ | ✅ | ✅ Luka-specific |
| capabilities | ❌ | ✅ | ✅ Luka-specific |
| dependencies.agents | ✅ | ✅ | ✅ Compatible |
| intent_triggers | ❌ | ✅ | ✅ Luka-specific |

**Summary:**
- ✅ **100% BMAD Core Compatible** - agent section follows BMAD exactly
- ✅ **Enhanced with luka_extensions** - Additional features for integration
- ✅ **Separate system prompt with i18n** - Better organization and maintainability
- ✅ **Template variables** - Dynamic prompt rendering
- ✅ **Intent triggers** - Auto-switching between agents
- ⚠️ **Split files vs single file** - Tradeoff for clarity and modularity

---

## Design Decisions

### Why Separate Files?

**config.yaml + system_prompt.md instead of single file:**

**Pros:**
- ✅ Clear separation of concerns (config vs prompt)
- ✅ Easier to maintain system prompts (markdown formatting)
- ✅ Template variables work better in separate file
- ✅ Can have language variants (en.md, ru.md)
- ✅ System prompt can be much longer without cluttering config
- ✅ Easier to review/diff system prompt changes

**Cons:**
- ❌ Two files instead of one
- ❌ Slight deviation from pure BMAD (but compatible)

**Decision:** Benefits outweigh the cost for luka_agent's needs.

---

### Why YAML-only (Not XML)?

**Reasons:**
- ✅ Simpler for most agents
- ✅ Better BMAD alignment (BMAD uses YAML primarily)
- ✅ Easier to edit and maintain
- ✅ Better tool support (linters, validators)
- ✅ Familiar format for developers
- ✅ Good enough expressiveness for current needs
- ✅ All current features work perfectly with YAML

**Decision:** YAML-only architecture. All agent definitions use YAML format.

**Note:** XML support was considered but removed in favor of simplicity. Current YAML structure provides all necessary features:
- Metadata and persona definitions
- Menu actions
- Tool configuration
- Knowledge base management
- LLM settings
- Agent delegation

---

### Why luka_extensions Section?

**Reasons:**
- ✅ Clear separation: BMAD core vs luka-specific
- ✅ Easy to identify what's portable (agent section)
- ✅ Easy to identify what's luka-specific (luka_extensions)
- ✅ Backward compatible - can ignore luka_extensions in other systems
- ✅ Namespaced - won't conflict with future BMAD additions

**Decision:** Keep luka-specific features in separate namespace.

---

## Migration from Previous Version

### Old Architecture (XML hybrid)

```
agent_name/
├── config.yaml          # Had xml_definition reference
├── agent.xml            # Duplicate XML definition
└── system_prompt.md
```

### New Architecture (YAML only)

```
agent_name/
├── config.yaml          # Pure YAML (BMAD core + luka extensions)
├── system_prompt.md     # Same
└── README.md            # Optional documentation
```

### Migration Steps

1. **Remove agent.xml** - No longer used
2. **Update config.yaml** - Remove xml_definition reference
3. **Keep YAML definitions** - agent.persona and agent.menu in YAML
4. **Keep system_prompt.md** - No changes needed
5. **Add README.md** - Optional but recommended
6. **Validate** - Test with CLI

---

## Summary

✅ **Clean YAML-only Architecture**

- **config.yaml** - BMAD agent definition + luka integration
- **system_prompt.md** - Agent system prompt template with template variables
- **README.md** - Developer documentation (optional but recommended)
- **prompts/** - Optional language variants (en.md, ru.md, etc.)

✅ **BMAD Compatible**

- agent section follows BMAD format exactly
- Can import BMAD YAML agents with minimal changes
- Can export luka agents to BMAD (remove luka_extensions)

✅ **Enhanced for Luka Needs**

- **Tool management** - enabled_tools with selective access
- **Knowledge base configuration** - Multiple KB indices with {user_id} substitution
- **LLM configuration** - Provider, model, temperature, streaming
- **Data access controls** - Allowed/forbidden KB patterns
- **Agent delegation** - dependencies.agents for cross-agent routing
- **Auto-switching** - intent_triggers for keyword-based agent activation
- **Internationalization** - Language variants and template variables
- **Dynamic rendering** - Template variables for user/platform/language context

✅ **Developer Friendly**

- Clear three-file structure
- Template variables for dynamic prompts
- Comprehensive CLI tools (list, validate, info, test)
- Real examples (general_luka, crypto_analyst)
- Easy to create, test, deploy

✅ **Currently Implemented Features**

- YAML-based configuration ✅
- System prompt rendering with template variables ✅
- Tool configuration and access control ✅
- Knowledge base management ✅
- LLM provider configuration ✅
- Agent delegation ✅
- Intent-based auto-switching ✅
- Language variants (i18n) ✅
- CLI validation and testing ✅

---

**The architecture is now aligned with BMAD while supporting luka_agent's extended features. All documented features are implemented and working.**
