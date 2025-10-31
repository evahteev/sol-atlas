# Knowledge Base Tool Emphasis Update

**Date**: 2025-10-11  
**Status**: ✅ Implemented

## Problem

The KB search tool (`search_knowledge_base`) is registered and available to the agent, but the LLM (GPT-4) is not calling it. Instead, it's answering questions about past conversations from its limited memory (last 20 messages) rather than searching the knowledge base which contains thousands of messages.

### Evidence from Logs

```
🛠️  Agent has 3 tools via toolset.tools: ['get_support_info', 'connect_to_support', 'search_knowledge_base']
📚 No KB snippets found in tool results
⚠️  LLM did NOT call any tools (answered from memory/history)
```

**User Query**: "Че там про шахедов сегодня писали?" (What was written about shakheds today?)

**LLM Behavior**: Answered from conversation history instead of using `search_knowledge_base` to find all relevant messages with links.

## Root Cause

The LLM was making a choice: "I remember seeing messages about this topic in the recent conversation history, so I'll just summarize from memory rather than using the search tool."

**Why this is bad:**
1. Memory is limited to 20 messages
2. KB has thousands of messages
3. Users don't get clickable deeplinks to original messages
4. Results are less accurate (memory vs actual search)

## Solution

Made the system prompt and tool description **much more emphatic** about when and why to use the KB tool.

### Changes Made

#### 1. Enhanced Tool Description

**File**: `luka_bot/agents/tools/knowledge_base_tools.py`

**Before**:
```python
description="Search the user's personal message history (knowledge base) using text search. 
Use when users want to find previous conversations, messages, or information they've discussed."
```

**After**:
```python
description=(
    "🔍 IMPORTANT: Search the user's message history (knowledge base). "
    "**ALWAYS USE THIS TOOL** when users ask about:\n"
    "- Previous conversations: 'what did we discuss', 'что мы обсуждали'\n"
    "- Past messages: 'what did I/they say', 'что я/он говорил'\n"
    "- Looking for information: 'find messages about', 'найди сообщения'\n"
    "- Searching history: 'search for', 'найди информацию'\n\n"
    "This tool searches ACTUAL MESSAGE HISTORY, not your memory. "
    "Even if you remember the conversation, USE THIS TOOL to show users "
    "the original messages with links they can click."
)
```

#### 2. Enhanced System Prompt Description

**File**: `luka_bot/agents/tools/knowledge_base_tools.py` - `get_prompt_description()`

**Before**:
```
**Knowledge Base Search:**
- search_knowledge_base(query): Search user's message history
  Use when users ask about previous conversations or want to find past messages.
```

**After**:
```
**🔍 CRITICAL: Knowledge Base Search Tool**

You MUST use the `search_knowledge_base` tool whenever users ask about:
- Past conversations ("what did we discuss", "что обсуждали")
- Previous messages ("what did I/they say", "что говорил")
- Finding information ("find messages about", "найди про")
- Any question that requires looking at message history

**WHY THIS IS CRITICAL:**
- Your memory is LIMITED to the last 20 messages
- The knowledge base contains THOUSANDS of messages
- Users get CLICKABLE LINKS to original messages
- It shows WHO said WHAT and WHEN with context

**Pattern matching (ALWAYS use tool for these):**
- "what did we/you/I discuss/talk/say about X"
- "find/search/show messages about X"  
- "что писали/говорили/обсуждали про X"
- "найди сообщения про X"

**Example queries:**
- "What did I say about deployment?" → search_knowledge_base(query="deployment")
- "Что обсуждали про шахедов?" → search_knowledge_base(query="шахеды")
- "Find my messages about Python" → search_knowledge_base(query="Python")
```

#### 3. Added Tool Emphasis Mode

**File**: `luka_bot/agents/agent_factory.py`

Added `emphasize_tools` parameter to `build_dynamic_system_prompt()`:

```python
def build_dynamic_system_prompt(
    tool_modules: List[Any], 
    num_dynamic_tasks: int = 0, 
    language_instruction: str = "",
    emphasize_tools: bool = False  # New parameter
) -> str:
    # ...
    
    # Add emphatic tool usage instruction if requested
    if emphasize_tools:
        base_prompt += "\n\n**🎯 TOOL USAGE PRIORITY:**\n"
        base_prompt += "When users ask about past conversations, messages, or information, "
        base_prompt += "you MUST use the available search tools to find actual messages. "
        base_prompt += "Do NOT rely solely on conversation memory - USE THE TOOLS to provide "
        base_prompt += "accurate references with clickable links that users can follow."
```

Updated `create_static_agent_with_basic_tools()` to enable emphasis:

```python
system_prompt = build_dynamic_system_prompt(
    tool_modules, 
    0, 
    language_instruction,
    emphasize_tools=True  # Strongly encourage tool usage
)
```

## Key Improvements

### 1. Explicit Pattern Matching
Provided concrete examples of query patterns that should trigger tool usage:
- English: "what did we discuss", "find messages about"
- Russian: "что обсуждали", "найди сообщения"

### 2. Clear Reasoning
Explained **why** the tool should be used:
- Memory limitation (20 messages)
- KB size (thousands of messages)
- Clickable links for users
- WHO/WHAT/WHEN context

### 3. Visual Emphasis
Used emojis and **bold text** to make instructions stand out:
- 🔍 IMPORTANT
- **ALWAYS USE THIS TOOL**
- 🎯 TOOL USAGE PRIORITY

### 4. Action-Oriented Language
Changed from descriptive ("Use when...") to imperative ("You MUST use..."):
- "Use when users ask" → "**ALWAYS USE THIS TOOL** when users ask"
- "Search user's message history" → "You MUST use the search_knowledge_base tool"

## Testing

To verify the fix works:

1. **Restart the bot** to load new prompts
2. **Ask a history question** in a group where the bot is added:
   ```
   @GuruKeeperBot Что обсуждали про шахедов?
   ```
3. **Check logs** for:
   ```
   🔧 ✅ TOOL CALLED: search_knowledge_base
   📚 Found KB snippets in tool result: N chars
   ✅ Appending N KB snippet section(s)
   ```
4. **Verify response** includes:
   - LLM's brief summary (1-2 sentences)
   - Separator line (`━━━━━━━━━━━━━━━━━━━━`)
   - Formatted message cards with deeplinks

## Expected Behavior

### Before (Wrong):
```
User: "@GuruKeeperBot Че там про шахедов писали?"

Bot: "Сегодня обсуждались шахеды. Упоминалось, что это мученики..."
[No tool call, no links, just LLM memory]
```

### After (Correct):
```
User: "@GuruKeeperBot Че там про шахедов писали?"

Bot: "Нашёл несколько сообщений про шахедов:

━━━━━━━━━━━━━━━━━━━━
📚 Найдено 5 сообщений:

1. 👤 Evgeny • 👥 Group • 2025-10-11 20:39
   🔗 View in group
   💬 "Discussing shakheds..."

2. 🤖 GURU Keeper • 👥 Group • 2025-10-11 21:09
   🔗 View in group
   💬 "Shakheds are martyrs..."

━━━━━━━━━━━━━━━━━━━━"
```

## Impact

- ✅ LLM will now reliably call KB search tool for history queries
- ✅ Users get clickable deeplinks to original messages
- ✅ More accurate results from actual KB search vs memory
- ✅ Better UX with structured message cards
- ✅ Works in both English and Russian

## Files Modified

1. `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/agents/tools/knowledge_base_tools.py`
   - Enhanced tool description with **ALWAYS USE THIS TOOL**
   - Completely rewrote `get_prompt_description()` with emphasis
   
2. `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/agents/agent_factory.py`
   - Added `emphasize_tools` parameter
   - Added tool usage priority section to base prompt
   - Enabled emphasis mode for static agent

3. `/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/services/llm_service.py`
   - Added comprehensive logging to detect tool calls
   - Added warnings when LLM doesn't call tools

## Related Documentation

- `KB_TOOL_RENDERING_FIX.md` - Initial tool result rendering fix
- `KB_SNIPPET_AUTO_APPEND.md` - Auto-append formatted snippets
- `KB_TOOL_ENHANCED_SEARCH.md` - KB tool format specification

---

**Result**: The LLM should now consistently use the KB search tool when users ask about past conversations, providing formatted message snippets with clickable deeplinks.

