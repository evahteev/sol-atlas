"""
Support tools for Luka Bot - Phase 4.

Adapted from bot_server/agents/tools/support_tools.py.
Simplified for Phase 4 (no Camunda integration yet).

Phase 5: Will add full Camunda support BPMN process integration.
"""
from pydantic_ai import Tool, RunContext  # FIX 33: Add RunContext
from pydantic import Field
from loguru import logger

from ..context import ConversationContext


async def get_support_info(
    ctx: RunContext[ConversationContext],  # FIX 33: Use RunContext wrapper
    question: str = Field(description="User's support question or issue")
) -> str:
    """
    Provide support information and help resources.
    
    Phase 4: Returns static support info and resources.
    Phase 5+: Will integrate with Camunda app_support process.
    
    Args:
        ctx: Conversation context with user info
        question: Specific question or issue the user needs help with
    
    Returns:
        Support information and available resources
    """
    try:
        conv_ctx = ctx.deps  # FIX 33: Extract context
        logger.info(f"🔧 TOOL EXECUTED: get_support_info - User {conv_ctx.user_id} - Question: {question[:50]}...")
        
        support_message = f"""📞 **Support & Help Resources**

**Your Question:** {question}

**Getting Help with Luka:**
- **Commands:** Type `/` to see all available commands
- **Threads:** Use `/chat` to manage conversation threads  
- **Tasks:** Use `/tasks` to view and manage your tasks
- **Profile:** Use `/profile` to adjust your settings and language

**Common Questions:**

🔹 **How do I create a new thread?**
   Use the "➕ New Thread" button in `/chat` or just start typing!

🔹 **How do I change my language?**
   Go to `/profile` → Click "🌍 Change Language"

🔹 **How do I reset everything?**
   Use `/reset` to clear all data and start fresh

🔹 **How do threads work?**
   Each thread is a separate conversation with its own history and context

**Documentation & Community:**
- 📚 Bot Guide: https://gurunetwork.ai/docs/luka
- 💬 Community: https://t.me/dexguru
- 🌐 Website: https://gurunetwork.ai

**Need Human Support?**
For technical issues or account problems, contact:
- Telegram: @GuruKeeperBot
- Email: support@gurunetwork.ai

Is there anything specific I can help you with right now?"""

        return support_message
        
    except Exception as e:
        logger.error(f"❌ Error in get_support_info tool: {e}")
        return """**Support Information**

For assistance, please contact:
- Telegram: @GuruKeeperBot  
- Website: https://gurunetwork.ai
- Community: https://t.me/dexguru

Our support team is here to help!"""


async def connect_to_support(
    ctx: RunContext[ConversationContext],  # FIX 33: Use RunContext wrapper
    reason: str = Field(description="Reason for contacting human support")
) -> str:
    """
    Connect user to human support team.
    
    Phase 4: Shows contact information and escalation path.
    Phase 5+: Will start Camunda app_support BPMN process for ticketing.
    
    Args:
        ctx: Conversation context
        reason: Reason for contacting support
    
    Returns:
        Support escalation message with contact info
    """
    try:
        conv_ctx = ctx.deps  # FIX 33: Extract context
        logger.info(f"🔧 TOOL EXECUTED: connect_to_support - User {conv_ctx.user_id} - Reason: {reason[:50]}...")
        
        # Phase 5: Will integrate with Camunda
        # process_instance = await start_support_process(ctx, reason)
        
        return f"""🎫 **Support Request Initiated**

**Your Issue:** {reason}

**✨ Coming Soon:** Automated support ticketing via Camunda workflows!

**For now, please contact our support team directly:**

📱 **Telegram:** @GuruKeeperBot
📧 **Email:** support@gurunetwork.ai  
🌐 **Website:** https://gurunetwork.ai/support
💬 **Community:** https://t.me/dexguru

**What to include:**
- Your user ID: `{ctx.user_id}`
- Thread ID: `{ctx.thread_id or 'N/A'}`
- Issue description: {reason}

**In the meantime:**
- Check `/profile` for settings and preferences
- Use `/tasks` to manage your tasks
- Try `/reset` if experiencing technical issues

Our support team typically responds within 24 hours. Thank you for your patience!

Is there anything else I can help you with right now?"""
        
    except Exception as e:
        logger.error(f"❌ Error in connect_to_support tool: {e}")
        return f"""**Support Request Noted**

Issue: {reason}

Please contact support directly:
- Telegram: @GuruKeeperBot
- Website: https://gurunetwork.ai

We're here to help!"""


def get_tools():
    """
    Return all support-related tools for pydantic-ai agent.
    
    Returns:
        List of Tool objects for agent registration
    """
    return [
        Tool(
            get_support_info,
            name="get_support_info",
            description="Get help resources, documentation, and answers to common questions about using Luka"
        ),
        Tool(
            connect_to_support,
            name="connect_to_support",
            description="Connect user to human support team when escalation is needed or issue requires human assistance"
        )
    ]


def get_prompt_description():
    """
    Return the system prompt description for support tools.
    
    This text is injected into the agent's system prompt to explain
    when and how to use support tools.
    
    Returns:
        Prompt description string
    """
    return """**Support Tools:**
You have access to support tools to help users:
- `get_support_info`: Provide help resources, documentation, and answer common questions
- `connect_to_support`: Escalate to human support when needed

Use support tools when:
- User asks "how do I...?" questions
- User reports issues or problems  
- User needs human assistance
- User asks about features or documentation

Always try to help directly first, but don't hesitate to escalate to human support for complex issues."""


__all__ = [
    'get_support_info',
    'connect_to_support',
    'get_tools',
    'get_prompt_description',
]

