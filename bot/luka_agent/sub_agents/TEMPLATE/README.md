# Sub-Agent Template (BMAD-Compatible)

**Use this directory as a starting point for creating new BMAD-compatible sub-agents.**

---

## Quick Start

```bash
# 1. Copy template to new sub-agent
cp -r luka_agent/sub_agents/TEMPLATE luka_agent/sub_agents/my_agent

# 2. Edit config.yaml
cd luka_agent/sub_agents/my_agent
# Replace all [PLACEHOLDERS] with your values

# 3. Edit system_prompt.md
# Follow the template structure and customize

# 4. Validate
python -m luka_agent.cli validate my_agent

# 5. Test
python -m luka_agent.cli test my_agent "Hello, who are you?"

# 6. Deploy
# Restart services (luka_bot or ag_ui_gateway)
```

---

## Template Files

### config.yaml (REQUIRED)
Complete BMAD-compatible configuration template with:
- **BMAD Core Section**: metadata, persona, menu (compatible with BMAD Method)
- **Luka Extensions**: system_prompt, enabled_tools, knowledge_bases, llm_config, capabilities
- Detailed comments explaining each field
- Example values and patterns
- Quick customization checklist

### system_prompt.md (REQUIRED)
System prompt template with:
- Standard structure (identity, style, principles, tools, examples)
- Template variables ({agent_name}, {user_name}, {platform}, {language})
- Sections for tool documentation
- Example interaction templates
- Edge case handling guide
- Detailed customization instructions

### README.md (this file)
Instructions for using the template.

---

## Customization Checklist

### Step 1: Configure Agent Metadata

In `config.yaml`:
- [ ] `id: "[AGENT_ID]"` → `id: "my_agent"`
- [ ] `name: "[AGENT_NAME]"` → `name: "My Agent"`
- [ ] `title: "[FULL_TITLE]"` → `title: "My Specialized Agent"`
- [ ] `icon: "[EMOJI]"` → `icon: "🤖"`
- [ ] `description: "[BRIEF_DESCRIPTION]"` → Actual one-sentence description
- [ ] `version: "1.0.0"` → Keep as is for first version

### Step 2: Define Persona

In `config.yaml`:
- [ ] `role:` → Write specific role (not "Assistant")
- [ ] `identity:` → Multi-line description (who, what, why, unique features)
- [ ] `communication_style:` → Tone, pacing, language characteristics
- [ ] `principles:` → 3-5 principles with ALWAYS/NEVER and WHY

**Example:**
```yaml
role: "Crypto Market Expert + On-Chain Analyst"
identity: |
  You are Crypto Analyst, a market expert with 15+ years in blockchain.

  You help users with:
  - Real-time token analysis
  - Market trend insights
  - On-chain data interpretation
communication_style: "Data-driven, concise. Always cite sources."
principles:
  - "ALWAYS cite data sources to build trust"
  - "NEVER give financial advice because legal liability"
```

### Step 3: Configure Menu (BMAD Quick Actions)

In `config.yaml`:
- [ ] `agent.menu:` → Define quick action buttons for users
- [ ] Each menu item needs: `label`, `description`, `action`
- [ ] Action types: `tool`, `command`, `agent`, `workflow`

**Example Menu Items:**
```yaml
menu:
  - label: "🔍 Search Notes"
    description: "Search your knowledge base"
    action:
      type: "tool"
      tool: "knowledge_base"

  - label: "📈 Switch to Crypto Analyst"
    description: "Get market analysis"
    action:
      type: "agent"
      agent_id: "crypto_analyst"
```

**When to use menu:**
- Provide 3-5 most common actions
- Make it easy for users to discover capabilities
- Guide users through complex workflows

### Step 4: Configure Tools & Knowledge Bases

In `config.yaml`:
- [ ] `enabled_tools:` → List only relevant tools
- [ ] `knowledge_bases:` → Add domain-specific indices if needed

**Common Tools:**
- `knowledge_base` - Recommended for most agents
- `sub_agent` - Enables agent discovery
- `youtube` - For video analysis
- `support` - For help resources
- `token_info`, `swap_executor` - Domain-specific (crypto)

### Step 5: Add Dependencies (Optional - BMAD Compatibility)

In `config.yaml`:
- [ ] `dependencies.tasks:` → Reusable workflows this agent can execute
- [ ] `dependencies.templates:` → Document templates
- [ ] `dependencies.agents:` → Other agents for delegation
- [ ] `dependencies.data:` → Static reference data

**When to use dependencies:**
- Agent needs multi-step workflows (tasks)
- Agent creates documents from templates
- Agent delegates to specialized agents
- Agent needs reference data (CSV, JSON)

#### Creating Tasks

Tasks are executable workflows (3-5 interactive steps). See `tasks/example_task.md` for complete example.

**Create a task:**
```bash
mkdir -p sub_agents/my_agent/tasks
cp sub_agents/TEMPLATE/tasks/example_task.md sub_agents/my_agent/tasks/my_task.md
# Edit my_task.md with your workflow
```

**Task structure:**
```markdown
# Task Name

## Task Configuration
```yaml
task:
  id: "my_task"
  name: "My Task"
  elicit: true
  variables:
    var1: "Description"
  output:
    default_file: "output/{var1}-{date}.md"
```

## Execution Steps
### Step 1: Initialize
### Step 2: Process
### Step 3: Finalize
```

**Reference in config.yaml:**
```yaml
dependencies:
  tasks:
    - id: "my_task"
      path: "sub_agents/my_agent/tasks/my_task.md"
      description: "Task description"
      elicit: true
```

#### Creating Workflows

Workflows are complex multi-step processes (5+ steps, branching logic). See `workflows/example_workflow/` for complete example.

**Create a workflow:**
```bash
mkdir -p sub_agents/my_agent/workflows/my_workflow
cp sub_agents/TEMPLATE/workflows/example_workflow/workflow.yaml sub_agents/my_agent/workflows/my_workflow/
cp sub_agents/TEMPLATE/workflows/example_workflow/instructions.md sub_agents/my_agent/workflows/my_workflow/
# Edit workflow.yaml and instructions.md
```

**Workflow directory:**
```
workflows/my_workflow/
├── workflow.yaml      # Configuration
├── instructions.md    # Execution steps with XML tags
├── template.md        # Output template (optional)
└── checklist.md       # Validation checklist (optional)
```

**Reference in config.yaml:**
```yaml
dependencies:
  workflows:
    - id: "my_workflow"
      path: "sub_agents/my_agent/workflows/my_workflow"
      description: "Workflow description"
```

#### Agent Delegation

**Example:**
```yaml
dependencies:
  agents:
    - id: "crypto_analyst"
      description: "Delegate crypto analysis"
      trigger_keywords: ["token", "price", "market"]
```

**See Also:**
- Complete task/workflow guide: `SUB_AGENT_DEV_GUIDE.md` → "Creating Tasks" and "Creating Workflows" sections
- Example files: `TEMPLATE/tasks/example_task.md` and `TEMPLATE/workflows/example_workflow/`

### Step 6: Set LLM Configuration

In `config.yaml`:
- [ ] `provider:` → "ollama" (default) or "openai" (advanced)
- [ ] `model:` → "llama3.2" (ollama) or "gpt-4o" (openai)
- [ ] `temperature:` → 0.3-0.5 (analytical), 0.6-0.7 (balanced), 0.8+ (creative)

### Step 7: Write System Prompt

In `system_prompt.md`:
- [ ] Keep template structure (don't rearrange sections)
- [ ] Document all enabled tools (copy tool section template)
- [ ] Write 3-5 complete example interactions
- [ ] Add domain-specific edge cases
- [ ] Update closing statement with agent purpose
- [ ] Remove instruction comments at bottom

**Tool Documentation Template:**
```markdown
### 🔍 tool_name

**When to use:**
- Specific use case 1
- Specific use case 2

**Usage Example:**
```
User: "Example query"
→ tool_name(param="value")
```

**Critical Rules:**
- ALWAYS do X
- NEVER do Y because Z
```

### Step 8: Add Language Variants (Optional)

If supporting multiple languages:
```bash
mkdir prompts
cp system_prompt.md prompts/en.md
cp system_prompt.md prompts/ru.md
# Edit each variant in appropriate language
```

In `config.yaml`:
```yaml
language_variants:
  en: "sub_agents/my_agent/prompts/en.md"
  ru: "sub_agents/my_agent/prompts/ru.md"
```

### Step 9: Validate & Test

```bash
# Validate YAML syntax and structure
python -m luka_agent.cli validate my_agent

# Test basic conversation
python -m luka_agent.cli test my_agent "Hello, introduce yourself"

# Test tool usage
python -m luka_agent.cli test my_agent "Search my notes for X"

# Test edge cases
python -m luka_agent.cli test my_agent "idk"

# List all agents (verify yours appears)
python -m luka_agent.cli list
```

### Step 10: Deploy & Monitor

```bash
# Set as default (optional)
# Edit luka_bot/core/config.py or ag_ui_gateway/config.py:
DEFAULT_SUB_AGENT = "my_agent"

# Restart services
python -m luka_bot  # Telegram
# or
uvicorn ag_ui_gateway.main:app --reload  # Web

# Monitor logs
tail -f logs/luka_bot.log | grep "my_agent"
```

---

## BMAD Compatibility

This template follows **BMAD Method** structure:

### BMAD Core (100% Compatible)
```yaml
agent:
  metadata: {id, name, title, icon, version, description}
  persona: {role, identity, communication_style, principles}
  menu: []  # BMAD menu structure (not used in luka_agent)
```

### Luka Extensions (Additional Features)
```yaml
luka_extensions:
  system_prompt: {base, language_variants, template_vars}
  enabled_tools: [...]
  knowledge_bases: [...]
  llm_config: {provider, model, temperature, ...}
  capabilities: {data_access, features}
```

**Benefits:**
- ✅ Can import BMAD agents with minimal changes
- ✅ Can export luka agents to BMAD ecosystem
- ✅ Access to BMAD community resources
- ✅ Standard agent architecture patterns

**Migration Path:**
1. Take BMAD agent YAML
2. Add `luka_extensions` section
3. Create `system_prompt.md` from BMAD instructions
4. Deploy to luka_agent

---

## Best Practices

### 1. Be Specific in System Prompt

**❌ Bad:**
```markdown
You are a helpful assistant. Be friendly.
```

**✅ Good:**
```markdown
You are Crypto Analyst, a market expert.

ALWAYS cite data sources with timestamps.
NEVER give financial advice - only analysis.
```

### 2. Document All Tools

**❌ Bad:**
```markdown
You have access to tools. Use them when needed.
```

**✅ Good:**
```markdown
### 🔍 search_knowledge_base

**When to use:** User asks about past conversations

**Usage:**
```
User: "Find my notes about X"
→ search_knowledge_base(query="X", date_from="30d")
```

**Critical:** Always cite the source
```

### 3. Provide Examples

Include 3-5 complete example interactions showing:
- Tool usage in context
- Good response format
- Edge case handling

### 4. Handle Edge Cases

Always document how to handle:
- User says "I don't know"
- User changes mind
- Unexpected input
- Out-of-scope questions

### 5. Match Temperature to Task

- **0.3-0.5**: Data analysis, factual responses (crypto_analyst)
- **0.6-0.7**: Balanced conversation (general_luka)
- **0.8-1.0**: Creative brainstorming (creative agents)

---

## Examples to Study

### general_luka/ (General Assistant)
- Broad capabilities
- Multiple tools
- Conversational and helpful
- Good default agent

**Key Learnings:**
- How to handle diverse user needs
- Sub-agent discovery and switching
- Balanced tone and style

### crypto_analyst/ (Domain Specialist)
- Domain-focused (crypto markets)
- Specific tool set (token_info)
- Expert knowledge (crypto-tweets KB)
- Higher-capability model (gpt-4o)

**Key Learnings:**
- Specialized KB usage
- Domain-specific principles
- Advanced LLM configuration

### trip_planner/ (Workflow Guide)
- Multi-step process (5 steps)
- Interactive planning
- Iterative refinement

**Key Learnings:**
- How to guide complex workflows
- Progressive disclosure
- User confirmation patterns

---

## Common Patterns

### General Assistant Pattern
```yaml
enabled_tools: [knowledge_base, sub_agent, youtube, support]
knowledge_bases: [user-kb-{user_id}]
llm_config: {provider: ollama, model: llama3.2, temperature: 0.7}
```

### Domain Specialist Pattern
```yaml
enabled_tools: [knowledge_base, domain_tool_1, domain_tool_2]
knowledge_bases: [domain-specific-kb, user-kb-{user_id}]
llm_config: {provider: openai, model: gpt-4o, temperature: 0.5}
capabilities:
  data_access:
    allowed_kb_patterns: [domain-*, user-kb-*]
```

### Workflow Guide Pattern
```yaml
enabled_tools: [knowledge_base, workflow_tool_1, workflow_tool_2]
llm_config: {temperature: 0.6}  # Balanced for guidance
principles:
  - "ALWAYS ask before making changes"
  - "NEVER suggest >2 options to avoid overwhelm"
```

### Menu-Driven Pattern (BMAD Style)
```yaml
menu:
  - label: "🚀 Start Workflow"
    description: "Begin the guided process"
    action:
      type: "workflow"
      workflow_id: "main_workflow"

  - label: "📋 View Templates"
    description: "Browse available templates"
    action:
      type: "command"
      command: "list_templates"

  - label: "🔄 Switch Agent"
    description: "Change to specialized agent"
    action:
      type: "agent"
      agent_id: "specialist"

dependencies:
  tasks:
    - id: "main_workflow"
      path: "sub_agents/my_agent/tasks/workflow.md"
      elicit: true

  templates:
    - id: "output_template"
      path: "sub_agents/my_agent/templates/output.md"
      variables: [title, content]
```

**Use when:**
- Agent has clear multi-step workflows
- Users need guidance through complex processes
- Want to provide quick access to common actions

### Agent Delegation Pattern (BMAD Dependencies)
```yaml
enabled_tools: [knowledge_base, sub_agent]

dependencies:
  agents:
    - id: "crypto_analyst"
      description: "Crypto market analysis"
      trigger_keywords: ["token", "price", "market"]

    - id: "trip_planner"
      description: "Travel planning"
      trigger_keywords: ["trip", "travel", "vacation"]

    - id: "code_reviewer"
      description: "Code review and analysis"
      trigger_keywords: ["review", "code", "refactor"]

principles:
  - "DELEGATE to specialists when possible"
  - "RECOMMEND appropriate agent for user's needs"
```

**Use when:**
- Agent orchestrates other specialized agents
- Need to route users to appropriate specialists
- Building a "meta-agent" or agent selector

---

## Resources

**Documentation:**
- `luka_agent/sub_agents/SUB_AGENT_DEV_GUIDE.md` - Complete developer guide
- `luka_agent/LUKA_AGENT_PIVOT_ARCHITECTURE.md` - Architecture overview
- `luka_agent/BMAD-METHOD/README.md` - BMAD methodology

**Examples:**
- `luka_agent/sub_agents/general_luka/` - General assistant
- `luka_agent/sub_agents/crypto_analyst/` - Domain specialist
- `luka_agent/sub_agents/trip_planner/` - Workflow guide

**Tools:**
- `luka_agent/cli.py` - CLI testing tool
- `luka_agent/sub_agents/loader.py` - Loader implementation
- `luka_agent/tools/` - Available tools

---

## Troubleshooting

### Agent Not Discovered

**Check:**
```bash
ls luka_agent/sub_agents/my_agent/config.yaml  # File exists?
python -m luka_agent.cli list  # Appears in list?
tail -f logs/luka_bot.log | grep my_agent  # Any errors?
```

**Common Issues:**
- YAML syntax error
- Missing required fields
- Incorrect file path in system_prompt.base

### System Prompt Not Loading

**Check:**
```bash
ls luka_agent/sub_agents/my_agent/system_prompt.md  # File exists?
python -m luka_agent.cli validate my_agent  # Shows prompt size?
```

**Common Issues:**
- Wrong path in config.yaml
- Template variables syntax ({agent_name} not {{agent_name}})

### Agent Behavior Unexpected

**Solutions:**
- Be more specific in system prompt
- Add ALWAYS/NEVER rules to principles
- Provide concrete examples
- Lower temperature for deterministic behavior

---

## Next Steps

1. ✅ Copy template to new directory
2. ✅ Follow customization checklist
3. ✅ Validate configuration
4. ✅ Test with CLI tool
5. ✅ Deploy to development
6. ✅ Monitor user interactions
7. ✅ Iterate based on feedback

**Questions?**
- Review SUB_AGENT_DEV_GUIDE.md
- Study existing sub-agents
- Check troubleshooting section

---

**Happy building! 🚀**

Build specialized AI personalities that delight users and solve real problems.
