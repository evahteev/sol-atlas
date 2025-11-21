# General Luka - Default AI Assistant

**Agent ID:** `general_luka`
**Version:** 1.0.0
**Icon:** 🤖

## Overview

General Luka is the default sub-agent for the luka_agent system. It provides a versatile, general-purpose AI assistant experience for everyday tasks, knowledge management, and agent discovery.

## Purpose

This agent serves as the primary entry point for users, offering:

- **Knowledge Management**: Search and recall past conversations using the user's personal knowledge base
- **Video Analysis**: Fetch and summarize YouTube video content
- **Agent Discovery**: Help users find and switch to specialized agents for complex tasks
- **General Assistance**: Answer questions, provide support, and help with everyday queries

## Agent Characteristics

### Role
Helpful AI Assistant + Knowledge Manager

### Communication Style
- **Friendly** - Approachable and warm
- **Concise** - Respects user's time with direct, actionable responses
- **Professional** - Maintains appropriate boundaries and expertise
- **Adaptive** - Matches user's tone when appropriate

### Core Principles

1. **Be concise and respectful** - Save users' time
2. **Cite sources** - Build trust with attribution
3. **Explain actions** - Maintain transparency
4. **Ask clarifying questions** - Provide better help
5. **Don't assume** - Ask when uncertain
6. **Use specialized agents** - Delegate to experts when needed

## Enabled Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `knowledge_base` | Search user's past conversations and notes | Historical context retrieval |
| `sub_agent` | Discover and switch to specialized agents | Agent delegation |
| `youtube` | Fetch video transcripts and analyze content | Video summarization |
| `support` | Provide help resources and documentation | User assistance |

## Knowledge Bases

- **user-kb-{user_id}**: User's personal knowledge base containing all their past messages

## LLM Configuration

- **Provider**: Ollama (local inference)
- **Model**: llama3.2
- **Temperature**: 0.7 (balanced creativity)
- **Max Tokens**: 2000
- **Streaming**: Enabled

## Capabilities

### Data Access

**Allowed KB Patterns:**
- `user-kb-*` - User knowledge bases
- `public-*` - Public knowledge bases

**Forbidden KB Patterns:**
- `admin-*` - Admin data
- `system-*` - System data

### Features

- ✅ Can create threads
- ✅ Can execute workflows
- ❌ Cannot search external sources (no real-time data)
- ❌ Cannot modify user data

## Agent Dependencies

### Related Agents

- **crypto_analyst** - For cryptocurrency market analysis and on-chain insights
  - Triggered by: crypto, token, price, market, blockchain, defi

## Use Cases

### When to Use General Luka

- Default conversational assistant
- General questions and everyday tasks
- Searching personal knowledge base
- Analyzing YouTube videos
- Finding the right specialized agent
- Getting help with bot features

### When NOT to Use General Luka

- Complex domain-specific tasks (crypto analysis, trip planning)
- Real-time data queries (token prices, market data)
- Tasks requiring specialized expertise

In these cases, General Luka will recommend switching to an appropriate specialized agent.

## Example Interactions

### Knowledge Base Search

**User:** "what did i say about ethereum?"

**Response:**
```
Let me search your knowledge base for mentions of Ethereum...

🔍 knowledge_base(query="ethereum", limit=5)

I found 4 mentions of Ethereum in your history:

1. **Nov 10**: You asked about Ethereum staking rewards (source: msg #5432)
2. **Nov 5**: You discussed ETH price predictions (source: msg #5201)
3. **Oct 28**: You mentioned holding 2.5 ETH (source: msg #4890)
4. **Oct 15**: You asked about Ethereum 2.0 upgrade (source: msg #4567)

Would you like me to elaborate on any of these?
```

### Agent Discovery

**User:** "i need help analyzing token prices"

**Response:**
```
For crypto market analysis, I recommend our Crypto Analyst agent 📈! They specialize in:

- Real-time token price analysis
- Market trend interpretation
- On-chain data insights

Would you like me to switch you to the Crypto Analyst?
```

### YouTube Analysis

**User:** "can you summarize this video? https://youtube.com/watch?v=abc123"

**Response:**
```
Let me fetch the transcript and analyze this video for you...

📺 youtube(url="https://youtube.com/watch?v=abc123")

Video: "How to Trade Crypto" (15:30)

Key points:
- Explains market order vs limit order (2:30-5:00)
- Discusses risk management strategies (6:00-9:00)
- Shows technical analysis basics (10:00-14:00)

The video is best for beginners learning crypto trading fundamentals.
```

## Technical Details

### Platform Support

- ✅ Telegram (via luka_bot)
- ✅ Web (via ag_ui_gateway)

### File Structure

```
general_luka/
├── config.yaml           # Agent configuration (BMAD + Luka extensions)
├── system_prompt.md      # Main LLM instructions
├── prompts/              # Language-specific variants
│   ├── en.md            # English prompt
│   └── ru.md            # Russian prompt
└── README.md            # This file
```

### Template Variables

The system prompt uses these template variables:

- `{agent_name}` - "Luka"
- `{user_name}` - User's display name
- `{platform}` - "telegram" or "web"
- `{language}` - User's preferred language

## Version History

### 1.0.0 (2025-11-18)
- Initial release
- Core tools: knowledge_base, sub_agent, youtube, support
- BMAD-compatible configuration
- Multi-language support (en, ru)
- Crypto analyst agent integration

## Development

### Testing

```bash
# Validate configuration
python -m luka_agent.cli validate general_luka

# Show agent info
python -m luka_agent.cli info general_luka

# List all agents
python -m luka_agent.cli list
```

### Deployment

General Luka is the default agent and loads automatically when:
- User starts a conversation in Telegram
- User opens web chat interface
- No specific agent is requested

## Best Practices

### For Users

1. **Be specific** - The more context you provide, the better the responses
2. **Ask for clarification** - If unsure, ask follow-up questions
3. **Use specialized agents** - Switch to experts for complex tasks
4. **Search your history** - Leverage your personal knowledge base

### For Developers

1. **Keep prompts updated** - Sync system_prompt.md with config.yaml tools
2. **Test on both platforms** - Verify Telegram and Web behavior
3. **Monitor logs** - Check for tool usage patterns and errors
4. **Version properly** - Update version number for changes

## Support

For issues or questions:
- Check logs: `logs/luka_bot.log`
- Validate config: `python -m luka_agent.cli validate general_luka`
- Review system prompt: `luka_agent/sub_agents/general_luka/system_prompt.md`

## License

Part of the luka_agent ecosystem. See main project for license details.
