# Sub-Agent Development Guide

**Expert system for creating YAML-based specialized AI personalities for luka_agent runtime.**

---

<objective>
Create production-ready sub-agents that:
- Define unique AI personalities with specialized expertise
- Work identically on Telegram and Web platforms
- Follow BMAD-compatible YAML structure with Luka extensions
- Provide consistent tool access and knowledge base integration
- Use template variables for dynamic prompt rendering
</objective>

<context>
## Architecture Overview

luka_agent provides a unified sub-agent system that serves both platforms:

```
┌─────────────────────────────────────────────────┐
│           luka_agent (Execution Engine)          │
│  ┌────────────────────────────────────────┐    │
│  │         SubAgentLoader                 │    │
│  │  ┌──────────────────────────────┐      │    │
│  │  │  Sub-Agents (Personalities)  │      │    │
│  │  │  - general_luka/             │      │    │
│  │  │    - config.yaml             │      │    │
│  │  │    - system_prompt.md        │      │    │
│  │  │  - crypto_analyst/           │      │    │
│  │  │    - config.yaml             │      │    │
│  │  │    - system_prompt.md        │      │    │
│  │  │  - [your agents here]        │      │    │
│  │  └──────────────────────────────┘      │    │
│  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
┌──────────────┐        ┌──────────────┐
│   Telegram   │        │     Web      │
│   (luka_bot) │        │ (ag_ui_gate) │
└──────────────┘        └──────────────┘
```

**Key Benefits:**
- ✅ Single implementation serves both platforms
- ✅ Specialized expertise domains (general, crypto, travel, etc.)
- ✅ BMAD-compatible core structure
- ✅ Dynamic prompt rendering with template variables
- ✅ Isolated tool sets and knowledge bases

**Directory Structure:**
```
luka_agent/sub_agents/
├── __init__.py
├── loader.py                # SubAgentLoader singleton
├── TEMPLATE/                # Template for new agents
│   ├── config.yaml
│   ├── system_prompt.md
│   └── README.md
├── general_luka/            # Default general assistant
│   ├── config.yaml
│   ├── system_prompt.md
│   ├── prompts/
│   │   ├── en.md
│   │   └── ru.md
│   └── README.md
├── crypto_analyst/          # Crypto domain specialist
│   ├── config.yaml
│   ├── system_prompt.md
│   └── README.md
└── [your agents here]/
```
</context>

---

## Table of Contents

- [Quick Start](#quick-start)
- [Sub-Agent Structure](#sub-agent-structure)
- [Creating a New Sub-Agent](#creating-a-new-sub-agent)
- [Configuration Reference](#configuration-reference)
- [System Prompt Writing](#system-prompt-writing)
- [Testing & Validation](#testing--validation)
- [Best Practices](#best-practices)
- [Example Patterns](#example-patterns)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

<requirements>
### Prerequisites

Before creating a sub-agent, ensure you understand:

1. **YAML Structure**: config.yaml with BMAD core + luka_extensions
2. **System Prompts**: Markdown files with template variables
3. **Template Variables**: `{agent_name}`, `{user_name}`, `{platform}`, `{language}`
4. **Tool Configuration**: enabled_tools list from available tools
5. **Knowledge Bases**: KB index patterns with {user_id} substitution
6. **LLM Configuration**: provider, model, temperature settings

### Sub-Agent Requirements Checklist

- [ ] **Platform-agnostic**: Works identically on Telegram and Web
- [ ] **YAML config**: config.yaml with BMAD core + luka_extensions
- [ ] **System prompt**: system_prompt.md with template variables
- [ ] **Unique persona**: Clear role, identity, communication style
- [ ] **Tool access**: Relevant tools from available tool set
- [ ] **Knowledge bases**: Appropriate KB indices
- [ ] **LLM config**: Provider, model, temperature
- [ ] **Validation**: Passes `python -m luka_agent.cli validate {agent_id}`
- [ ] **Testing**: Deployed and tested on both platforms
</requirements>

---

## Sub-Agent Structure

<output>
### Standard Sub-Agent Pattern

Every sub-agent follows this two-file structure:

**1. config.yaml** - BMAD-compatible YAML with Luka extensions
**2. system_prompt.md** - LLM instructions with template variables
**3. README.md** (optional) - Developer documentation

```
my_agent/
├── config.yaml           # REQUIRED - Agent definition
├── system_prompt.md      # REQUIRED - LLM instructions
├── prompts/              # OPTIONAL - Language variants
│   ├── en.md
│   └── ru.md
└── README.md             # OPTIONAL - Developer docs
```

### config.yaml Structure

```yaml
# =============================================================================
# BMAD Core Section (100% Compatible)
# =============================================================================

agent:
  # Metadata - Who is this agent?
  metadata:
    id: "agent_id"                    # Unique identifier (snake_case)
    name: "Display Name"              # User-facing name
    title: "Full Title"               # Detailed role title
    icon: "🤖"                        # Emoji icon for UI
    version: "1.0.0"                  # Semantic versioning
    description: "One-sentence description"

  # Persona - Agent's personality and expertise
  persona:
    role: "Primary role description"

    identity: |
      Detailed description of who the agent is.

      You help users with:
      - Task 1
      - Task 2
      - Task 3

    communication_style: "Tone, pacing, language style"

    principles:
      - "ALWAYS [action] because [reason]"
      - "NEVER [action] because [reason]"
      - "USE [technique] when [condition]"

  # Menu - Quick actions (BMAD compatibility)
  menu:
    - label: "🔍 Action Label"
      description: "What this action does"
      action:
        type: "tool"
        tool: "tool_name"
        prompt_template: "Template with {user_input}"

# =============================================================================
# Luka Extensions
# =============================================================================

luka_extensions:
  # System Prompt Configuration
  system_prompt:
    base: "sub_agents/{agent_id}/system_prompt.md"

    language_variants:
      en: "sub_agents/{agent_id}/prompts/en.md"
      ru: "sub_agents/{agent_id}/prompts/ru.md"

    template_vars:
      agent_name: "{metadata.name}"
      user_name: "{user.name}"
      platform: "{state.platform}"
      language: "{state.language}"

  # Tool Access
  enabled_tools:
    - "knowledge_base"
    - "sub_agent"
    - "youtube"
    - "support"

  # Knowledge Bases
  knowledge_bases:
    - "user-kb-{user_id}"

  # LLM Configuration
  llm_config:
    provider: "ollama"      # "ollama" or "openai"
    model: "llama3.2"       # Model name
    temperature: 0.7        # 0.0-1.0
    max_tokens: 2000
    streaming: true

  # Capabilities
  capabilities:
    data_access:
      allowed_kb_patterns:
        - "user-kb-*"
        - "public-*"
      forbidden_kb_patterns:
        - "admin-*"

    features:
      can_create_threads: true
      can_execute_workflows: true
      can_search_external: false
      can_modify_user_data: false

  # Dependencies (optional)
  dependencies:
    agents:
      - id: "other_agent"
        description: "When to use this agent"
        trigger_keywords:
          - "keyword1"
          - "keyword2"

  # Intent Triggers (optional - for auto-switching)
  intent_triggers:
    - "keyword1"
    - "keyword2"
```

### system_prompt.md Structure

```markdown
# System Prompt for {agent_name}

You are **{agent_name}** {metadata.icon}, {persona.role}.

## Your Identity

{persona.identity}

## Communication Style

{persona.communication_style}

## Core Principles

1. **Principle 1**: {persona.principles[0]}
2. **Principle 2**: {persona.principles[1]}
3. **Principle 3**: {persona.principles[2]}

## Available Tools

### 🔍 tool_name_1

**When to use:**
- Use case 1
- Use case 2

**When NOT to use:**
- Anti-pattern 1

**Usage Example:**
```
User: "Example query"
→ tool_name_1(param="value")
```

**Critical Rules:**
- ALWAYS do X before Y
- NEVER do Z because [reason]

### 🎥 tool_name_2

[Same structure]

## Example Interactions

### Example 1: [Scenario Name]

**User:** "Example user message"

**Good Response:**
```
Your response here...

[If calling tool: tool_name(params)]

Explanation of what you're doing and why.
```

**Why This Works:**
- Reason 1
- Reason 2

## Edge Cases

### User Says "I Don't Know"

- Offer 2-3 simple options
- Explain each briefly
- Reassure them

### User Changes Topic

- Acknowledge positively
- Offer to switch focus
- Continue naturally

## Platform Context

- **Platform:** {platform}
- **User:** {user_name}
- **Language:** {language}

**Language Rule:** Always respond in {language} unless explicitly asked otherwise.

## Final Reminders

1. **Be Concise**: Respect user's time
2. **Use Tools**: When they provide better answers
3. **Be Transparent**: Explain what you're doing
4. **Stay In Character**: Maintain persona consistently
5. **Respect Boundaries**: Never exceed capabilities

You are **{agent_name}**. [Closing statement]
```

### Why This Pattern?

<constraints>
**Design Rationale:**

1. **BMAD Core Section**
   - WHY: Portable across BMAD-compatible systems
   - WHY: Standard metadata enables tool discovery
   - WHY: Persona structure guides LLM behavior

2. **Luka Extensions**
   - WHY: Platform-specific features (tools, KBs)
   - WHY: Runtime configuration (LLM provider)
   - WHY: Isolated from BMAD core for compatibility

3. **System Prompt Markdown**
   - WHY: Human-readable for editing
   - WHY: Template variables enable dynamic content
   - WHY: Language variants support i18n

4. **Template Variables**
   - WHY: One prompt template, many contexts
   - WHY: User-specific personalization
   - WHY: Platform-aware behavior
</constraints>
</output>

---

## Creating a New Sub-Agent

<implementation>
### Step-by-Step Process

#### Step 1: Create Directory Structure

```bash
cd /path/to/bot/luka_agent/sub_agents
mkdir my_agent
cd my_agent
```

Or copy template:
```bash
cp -r TEMPLATE my_agent
cd my_agent
```

#### Step 2: Define Agent Identity

Answer these questions:

**Who is this agent?**
- Role: "Crypto Market Analyst", "Trip Planning Consultant"
- Expertise: What domains does it know deeply?
- Personality: Formal? Friendly? Data-driven?

**What can it do?**
- Tools: Which tools does it need?
- Knowledge: Which KB indices should it access?
- Capabilities: What are its boundaries?

**How does it communicate?**
- Style: Concise? Detailed? Technical?
- Tone: Professional? Warm? Serious?
- Language: Simple? Domain jargon?

**What are its boundaries?**
- Can it execute transactions?
- Which KBs are forbidden?
- What should it NEVER do?

#### Step 3: Write config.yaml

```yaml
# my_agent/config.yaml

agent:
  metadata:
    id: "my_agent"
    name: "My Agent"
    title: "My Specialized Agent"
    icon: "🤖"
    version: "1.0.0"
    description: "Brief description of what this agent does"

  persona:
    role: "Specialized Role Description"

    identity: |
      You are [Name], a [role] with expertise in [domain].

      You help users with:
      - Task 1
      - Task 2
      - Task 3

    communication_style: "Describe tone, pacing, language style"

    principles:
      - "Core principle 1: Why it matters"
      - "Core principle 2: Why it matters"
      - "Core principle 3: Why it matters"

  menu: []

luka_extensions:
  system_prompt:
    base: "sub_agents/my_agent/system_prompt.md"
    template_vars:
      agent_name: "{metadata.name}"
      user_name: "{user.name}"
      platform: "{state.platform}"
      language: "{state.language}"

  enabled_tools:
    - "knowledge_base"
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
```

<validation>
**Config Best Practices:**

✅ **DO:**
- Use lowercase snake_case for id
- Write clear, specific persona.identity
- List only relevant tools
- Set appropriate temperature (0.3-0.5 for factual, 0.7-0.9 for creative)
- Define clear capability boundaries

❌ **DON'T:**
- Leave descriptions empty
- Enable all tools (be selective)
- Use generic persona ("helpful assistant")
- Skip version number
- Ignore capability constraints

WHY: Clear configuration helps SubAgentLoader properly initialize the agent and provides LLM with specific behavioral guidance.
</validation>

#### Step 4: Write system_prompt.md

See [System Prompt Writing](#system-prompt-writing) section for complete guide.

**Key Points:**
1. Use template variables: `{agent_name}`, `{user_name}`, etc.
2. Provide 3-5 example interactions
3. Document all enabled tools with usage examples
4. Handle edge cases explicitly
5. Use ALWAYS/NEVER for critical rules

#### Step 5: Validate Configuration

```bash
# Validate YAML syntax and structure
python -m luka_agent.cli validate my_agent

# Expected output:
# 🔍 Validating sub-agent: my_agent
# ✅ Config loaded successfully
# ✅ System prompt loaded (2543 chars)
# ✅ Validation passed!
```

**Current Validation Checks:**
- ✅ YAML syntax
- ✅ Required fields (metadata, persona, system_prompt)
- ✅ System prompt file exists
- ✅ Template variable syntax

**Note:** Validation is configuration-only. Does not invoke LLM.

#### Step 6: Test Configuration

```bash
# Test with CLI (configuration validation)
python -m luka_agent.cli test my_agent "Hello, introduce yourself"

# Show agent info
python -m luka_agent.cli info my_agent

# List all agents
python -m luka_agent.cli list
```

**For Real Testing:**
Deploy to luka_bot or ag_ui_gateway and test via Telegram/Web interface.

#### Step 7: Deploy and Iterate

```bash
# Set as default (optional)
# Edit luka_bot/core/config.py or ag_ui_gateway/config.py
DEFAULT_SUB_AGENT = "my_agent"

# Restart services
python -m luka_bot  # Telegram

# or
uvicorn ag_ui_gateway.main:app --reload  # Web

# Monitor logs
tail -f logs/luka_bot.log | grep "my_agent"
```

**Iteration Loop:**
1. Test with realistic user messages
2. Note where agent behavior is wrong
3. Update system_prompt.md with clearer instructions
4. Validate and redeploy
5. Repeat until behavior matches intent

<success_criteria>
**Deployment Checklist:**

- [ ] Agent validated: `python -m luka_agent.cli validate my_agent`
- [ ] Info displays correctly: `python -m luka_agent.cli info my_agent`
- [ ] Agent appears in list: `python -m luka_agent.cli list`
- [ ] Tested on Telegram
- [ ] Tested on Web
- [ ] No errors in logs
- [ ] Agent stays in character
- [ ] Tools work as expected
- [ ] Edge cases handled gracefully
- [ ] README.md documents agent purpose

WHY: Systematic testing catches issues across platforms and ensures consistent behavior.
</success_criteria>
</implementation>

---

## Configuration Reference

<context>
### agent.metadata (REQUIRED)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (snake_case) |
| `name` | string | Yes | User-facing display name (1-3 words) |
| `title` | string | Yes | Full descriptive title |
| `icon` | string | Yes | Single emoji for UI |
| `version` | string | Yes | Semantic version (1.0.0) |
| `description` | string | Yes | One-sentence purpose (max 100 chars) |

**Example:**
```yaml
metadata:
  id: "crypto_analyst"
  name: "Crypto Analyst"
  title: "Crypto Market Expert"
  icon: "📈"
  version: "1.0.0"
  description: "Specialized agent for cryptocurrency market analysis and on-chain insights"
```

### agent.persona (REQUIRED)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | string | Yes | One-line role summary |
| `identity` | string | Yes | Detailed background (multiline) |
| `communication_style` | string | Yes | Tone, pacing, language |
| `principles` | list[string] | Yes | Core behavioral rules |

**Example:**
```yaml
persona:
  role: "Crypto Market Expert + On-Chain Analyst"

  identity: |
    You are Crypto Analyst, a cryptocurrency expert.

    You help users with:
    - Real-time token price analysis
    - Market trend interpretation
    - DeFi protocol insights

  communication_style: "Data-driven and analytical. Always cite sources."

  principles:
    - "ALWAYS cite data sources with timestamps"
    - "NEVER give financial advice"
    - "EXPLAIN technical concepts simply"
```

### luka_extensions.system_prompt (REQUIRED)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `base` | string | Yes | Path to main system prompt |
| `language_variants` | dict | No | Language-specific prompts |
| `template_vars` | dict | No | Available template variables |

**Example:**
```yaml
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
```

### luka_extensions.enabled_tools (REQUIRED)

**Available Tools:**

| Tool | Description | Use Case |
|------|-------------|----------|
| `knowledge_base` | Search user's personal KB | Finding past conversations |
| `sub_agent` | Discover/launch other agents | Agent delegation |
| `youtube` | Fetch video transcripts | Video analysis |
| `support` | Get help resources | User assistance |
| `token_info` | Crypto token data (if available) | Market data |
| `swap_executor` | Token swaps (if available) | Trading |

**Example:**
```yaml
enabled_tools:
  - "knowledge_base"
  - "sub_agent"
  - "youtube"
  - "support"
```

<validation>
**Tool Selection Guidelines:**

✅ **DO:**
- Include only tools relevant to agent's domain
- Always include "knowledge_base" for context retrieval
- Include "sub_agent" to enable agent discovery
- Match tools to agent's expertise

❌ **DON'T:**
- Enable all tools by default
- Include tools agent shouldn't use
- Skip "knowledge_base" unless agent has no memory needs

WHY: Selective tool access keeps agent focused and prevents inappropriate tool usage.
</validation>

### luka_extensions.knowledge_bases (REQUIRED)

**KB Index Patterns:**

| Pattern | Description | Example |
|---------|-------------|---------|
| `user-kb-{user_id}` | User's personal messages | `user-kb-12345` |
| `tg-kb-group-{group_id}` | Group messages | `tg-kb-group-67890` |
| `crypto-tweets` | Domain-specific KB | Global crypto data |
| `public-kb` | Public knowledge base | Shared data |

**Example:**
```yaml
knowledge_bases:
  - "user-kb-{user_id}"      # Personal data
  - "crypto-tweets"          # Domain KB (if specialist)
  - "defi-protocols"         # Domain KB (if specialist)
```

### luka_extensions.llm_config (REQUIRED)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | string | - | "ollama" or "openai" |
| `model` | string | - | Model name |
| `temperature` | float | 0.7 | 0.0 (deterministic) to 1.0 (creative) |
| `max_tokens` | int | 2000 | Max response length |
| `streaming` | bool | true | Enable streaming responses |

**Provider Options:**

| Provider | Models | Use Case | Cost |
|----------|--------|----------|------|
| `ollama` | `llama3.2`, `gpt-oss` | Local, fast | Free |
| `openai` | `gpt-4o`, `gpt-4-turbo` | Advanced reasoning | Paid |

**Temperature Guide:**

| Range | Use Case | Example Agents |
|-------|----------|----------------|
| 0.0-0.3 | Deterministic, factual | Data analysis, code |
| 0.4-0.7 | Balanced | General conversation |
| 0.8-1.0 | Creative | Brainstorming, storytelling |

**Example:**
```yaml
llm_config:
  provider: "ollama"
  model: "llama3.2"
  temperature: 0.7
  max_tokens: 2000
  streaming: true
```

### luka_extensions.capabilities (OPTIONAL)

**Data Access Boundaries:**
```yaml
capabilities:
  data_access:
    allowed_kb_patterns:
      - "user-kb-*"
      - "public-*"
    forbidden_kb_patterns:
      - "admin-*"
      - "system-*"
```

**Feature Flags:**
```yaml
  features:
    can_create_threads: true
    can_execute_workflows: true
    can_search_external: false
    can_modify_user_data: false
```

**Note:** Currently informational. Future versions may enforce these boundaries.
</context>

---

## System Prompt Writing

<requirements>
### Prompt Structure

Every system prompt should have:

1. **Introduction** - Who the agent is
2. **Identity** - Background and expertise
3. **Communication Style** - How to talk
4. **Principles** - Core rules (ALWAYS/NEVER)
5. **Tool Descriptions** - What tools do and when to use them
6. **Example Interactions** - Show good responses
7. **Edge Cases** - Handle unexpected inputs
8. **Context Variables** - Platform, user, language
9. **Final Reminders** - Key takeaways

### Writing Best Practices

<validation>
#### 1. Be Specific, Not Generic

**❌ Bad:**
```markdown
You are a helpful assistant. Be friendly and answer questions.
```

**✅ Good:**
```markdown
You are Crypto Analyst, a market expert with 15+ years in blockchain.

**Core Behavior:**
- ALWAYS cite data sources (on-chain, exchange, social)
- ALWAYS include timestamps with price data
- NEVER give financial advice, only analysis
- NEVER claim certainty in volatile markets
```

#### 2. Provide Examples

**❌ Bad:**
```markdown
Use the token_info tool to get token data.
```

**✅ Good:**
```markdown
### 📊 token_info

**When to use:** User asks about token prices, market cap, volume

**Usage:**
```
User: "What's the price of SOL?"
→ token_info(symbol="SOL")

Response: "Solana (SOL) is trading at $98.50 USD (+5.2% 24h) as of 10:30 UTC."
```

**Critical:**
- ALWAYS include 24h change percentage
- ALWAYS include data timestamp
- ALWAYS format as: $XX.XX USD (±X.X% 24h)
```

#### 3. Handle Edge Cases

**❌ Bad:**
```markdown
Ask the user for their preferences.
```

**✅ Good:**
```markdown
Ask: "What makes a trip special for you?"

**If user says "I don't know":**
- Offer 2-3 simple options: "adventure", "relaxation", "culture"
- Explain each briefly
- Reassure: "No worries! Let's explore together."

**If user changes topic:**
- Acknowledge: "I notice you're interested in [new topic] now."
- Offer to switch: "Should we focus on that instead?"
```

#### 4. Use Template Variables

**Available Variables:**

```markdown
# Agent info
{agent_name}        → "Crypto Analyst"
{metadata.icon}     → "📈"
{persona.role}      → "Crypto Market Expert"

# User info
{user_name}         → "Alice"
{platform}          → "web" or "telegram"
{language}          → "en" or "ru"
```

**Example:**
```markdown
You are **{agent_name}** {metadata.icon}, {persona.role}.

The user ({user_name}) prefers {language}. Always respond in {language}.
```

#### 5. Structure Tool Descriptions

**Template:**

```markdown
### 🔧 tool_name

**When to use:**
- Use case 1
- Use case 2

**When NOT to use:**
- Anti-pattern 1
- Anti-pattern 2

**Usage:**
```
User: "Example query"
→ tool_name(param="value")
```

**Critical Rules:**
- ALWAYS do X
- NEVER do Y because Z
- Format output as: [format]

**Example Response:**
[Show complete example of good response after tool use]
```

### Common Pitfalls

**Pitfall 1: Prompt Is Too Long**

Problem: LLM gets overwhelmed

Solution:
- Focus on CRITICAL rules only
- Use bullet points, not paragraphs
- Aim for 1500-2500 words max

**Pitfall 2: Instructions Are Ambiguous**

**❌ Bad:**
```markdown
Try to be helpful and answer questions when users ask.
```

**✅ Good:**
```markdown
When user asks a question:
1. Check if answer is in conversation history
2. If not, use knowledge_base tool to search
3. If no results, acknowledge and offer alternatives
4. Always cite where information came from
```

**Pitfall 3: No Behavioral Constraints**

**❌ Bad:**
```markdown
You are a crypto analyst. Help users.
```

**✅ Good:**
```markdown
**CRITICAL CONSTRAINTS:**

ALWAYS:
- Cite data sources (on-chain, exchange, social)
- Include timestamps with time-sensitive data
- Warn about volatility and risks
- Explain crypto jargon in simple terms

NEVER:
- Give financial advice ("invest in X")
- Claim certainty about future prices
- Ignore user's risk tolerance
```
</validation>
</requirements>

---

## Testing & Validation

<success_criteria>
### Current Testing Capabilities

**✅ Available Now:**
- **Config Validation** - YAML syntax, required fields, structure
- **Prompt Loading** - Template variable syntax, file existence
- **CLI Commands** - `list`, `validate`, `info`, `test` (config only)
- **Integration Testing** - Deploy to luka_bot/ag_ui_gateway for real testing

### CLI Testing Commands

```bash
# List all sub-agents
python -m luka_agent.cli list

# Validate configuration
python -m luka_agent.cli validate my_agent

# Show detailed info
python -m luka_agent.cli info my_agent

# Test configuration (does NOT invoke LLM)
python -m luka_agent.cli test my_agent "Hello"
```

**Test Command Behavior:**
- ✅ Validates YAML syntax and structure
- ✅ Loads config.yaml and system_prompt.md
- ✅ Checks required fields
- ✅ Verifies template variable syntax
- ❌ Does NOT invoke actual LLM (configuration validation only)

### Integration Testing

**Deploy and Test in Real Environment:**

```bash
# 1. Deploy to Telegram
python -m luka_bot

# 2. Or deploy to Web
uvicorn ag_ui_gateway.main:app --reload

# 3. Monitor logs
tail -f logs/luka_bot.log | grep "my_agent"
```

**Verify:**
- [ ] Agent loads successfully at startup
- [ ] State is hydrated correctly
- [ ] System prompt is rendered with variables
- [ ] Tools work as expected
- [ ] KB searches return results
- [ ] Agent switching works (if enabled)
- [ ] No errors in logs
- [ ] Agent stays in character
- [ ] Edge cases handled gracefully

### Pre-Deployment Checklist

**File Structure:**
- [ ] Directory exists: `luka_agent/sub_agents/{id}/`
- [ ] config.yaml exists and is valid YAML
- [ ] system_prompt.md exists
- [ ] Language variants exist (if configured)
- [ ] README.md documents agent purpose

**Configuration:**
- [ ] All required BMAD fields present
- [ ] All required luka_extensions fields present
- [ ] Domain/ID is unique
- [ ] Version follows semantic versioning
- [ ] Tools listed are available
- [ ] KB indices are valid

**System Prompt:**
- [ ] Uses template variables correctly
- [ ] Provides 3-5 example interactions
- [ ] Handles edge cases
- [ ] Tool descriptions are complete
- [ ] Behavioral constraints are specific
</success_criteria>

---

## Best Practices

<constraints>
### 1. Start Simple, Then Iterate

**Phase 1: MVP**
- Basic config (metadata, persona, tools)
- Simple system prompt (identity + 2-3 tools)
- Test with 2-3 scenarios

**Phase 2: Add Detail**
- More tools
- Edge case handling
- Example interactions

**Phase 3: Optimize**
- Refine based on testing
- Add language variants
- Fine-tune temperature

### 2. Write for the LLM, Not Humans

**Remember:** System prompt is what LLM reads.

**❌ Bad (Human Documentation):**
```markdown
This agent helps users with crypto analysis.
```

**✅ Good (LLM Instructions):**
```markdown
You are Crypto Analyst. When user asks about token prices:
1. Use token_info tool to fetch real-time data
2. Format response: "$XX.XX USD (±X.X% 24h) as of [timestamp]"
3. Always include data source and timestamp
4. NEVER give financial advice
```

### 3. Use Specific Examples

**General Rule:** For every tool, provide at least one complete example.

**Template:**
```markdown
### Tool Name

**User:** "Example user message"
→ tool_name(param="value")

**Good Response:**
```
Natural language response...
[Output from tool]
Explanation of what was done.
```
```

### 4. Enforce Boundaries

**Use `capabilities` section:**

```yaml
capabilities:
  data_access:
    allowed_kb_patterns: ["user-kb-*", "public-*"]
    forbidden_kb_patterns: ["admin-*", "crypto-tweets"]
```

**In system prompt:**

```markdown
**DATA ACCESS BOUNDARIES:**

You CAN search:
- User's personal KB (user-kb-*)
- Public knowledge bases (public-*)

You CANNOT search:
- Admin data (admin-*)
- Crypto Twitter (crypto-tweets) - Use crypto_analyst instead

If user asks for forbidden data:
"For crypto insights, I recommend switching to our Crypto Analyst agent..."
```

### 5. Version Control

**Update `version` when making changes:**

- **Patch (1.0.0 → 1.0.1):** Bug fixes, typos
- **Minor (1.0.0 → 1.1.0):** New tools, enhanced prompts
- **Major (1.0.0 → 2.0.0):** Breaking changes, complete rewrites

**Document in README.md:**

```markdown
## Version History

### 1.1.0 (2025-11-20)
- Added crypto_insight tool
- Enhanced system prompt with examples
- Improved edge case handling

### 1.0.0 (2025-11-15)
- Initial release
```

### 6. Test on Both Platforms

**Always test on Telegram AND Web** before production.

**Platform Differences:**
- **Telegram:** Persistent buttons, emoji-heavy
- **Web:** Quick prompts, cleaner UI

**Ensure:**
- No platform-specific references in prompts
- Markdown renders correctly on both
- Links are clickable on both
- Suggestions appear correctly
</constraints>

---

## Example Patterns

<context>
### Pattern 1: General Assistant (general_luka)

**Use Case:** Default conversational assistant

**Characteristics:**
- Broad tool access
- Multiple knowledge bases
- Lower temperature (0.7)
- Local LLM (Ollama)
- No intent triggers (always available)

**Key Config:**
```yaml
llm_config:
  provider: "ollama"
  model: "llama3.2"
  temperature: 0.7

enabled_tools:
  - "knowledge_base"
  - "sub_agent"
  - "youtube"
  - "support"

knowledge_bases:
  - "user-kb-{user_id}"
```

**When to Use:**
- Default fallback agent
- General conversation
- Multi-domain assistance
- Agent discovery

---

### Pattern 2: Domain Specialist (crypto_analyst)

**Use Case:** Expert in specific domain

**Characteristics:**
- Specialized tools (token_info, swap_executor)
- Domain knowledge bases
- Lower temperature (0.4) for accuracy
- Advanced LLM (GPT-4o)
- Intent triggers for auto-switching

**Key Config:**
```yaml
llm_config:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.4

enabled_tools:
  - "knowledge_base"
  - "token_info"
  - "swap_executor"
  - "youtube"

knowledge_bases:
  - "user-kb-{user_id}"
  - "crypto-tweets"
  - "defi-protocols"

intent_triggers:
  - "crypto"
  - "token"
  - "price"
  - "market"
```

**When to Use:**
- Domain experts (finance, medical, legal)
- Specialized knowledge bases
- Higher reasoning required
- Auto-switching based on keywords

---

### Comparison

| Aspect | General Assistant | Domain Specialist |
|--------|------------------|-------------------|
| LLM | Ollama (local) | OpenAI (cloud) |
| Temperature | 0.7 (balanced) | 0.4 (factual) |
| Tools | General | Domain-specific |
| KBs | User only | User + domain |
| Triggers | None | Domain keywords |
| Use Case | Default | Expert queries |
</context>

---

## Troubleshooting

<validation>
### Common Issues & Solutions

#### Agent Not Discovered

**Symptoms:** `cli list` doesn't show agent

**Diagnose:**
1. Check file location:
   ```bash
   ls luka_agent/sub_agents/my_agent/config.yaml
   ```

2. Validate YAML:
   ```bash
   python -c "import yaml; yaml.safe_load(open('luka_agent/sub_agents/my_agent/config.yaml'))"
   ```

3. Check required fields:
   - `agent.metadata.id`
   - `agent.metadata.name`
   - `agent.persona.role`
   - `luka_extensions.system_prompt.base`

**Solution:** Ensure all required fields present and valid YAML

---

#### System Prompt Not Rendering

**Symptoms:** Agent loads but prompt is empty

**Diagnose:**
1. Check file exists:
   ```bash
   ls luka_agent/sub_agents/my_agent/system_prompt.md
   ```

2. Check template variables:
   ```markdown
   # ✅ Correct
   You are {agent_name}

   # ❌ Wrong
   You are {{agent_name}}
   ```

3. Test rendering:
   ```bash
   python -m luka_agent.cli validate my_agent
   ```

**Solution:** Fix path or template variable syntax

---

#### Agent Not Following Instructions

**Symptoms:** LLM doesn't behave as expected

**Solutions:**

1. **Be more specific:**
   - ❌ "Try to help users"
   - ✅ "When user asks X, do Y. Format as Z."

2. **Add examples:**
   ```markdown
   **Example:**
   User: "What's the price of SOL?"
   You: [Exact response format]
   ```

3. **Use ALWAYS/NEVER:**
   ```markdown
   - ALWAYS cite sources
   - NEVER give financial advice
   ```

4. **Move to principles:**
   ```yaml
   principles:
     - "ALWAYS cite sources because trust"
     - "NEVER give advice because liability"
   ```

---

#### Tools Not Working

**Symptoms:** Agent can't call tools

**Diagnose:**
1. Check enabled in config:
   ```yaml
   enabled_tools:
     - "knowledge_base"
   ```

2. Verify tool exists:
   ```bash
   grep "knowledge_base" luka_agent/tools/__init__.py
   ```

3. Check system prompt describes tool

**Solution:** Add tool to enabled_tools and document in prompt

---

#### Validation Fails

**Symptoms:** `cli validate` reports errors

**Common Errors:**

```yaml
# ❌ Missing required field
agent:
  metadata:
    id: "my_agent"
    # Missing name, title, icon, etc.

# ✅ All required fields
agent:
  metadata:
    id: "my_agent"
    name: "My Agent"
    title: "My Agent"
    icon: "🤖"
    version: "1.0.0"
    description: "..."
```

**Solution:** Add all required BMAD fields

WHY troubleshooting: Most issues stem from missing fields, incorrect paths, or vague instructions. This section helps developers quickly diagnose and fix problems.
</validation>

---

## Resources

- **SubAgentLoader**: `luka_agent/sub_agents/loader.py` - Implementation
- **CLI Tool**: `luka_agent/cli.py` - Testing commands
- **Template**: `luka_agent/sub_agents/TEMPLATE/` - Starter template
- **Examples**:
  - `luka_agent/sub_agents/general_luka/` - General assistant
  - `luka_agent/sub_agents/crypto_analyst/` - Domain specialist
- **BMAD Method**: `luka_agent/BMAD-METHOD/` - Original methodology
- **Project Docs**: `CLAUDE.md` - Project overview

---

## Questions?

For issues or questions:
1. Check existing agents: `general_luka/`, `crypto_analyst/`
2. Validate configuration: `python -m luka_agent.cli validate {agent_id}`
3. Review test output: `python -m luka_agent.cli info {agent_id}`
4. Check logs: `logs/luka_bot.log`
5. Create GitHub issue with:
   - Agent ID and purpose
   - Error logs
   - Steps to reproduce
   - Expected vs actual behavior

---

**Happy sub-agent building! 🚀**

Build specialized AI personalities that solve real problems.
