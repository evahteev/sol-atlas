from pydantic_ai.agent import Agent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.openai import OpenAIModel
from aiogram.utils.i18n import gettext as _
from loguru import logger
from typing import List, Any
from datetime import datetime, timezone

from .context import ConversationContext
# Phase 4-5: Import available tools
from .tools import support_tools
from .tools import youtube_tools
from .tools import knowledge_base_tools  # Phase 5: KB search
from .tools import workflow_tools
from .tools import menu_tools
from .tools import twitter_tools  # Phase 1: Twitter/X content analysis (KB Gathering)
from luka_bot.core.config import settings
from luka_bot.services.user_profile_service import UserProfileService

async def get_language_instruction_for_user(user_id: int) -> str:
    """Get language instruction based on user's language preference."""
    try:
        # Get user language from profile service
        profile = await UserProfileService.get_user_profile(user_id)
        language_code = profile.language if profile else "en"
        logger.info(f"🌐 User {user_id} language preference: {language_code}")
        
        if language_code == 'ru':
            return "\n\n**IMPORTANT LANGUAGE INSTRUCTION**: Always respond in Russian language (русский язык). Use Russian for all your responses unless the user explicitly requests another language. Note: This instruction applies only to your response language, not to content retrieval (e.g., YouTube captions should still prefer English by default)."
        elif language_code == 'en':
            return "\n\n**IMPORTANT LANGUAGE INSTRUCTION**: Always respond in English language. Use English for all your responses unless the user explicitly requests another language. Note: This instruction applies only to your response language, not to content retrieval."
        else:
            # Default to Russian for unknown language codes
            logger.info(f"🌐 Unknown language code '{language_code}' for user {user_id}, defaulting to Russian")
            return "\n\n**IMPORTANT LANGUAGE INSTRUCTION**: Always respond in Russian language (русский язык). Use Russian for all your responses unless the user explicitly requests another language. Note: This instruction applies only to your response language, not to content retrieval (e.g., YouTube captions should still prefer English by default)."
    except Exception as e:
        logger.warning(f"🌐 Error getting language for user {user_id}: {e}, defaulting to Russian")
        return "\n\n**IMPORTANT LANGUAGE INSTRUCTION**: Always respond in Russian language (русский язык). Use Russian for all your responses unless the user explicitly requests another language. Note: This instruction applies only to your response language, not to content retrieval (e.g., YouTube captions should still prefer English by default)."


def build_dynamic_system_prompt(tool_modules: List[Any], num_dynamic_tasks: int = 0, language_instruction: str = "", emphasize_tools: bool = False) -> str:
    """Build system prompt dynamically based on available tool modules."""
    
    # Get localized base prompt (with fallback for testing)
    try:
        base_prompt = _("agent_base_prompt")
        # Check if we got a translation key back instead of actual text
        if base_prompt == "agent_base_prompt" or len(base_prompt) < 50:
            raise LookupError("Translation key not resolved")
    except (LookupError, Exception):
        # Fallback for test environment where i18n context is not set or localization failed
        application_name = settings.LUKA_NAME
        base_prompt = f"""You are {application_name}, an intelligent AI assistant integrated into Telegram.
You're a conversational AI that helps users with a wide range of tasks - from answering questions and having discussions, to organizing information and managing their workflow.

Your core capabilities include:
- Having natural, helpful conversations on any topic
- Searching through users' personal and group knowledge bases to find relevant information
- Analyzing YouTube videos by extracting and discussing their transcripts
- Helping organize thoughts and information across multiple conversation threads
- Assisting with task management and productivity
- Providing information, explanations, and creative help

**When to use tools:**
- When users ask about information from their message history or knowledge base, use the search_knowledge_base tool
- When users share YouTube links or ask about video content, use the get_youtube_transcript tool
- Otherwise, engage naturally using your general knowledge and conversational abilities

## AVAILABLE BOT COMMANDS AND FEATURES

The bot has the following commands that users can access:

**Core Commands:**
- `/start` - Main entry point showing Quick Actions menu with:
  • Chats (count) - Access conversation threads
  • Tasks (count) - View GTD-organized tasks
  • Profile - User settings and preferences

- `/chat` - Conversation thread management
  • View all existing conversation threads
  • Create new threads with custom names
  • Switch between different conversation contexts
  • Each thread maintains separate conversation history
  • Threads can have custom system prompts and KB connections

- `/search` - Knowledge Base search functionality
  • Create/access dedicated "chatbot_search" thread
  • Select which KBs to search from:
    - Personal KB (user's own indexed content)
    - Group KBs (from Telegram groups bot is added to)
  • Toggle multiple KBs simultaneously
  • Search across selected knowledge bases

- `/tasks` - GTD (Getting Things Done) task management (Coming Soon)
  • Inbox - New unprocessed tasks
  • Next - Tasks ready to start
  • Waiting - Tasks blocked/waiting on others
  • Scheduled - Future dated tasks
  • Someday - Future ideas and backlog
  • Integration with Camunda workflows planned
  • LLM-powered task control commands

- `/groups` - Group management features (Coming Soon)
  • Add bot to Telegram groups
  • Map groups/topics to dedicated threads
  • Set group owners for thread management
  • Import recent group history into threads
  • Auto-switch to group thread on notifications

- `/profile` - User profile and settings
  • View user information and statistics
  • Change interface language (English/Russian)
  • Bot preferences (system prompt, KB settings, default model)
  • View running processes (Camunda integration)
  • Access usage statistics and leaderboard

- `/reset` - Clear all user data
  • Delete all conversation threads
  • Clear conversation history
  • Reset session state
  • Fresh start for the user

**Key Features:**
1. **Multi-threaded Conversations** - Users can maintain separate conversation contexts with different configurations
2. **Knowledge Base Integration** - Search across personal and group knowledge bases
3. **YouTube Integration** - Extract and analyze YouTube video transcripts
4. **Language Support** - Interface available in English and Russian
5. **Thread Customization** - Each thread can have custom system prompts and KB connections
6. **Task Management** - GTD-style organization with Camunda workflow integration (in development)
7. **Group Integration** - Connect Telegram groups to dedicated conversation threads (in development)

**Your Role as Assistant:**
- Help users navigate and use these features effectively
- Guide them to the appropriate commands for their needs
- Explain feature capabilities when asked
- Use available tools (search_knowledge_base, get_youtube_transcript, etc.) to fulfill user requests
- Be proactive in suggesting relevant features based on user needs
- Inform users about "Coming Soon" features when they ask about unavailable functionality

## MENU AND NAVIGATION TOOLS

When users ask about menus, commands, or navigation:
- show_start_menu - Display main start menu with quick actions
- show_groups_menu - Display groups management menu
- show_chat_menu - Display chat/threads management menu
- show_profile_menu - Display profile and settings menu
- show_group_settings - Show settings for a specific group (requires group_id)
- list_user_groups - List all groups the user has access to

Use these tools when users:
- Ask "how do I access..."
- Want to see available options or settings
- Ask about commands or menus
- Want to manage groups or view group settings

Always be helpful, professional, and guide users toward completing their available tasks."""
    
    # Add current date/time context for accurate date filtering
    current_dt = datetime.now(timezone.utc)
    date_context = f"""

**📅 CURRENT DATE/TIME CONTEXT:**
Today is {current_dt.strftime('%A, %B %d, %Y')} (UTC: {current_dt.strftime('%Y-%m-%d')})
Current time: {current_dt.strftime('%H:%M UTC')}

⚠️ **CRITICAL FOR DATE FILTERS:**
When searching knowledge base, DO NOT add date filters unless user explicitly mentions time periods.
Leave date_from and date_to EMPTY by default - the tool searches ALL history automatically.
Only add date filters when user says: "last week", "yesterday", "in March", etc.
"""
    
    # Add emphatic tool usage instruction if requested
    if emphasize_tools:
        base_prompt += date_context  # Insert date context here
        base_prompt += "\n\n**🎯 TOOL USAGE PRIORITY:**\n"
        base_prompt += "When users ask about past conversations, messages, or information, "
        base_prompt += "you MUST use the available search tools to find actual messages. "
        base_prompt += "Do NOT rely solely on conversation memory - USE THE TOOLS to provide "
        base_prompt += "accurate references with clickable links that users can follow.\n\n"
        base_prompt += "**⚠️ CRITICAL TOOL USAGE RULES:**\n"
        base_prompt += "1. ALWAYS write 1-3 sentences of text BEFORE calling any tool (users need context)\n"
        base_prompt += "2. Call each tool EXACTLY ONCE per query - NEVER make duplicate/repeated tool calls\n"
        base_prompt += "3. After the tool returns results, generate a brief summary or transition text\n"
        base_prompt += "4. The tool results will be automatically displayed to the user\n"
        base_prompt += "5. Focus on providing context and interpretation, not just raw search results\n\n"
        base_prompt += "**📚 SPECIAL CASE - 'What's in the knowledge base?' Question:**\n"
        base_prompt += "When users ask 'What's in the knowledge base?' or 'What does the KB contain?':\n"
        base_prompt += "- Do NOT call list_recent_messages tool\n"
        base_prompt += "- Do NOT call search_knowledge_base tool\n"
        base_prompt += "- Instead: Explain DESCRIPTIVELY what the KB is (searchable message archive)\n"
        base_prompt += "- Mention it stores: all conversations, who said what, when messages were sent\n"
        base_prompt += "- Explain they can search it with specific queries\n"
        base_prompt += "- This is a QUESTION ABOUT THE FEATURE, not a request to USE the feature"
    
    # Add tool-specific sections
    tool_sections = []
    for module in tool_modules:
        if hasattr(module, 'get_prompt_description'):
            try:
                description = module.get_prompt_description()
                # Check if we got a translation key back instead of actual text
                if description and len(description) > 10 and not description.endswith("_prompt"):
                    tool_sections.append(description)
                else:
                    logger.warning(f"Module {module.__name__} returned invalid prompt description: {description}")
            except Exception as e:
                logger.warning(f"Error getting prompt description from module {module.__name__}: {e}")
    
    # Add dynamic task info if available
    if num_dynamic_tasks > 0:
        try:
            dynamic_section = _("dynamic_tasks_prompt").format(num_tasks=num_dynamic_tasks)
            # Check if we got a translation key back instead of actual text
            if dynamic_section == "dynamic_tasks_prompt" or len(dynamic_section) < 20:
                raise LookupError("Translation key not resolved")
        except (LookupError, Exception):
            # Fallback for test environment where i18n context is not set or localization failed
            dynamic_section = f"\n\nYou have {num_dynamic_tasks} dynamic task(s) available to execute for this user. Use the appropriate task execution tools when the user requests task-related actions."
        tool_sections.append(dynamic_section)
    
    # Combine all sections with language instruction
    sections_to_combine = [base_prompt + language_instruction]
    if tool_sections:
        sections_to_combine.extend(tool_sections)
    
    full_prompt = "\n\n".join(sections_to_combine)
    
    markdown_guidance = """
**FORMATTING REQUIREMENTS**
- Respond using Markdown suitable for chat messages.
- Do not emit raw HTML tags such as <div>, <p>, <span>, <br>, or inline styles.
- Use Markdown syntax for headings, emphasis, lists, links, and code blocks.
- Escape special characters when needed so the text renders correctly in Markdown/HTML viewers.
- Keep tables simple (pipe-separated) if tabular data is necessary.
"""
    
    full_prompt += "\n\n" + markdown_guidance.strip()
    
    return full_prompt

async def create_static_agent_with_basic_tools(user_id: int) -> Agent:
    """Create a fast agent with only static tools (no dynamic task tools)."""
    logger.info("Creating static agent with basic tools for immediate response")
    
    # Create model with automatic provider fallback (Ollama → OpenAI)
    try:
        logger.debug("📦 Step 1a: Importing llm_model_factory...")
        from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
        logger.debug("✅ Import successful")
        
        logger.debug("📦 Step 1b: Calling create_llm_model_with_fallback()...")
        logger.debug(f"   context=user_{user_id}, timeout={settings.OLLAMA_TIMEOUT}")
        
        model = await create_llm_model_with_fallback(
            context=f"user_{user_id}",
            model_settings=ModelSettings(
                temperature=settings.LLM_TEMPERATURE,
                top_p=settings.LLM_TOP_P,
                frequency_penalty=settings.LLM_FREQUENCY_PENALTY,
                presence_penalty=settings.LLM_PRESENCE_PENALTY,
                stop_sequences=["\n\n\n", "User:", "Assistant:"],
                max_tokens=settings.LLM_MAX_TOKENS,
                timeout=settings.OLLAMA_TIMEOUT
            )
        )
        logger.debug(f"✅ Model created: type={type(model).__name__}")
    except Exception as model_error:
        logger.error(f"❌ FATAL: LLM model creation failed: {model_error}", exc_info=True)
        raise
    
    # Build system prompt with user's language preference
    language_instruction = await get_language_instruction_for_user(user_id)
    
    # Minimal default agent: Only KB search + support in system prompt
    # Menu/workflow/twitter modules removed (moved to Bot Assistant sub-agent)
    tool_modules = [support_tools, youtube_tools, knowledge_base_tools]
    system_prompt = build_dynamic_system_prompt(
        tool_modules, 
        0, 
        language_instruction,
        emphasize_tools=True  # Strongly encourage tool usage
    )
    
    # Phase 4-5: Static tools available
    # Important: YouTube tool is invoked heuristically in LLM service to avoid duplicate agent invocations
    # FIX 32b: Revert to Tool() wrappers - issue was the LLM passing string "conversation"
    
    # Minimal default agent: KB search + support only
    # Menu/workflow/twitter tools moved to Bot Assistant sub-agent (coming in Phase 2)
    static_tools = [
        *support_tools.get_tools(),          # ✅ Support help
        *knowledge_base_tools.get_tools(),   # ✅ KB search tool
        # *youtube_tools.get_tools(),       # ✅ YouTube (handled via heuristic path)
        # ❌ REMOVED: workflow_tools, menu_tools, twitter_tools (bot control → Bot Assistant sub-agent)
    ]
    
    # Minimal default agent with KB search + support only
    logger.info(f"Creating MINIMAL DEFAULT agent with {len(static_tools)} tools (KB search + support only)")
    
    # Create agent WITH tools
    try:
        agent = Agent(
            model=model,  # Uses fallback-enabled model
            deps_type=ConversationContext,
            system_prompt=system_prompt,
            tools=static_tools,  # Pass Tool objects
            end_strategy='exhaustive',  # Allow both text and tool execution
            retries=0  # Disable automatic retries to prevent duplicate tool calls
        )
        logger.info("Agent created successfully with tools")
    except Exception as e:
        logger.warning(f"Agent creation with tools failed: {e}")
        # Fallback: create agent without tools
        agent = Agent(
            model=model,  # Uses fallback-enabled model
            deps_type=ConversationContext,
            system_prompt=system_prompt,
            end_strategy='exhaustive',  # Allow both text and tool execution
            retries=0  # Disable automatic retries
        )
        logger.info("Created fallback agent without tools")
    
    logger.info("Static agent created successfully")
    return agent

async def create_agent_with_user_tasks(ctx: ConversationContext) -> Agent:
    """Create an agent instance with user-specific dynamic task tools."""
    
    logger.info(f"Creating agent with dynamic tools for user {ctx.user_id}")
    
    try:
        # Get dynamic task tools for this user
        # Phase 5: Camunda dynamic tools
        # logger.info("Getting dynamic task tools...")
        # dynamic_tools = await camunda_tools.get_dynamic_tools_for_user(ctx)
        # logger.info(f"Got {len(dynamic_tools)} dynamic tools")
        dynamic_tools = []  # Phase 4: No Camunda integration yet
        
        # Create model with automatic provider fallback (Ollama → OpenAI)
        logger.info("Configuring LLM model with automatic fallback...")
        
        from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
        
        model = await create_llm_model_with_fallback(
            context=f"user_{ctx.user_id}_dynamic",
            model_settings=ModelSettings(
                temperature=settings.LLM_TEMPERATURE,
                top_p=settings.LLM_TOP_P,
                frequency_penalty=settings.LLM_FREQUENCY_PENALTY,  # Penalize repetition
                presence_penalty=settings.LLM_PRESENCE_PENALTY,   # Encourage variety
                stop_sequences=["\n\n\n", "User:", "Assistant:"],  # Stop sequences
                max_tokens=settings.LLM_MAX_TOKENS,
                timeout=settings.OLLAMA_TIMEOUT
            )
        )
        logger.info(f"LLM model configured with fallback: {model.model_name}")
        
        # DEBUG logging removed - model now uses automatic fallback system
        
        # Collect tools for this agent
        
        # Skip old debug code - model now uses automatic fallback system
        if False:  # Disabled debug code
            if hasattr(None, 'post'):
                original_post = client.post
                async def logged_post(*args, **kwargs):
                    logger.error("🔧 HTTP DEBUG: =================== POST REQUEST START ===================")
                    logger.error("🔧 HTTP DEBUG: POST request to model")
                    logger.error(f"🔧 HTTP DEBUG: args: {args}")
                    logger.error(f"🔧 HTTP DEBUG: URL: {args[0] if args else 'unknown'}")
                    logger.error(f"🔧 HTTP DEBUG: All kwargs keys: {list(kwargs.keys())}")
                    logger.error(f"🔧 HTTP DEBUG: Provider base_url: {getattr(ollama_provider, 'base_url', 'unknown')}")
                    logger.error("🔧 HTTP DEBUG: =================== POST REQUEST END ===================")
                    
                    # Extract JSON data from body parameter (OpenAI uses 'body' not 'json')
                    json_data = None
                    if 'body' in kwargs:
                        body = kwargs['body']
                        logger.info(f"🔧 HTTP DEBUG: Body type: {type(body)}")
                        if hasattr(body, 'decode'):
                            try:
                                import json as json_lib
                                json_data = json_lib.loads(body.decode('utf-8'))
                                logger.info("🔧 HTTP DEBUG: Successfully parsed JSON from body")
                            except Exception as e:
                                logger.info(f"🔧 HTTP DEBUG: Failed to parse JSON from body: {e}")
                        elif isinstance(body, dict):
                            json_data = body
                            logger.info("🔧 HTTP DEBUG: Body is already dict")
                        else:
                            logger.info(f"🔧 HTTP DEBUG: Body content (first 200 chars): {str(body)[:200]}")
                    elif 'json' in kwargs:
                        json_data = kwargs['json']
                        logger.info("🔧 HTTP DEBUG: Using json parameter")
                    
                    if json_data:
                        logger.info(f"🔧 HTTP DEBUG: Request payload keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'not dict'}")
                        if isinstance(json_data, dict):
                            logger.info(f"🔧 HTTP DEBUG: Model: {json_data.get('model', 'not specified')}")
                            logger.info(f"🔧 HTTP DEBUG: Has tools: {'tools' in json_data}")
                            logger.info(f"🔧 HTTP DEBUG: Has functions: {'functions' in json_data}")
                            if 'tools' in json_data:
                                tools = json_data['tools']
                                logger.info(f"🔧 HTTP DEBUG: Tools count: {len(tools) if isinstance(tools, list) else 'not list'}")
                                if isinstance(tools, list) and tools:
                                    for i, tool in enumerate(tools[:3]):  # Log first 3 tools
                                        if isinstance(tool, dict) and 'function' in tool:
                                            func_name = tool['function'].get('name', 'unnamed')
                                            logger.info(f"🔧 HTTP DEBUG: Tool {i+1}: {func_name}")
                                        else:
                                            logger.info(f"🔧 HTTP DEBUG: Tool {i+1}: {tool}")
                            if 'messages' in json_data:
                                messages = json_data['messages']
                                logger.info(f"🔧 HTTP DEBUG: Messages count: {len(messages) if isinstance(messages, list) else 'not list'}")
                                if isinstance(messages, list):
                                    for i, msg in enumerate(messages):
                                        if isinstance(msg, dict):
                                            role = msg.get('role', 'unknown')
                                            content = msg.get('content', '')
                                            logger.info(f"🔧 HTTP DEBUG: Message {i+1}: role={role}, length={len(content)}")
                                            if role == 'system':
                                                logger.info(f"🔧 HTTP DEBUG: System message content (first 200 chars): {content[:200]}")
                                                logger.info(f"🔧 HTTP DEBUG: System message has 'search_knowledge_base': {'search_knowledge_base' in content}")
                                                logger.info(f"🔧 HTTP DEBUG: System message has 'tool': {'tool' in content.lower()}")
                    
                    try:
                        logger.info("🔧 HTTP DEBUG: Making actual request...")
                        response = await original_post(*args, **kwargs)
                        logger.info(f"🔧 HTTP DEBUG: Request successful, response type: {type(response)}")
                        return response
                    except Exception as e:
                        logger.error(f"🔧 HTTP DEBUG: Request failed with error: {e}")
                        logger.error(f"🔧 HTTP DEBUG: Error type: {type(e)}")
                        if hasattr(e, 'response'):
                            logger.error(f"🔧 HTTP DEBUG: Response status: {getattr(e.response, 'status_code', 'unknown')}")
                            logger.error(f"🔧 HTTP DEBUG: Response text: {getattr(e.response, 'text', 'unknown')}")
                        raise
                pass  # Debug code disabled
        
        # Note: Debug logging disabled - using automatic fallback system now
        
        # TEMPORARILY DISABLE: basic_camunda_tools = camunda_tools.get_tools()
        # TEMPORARILY DISABLE: support_tools_list = support_tools.get_tools()
        kb_tools_list = knowledge_base_tools.get_tools()
        youtube_tools_list = youtube_tools.get_tools()
        # workflow_tools_list = workflow_tools.get_tools()  # Phase 4+: Not yet implemented
        workflow_tools_list = []  # Placeholder
        
        # Combine all tools
        all_tools = [
            *kb_tools_list,
            *youtube_tools_list,
            *workflow_tools_list,
            *dynamic_tools
        ]
        
        logger.info(f"Collected {len(all_tools)} tools for agent")
        
        # Build system prompt
        
        # Get user's language preference
        language_instruction = await get_language_instruction_for_user(ctx.user_id)
        
        # Create a simple, focused system prompt for function calling test
        application_name = settings.LUKA_NAME
        system_prompt = f"""You are {application_name}, an intelligent AI assistant.

You can help users with:
- Service information and support questions
- Executing available business process tasks

**IMPORTANT**: When users ask about services, ALWAYS use the search_knowledge_base tool first to provide accurate information from our knowledge base.

You have {len(dynamic_tools)} task(s) available to execute for this user. Use the appropriate task execution tools when the user requests task-related actions.

Always be helpful and professional.{language_instruction}"""
        
        logger.info(f"Creating agent with {len(all_tools)} tools for user {ctx.user_id}")
        
        try:
            # Create agent with tools
            agent_with_tasks = Agent(
                model=model,  # Uses fallback-enabled model
                deps_type=ConversationContext,
                system_prompt=system_prompt,
                tools=all_tools,  # Pass all tools directly
                end_strategy='exhaustive',  # Allow both text and tool execution
                retries=0  # Disable automatic retries to prevent duplicate tool calls
            )
            
            logger.info(f"Agent created successfully with {len(all_tools)} tools")
            
            return agent_with_tasks
            
        except Exception as e:
            # If model doesn't support tools, create a basic agent without tools
            logger.error(f"🚨 AGENT CREATION ERROR: Model {settings.OLLAMA_MODEL_NAME} does not support function calling/tools!")
            logger.error(f"🚨 AGENT CREATION ERROR: Original exception: {e}")
            logger.error(f"🚨 AGENT CREATION ERROR: Exception type: {type(e)}")
            import traceback
            logger.error(f"🚨 AGENT CREATION ERROR: Full traceback: {traceback.format_exc()}")
            logger.warning("Creating fallback agent without tools...")
            
            # Create simpler system prompt without tool references
            try:
                fallback_prompt = _("agent_fallback_prompt")
            except LookupError:
                application_name = settings.LUKA_NAME
                fallback_prompt = f"You are {application_name}, a helpful AI assistant. Answer user questions as best you can."
            
            # Add user's language instruction to fallback prompt
            language_instruction = await get_language_instruction_for_user(ctx.user_id)
            fallback_prompt += language_instruction

            agent_without_tools = Agent(
                model=model,  # Uses fallback-enabled model
                deps_type=ConversationContext,
                system_prompt=fallback_prompt,
                end_strategy='exhaustive',  # Allow both text and tool execution
                retries=0  # Disable automatic retries
            )
            
            logger.warning("🚨 FALLBACK: Created agent WITHOUT TOOLS - this explains why no tool calls are happening!")
            return agent_without_tools
        
    except Exception as e:
        logger.error(f"Error in create_agent_with_user_tasks: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

async def create_simple_agent_without_tools(user_id: int) -> Agent:
    """Create a simple agent without tools for models that don't support function calling."""
    logger.info("Creating simple agent without tools")
    
    # Create model with automatic provider fallback (Ollama → OpenAI)
    from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
    
    model = await create_llm_model_with_fallback(
        context=f"user_{user_id}_simple",
        model_settings=ModelSettings(
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.5,  # Penalize repetition
            presence_penalty=0.3,   # Encourage variety
            stop_sequences=["\n\n\n", "User:", "Assistant:"],  # Stop sequences
            max_tokens=2000,
            timeout=30.0
        )
    )
    
    # Simple system prompt without tool references
    simple_prompt = _("agent_simple_prompt")
    
    # Add user's language instruction to simple prompt
    language_instruction = await get_language_instruction_for_user(user_id)
    simple_prompt += language_instruction

    simple_agent = Agent(
        model=model,  # Uses fallback-enabled model
        deps_type=ConversationContext,
        system_prompt=simple_prompt,
        end_strategy='exhaustive',  # Allow both text and tool execution
        retries=0  # Disable automatic retries
    )
    
    logger.info("Simple agent created successfully without tools")
    return simple_agent
