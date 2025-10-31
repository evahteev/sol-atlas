# Group Onboarding & Admin Controls - Implementation Roadmap

## 🎯 Goals

1. **Personality-driven welcome** - Use bot settings for consistent branding ✅
2. **Drive onboarding** - Get group members to DM bot and register ✅
3. **Admin controls** - Empower group admins to manage bot behavior ✅
4. **History import** - Encourage importing past conversations (Coming Soon)
5. **Smart command menus** - Different commands for DMs, groups, and admins ✅

## ⚡ Architecture Update (2025)

**The bot now uses a unified Thread model for all conversations!**

See **[THREAD_ARCHITECTURE.md](./THREAD_ARCHITECTURE.md)** for full details.

### Key Changes:
- ✅ **Thread** stores all configuration (language, KB, LLM settings, tools)
- ✅ **GroupLink** is simplified to just track user ↔ group access
- ✅ All group settings now in Thread model
- ✅ Per-group agent customization supported
- ✅ Easy to extend for new features

## 📊 Current State

### What Works ✅
- Bot detects when added to group
- **Thread-based architecture** with unified configuration
- Creates group KB index automatically
- Sends welcome messages (static + LLM-generated) with bot personality
- Tracks topics/threads in supergroups
- Auto-initializes on first message if missed bot add event
- **Bot personality from settings** (via Thread.agent_name)
- **Deep links to onboard users** from group → DM
- **Admin detection and controls** (settings, reset, etc.)
- **Commands scoped** for DMs, groups, and admins
- **Language setting per group** (stored in Thread)
- **Inline settings keyboard** for group admins
- **Per-group agent customization** (name, system prompt, tools)

### What's Missing ❌
- History import UI (coming soon)
- Advanced admin UI for thread customization
- Tool selection UI
- Per-topic KB separation

## 🎨 Phase 1: Enhanced Welcome Messages

### Goal: Rich, personality-driven onboarding

### Changes Needed:

1. **Use Bot Personality from Settings:**
   ```python
   from luka_bot.core.config import settings
   
   bot_name = settings.LUKA_NAME  # "Luka"
   bot_personality = settings.LUKA_DEFAULT_SYSTEM_PROMPT
   ```

2. **Add Deep Link to Bot:**
   ```python
   bot_username = (await bot.get_me()).username
   deep_link = f"https://t.me/{bot_username}?start=group_{abs(group_id)}"
   ```

3. **Enhanced Welcome Message Template:**
   ```markdown
   👋 Hello! I'm {bot_name}, your AI assistant!
   
   I've just been added to {group_name} and I'm ready to help!
   
   📊 Setup Complete:
   • 🆔 Group ID: {group_id}
   • 📚 KB Index: {kb_index}
   • ✅ Status: Active and indexing
   
   🚀 Get Started:
   1️⃣ Start a private chat with me: {deep_link}
   2️⃣ Complete quick onboarding (~30 seconds)
   3️⃣ Access powerful features in DM
   
   💬 In This Group:
   • Mention me (@{bot_username}) to ask questions
   • I'll index messages for searchability
   • Group members can search history via DM
   
   📚 Import History (Coming Soon):
   • Admins can import past group messages
   • Use /groups command in DM when available
   • Build comprehensive searchable knowledge base
   
   👤 For Admins:
   • Configure bot settings in DM
   • Manage group integrations
   • Control what gets indexed
   
   🤖 [Personalized LLM welcome follows...]
   ```

4. **Update LLM Welcome Prompt:**
   ```python
   llm_prompt = f"""You are {settings.LUKA_NAME}. You've just been added to the group '{group_title}'.
   
   Write a SHORT (2-3 sentences max), friendly welcome message that:
   - Greets the group members warmly
   - Mentions your key capability: being a helpful AI assistant
   - Encourages them to mention you (@{bot_username}) with questions
   - Shows enthusiasm about helping the group
   
   Be conversational, friendly, and brief. No bullet points or long explanations."""
   ```

### Files to Modify:
- `luka_bot/handlers/group_messages.py` - Update welcome messages
- `luka_bot/locales/*/messages.po` - Add new translation strings

## 🔐 Phase 2: Admin Detection & Controls

### Goal: Empower group admins with bot management

### Admin Detection:

```python
async def is_user_admin_in_group(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Check if user is admin in the group."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False

async def is_user_registered(user_id: int) -> bool:
    """Check if user has completed bot onboarding."""
    from luka_bot.services.user_profile_service import get_user_profile_service
    profile_service = get_user_profile_service()
    profile = await profile_service.get_profile(user_id)
    return profile is not None
```

### Admin Control Menu (Inline Keyboard):

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_group_admin_menu(group_id: int) -> InlineKeyboardMarkup:
    """Create admin control menu for group management."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚙️ Group Settings",
                callback_data=f"group_settings:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Import History (Soon)",
                callback_data=f"group_import:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Group Stats",
                callback_data=f"group_stats:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔗 Manage Threads",
                callback_data=f"group_threads:{group_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Close",
                callback_data="close_menu"
            )
        ]
    ])
```

### When to Show Admin Menu:

```python
# In handle_bot_added_to_group or when bot is mentioned
if message.from_user:
    user_id = message.from_user.id
    group_id = message.chat.id
    
    # Check if user is registered AND admin
    is_registered = await is_user_registered(user_id)
    is_admin = await is_user_admin_in_group(bot, group_id, user_id)
    
    if is_registered and is_admin:
        # Send admin menu in DM (not in group!)
        admin_menu = create_group_admin_menu(group_id)
        await bot.send_message(
            user_id,
            f"👋 Hi! You're an admin in {group_title}.\n\n"
            f"Here are your group management controls:",
            reply_markup=admin_menu
        )
    elif is_admin and not is_registered:
        # Encourage admin to register
        deep_link = f"https://t.me/{bot_username}?start=admin_{abs(group_id)}"
        await bot.send_message(
            user_id,
            f"👋 Hi! You're an admin in {group_title}.\n\n"
            f"Complete your onboarding to unlock admin controls:\n"
            f"{deep_link}"
        )
```

### Admin Menu Handlers:

```python
# In handlers/group_admin.py (new file)

@router.callback_query(F.data.startswith("group_settings:"))
async def handle_group_settings(callback: CallbackQuery):
    """Handle group settings button."""
    group_id = int(callback.data.split(":")[1])
    # Show group settings menu
    ...

@router.callback_query(F.data.startswith("group_import:"))
async def handle_group_import(callback: CallbackQuery):
    """Handle history import button."""
    await callback.answer("📚 History import coming soon!", show_alert=True)

@router.callback_query(F.data.startswith("group_stats:"))
async def handle_group_stats(callback: CallbackQuery):
    """Show group statistics."""
    group_id = int(callback.data.split(":")[1])
    # Fetch and display stats
    ...

@router.callback_query(F.data.startswith("group_threads:"))
async def handle_group_threads(callback: CallbackQuery):
    """Manage group-linked threads."""
    group_id = int(callback.data.split(":")[1])
    # Show thread management UI
    ...
```

### Files to Create:
- `luka_bot/handlers/group_admin.py` - Admin control handlers
- `luka_bot/keyboards/group_admin.py` - Admin menu keyboards

### Files to Modify:
- `luka_bot/handlers/group_messages.py` - Add admin detection
- `luka_bot/handlers/__init__.py` - Register new router

## 📋 Phase 3: Command Scope Management

### Goal: Different commands for DMs, groups, and admins

### Current Commands (DM Only):
```python
# luka_bot/keyboards/default_commands.py
commands_by_language = {
    "en": {
        "start": "Main menu with Quick Actions",
        "chat": "Manage conversation threads",
        "search": "Search knowledge bases",
        "tasks": "Task management (GTD)",
        "groups": "Manage group integrations",
        "profile": "User profile and settings",
        "reset": "Clear all data and start fresh",
    }
}
```

### Proposed Command Structure:

#### DM Commands (Private Chats):
```python
private_commands = {
    "en": {
        "start": "Main menu with Quick Actions",
        "chat": "Manage conversation threads",
        "search": "Search knowledge bases",
        "tasks": "Task management (GTD)",
        "groups": "Manage group integrations",
        "profile": "User profile and settings",
        "reset": "Clear all data and start fresh",
        "help": "Help and documentation",
    }
}
```

#### Group Commands (All Members):
```python
group_commands = {
    "en": {
        "help": "Learn how to use me",
        "stats": "Group statistics and usage",
    }
}
```

#### Group Admin Commands:
```python
admin_commands = {
    "en": {
        "help": "Learn how to use me",
        "stats": "Group statistics and usage",
        "settings": "Configure bot for this group",
        "import": "Import group history",
    }
}
```

### Implementation:

```python
# luka_bot/keyboards/default_commands.py

from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
)

async def set_default_commands(bot: Bot) -> None:
    """Set commands for different scopes."""
    
    # Remove old commands
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    
    for language_code in ["en", "ru"]:
        # Private chat commands (all features)
        await bot.set_my_commands(
            [BotCommand(command=cmd, description=desc)
             for cmd, desc in private_commands[language_code].items()],
            scope=BotCommandScopeAllPrivateChats(),
            language_code=language_code,
        )
        logger.info(f"✅ Set private commands for {language_code}")
        
        # Group commands (limited, discovery-focused)
        await bot.set_my_commands(
            [BotCommand(command=cmd, description=desc)
             for cmd, desc in group_commands[language_code].items()],
            scope=BotCommandScopeAllGroupChats(),
            language_code=language_code,
        )
        logger.info(f"✅ Set group commands for {language_code}")
        
        # Group admin commands (includes management)
        await bot.set_my_commands(
            [BotCommand(command=cmd, description=desc)
             for cmd, desc in admin_commands[language_code].items()],
            scope=BotCommandScopeAllChatAdministrators(),
            language_code=language_code,
        )
        logger.info(f"✅ Set admin commands for {language_code}")
```

### Group Command Handlers:

```python
# In handlers/group_commands.py (new file)

@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]), Command("help"))
async def handle_help_in_group(message: Message):
    """Handle /help command in groups."""
    bot_username = (await message.bot.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start=help"
    
    await message.answer(
        f"👋 Hi! I'm {settings.LUKA_NAME}.\n\n"
        f"🤖 <b>In groups, I can:</b>\n"
        f"• Answer questions when you mention me (@{bot_username})\n"
        f"• Index conversations for searchability\n"
        f"• Help organize group knowledge\n\n"
        f"💬 <b>For full features, start a private chat:</b>\n"
        f"{deep_link}\n\n"
        f"📚 There you can search this group's history, manage threads, and more!",
        parse_mode="HTML"
    )

@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]), Command("stats"))
async def handle_stats_in_group(message: Message):
    """Handle /stats command in groups."""
    group_id = message.chat.id
    group_service = await get_group_service()
    kb_index = await group_service.get_group_kb_index(group_id)
    
    if not kb_index:
        await message.answer("⚠️ Bot not fully set up in this group yet.")
        return
    
    # Fetch stats from Elasticsearch
    # ... show message count, active members, etc.
    await message.answer("📊 <b>Group Statistics</b>\n\n...", parse_mode="HTML")

@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]), Command("settings"))
async def handle_settings_in_group(message: Message):
    """Handle /settings command in groups (admin only)."""
    if not message.from_user:
        return
    
    user_id = message.from_user.id
    group_id = message.chat.id
    
    # Check if admin
    is_admin = await is_user_admin_in_group(message.bot, group_id, user_id)
    
    if not is_admin:
        await message.answer("⚠️ This command is only available to group admins.")
        return
    
    # Send settings menu in DM
    await message.bot.send_message(
        user_id,
        "⚙️ Group settings menu:",
        reply_markup=create_group_admin_menu(group_id)
    )
    await message.answer("✅ Sent settings to your DM!")
```

### Files to Create:
- `luka_bot/handlers/group_commands.py` - Group command handlers
- `luka_bot/utils/permissions.py` - Helper functions for permission checks

### Files to Modify:
- `luka_bot/keyboards/default_commands.py` - Multi-scope command setup
- `luka_bot/handlers/__init__.py` - Register group_commands router

## 🔗 Phase 4: Deep Link & Onboarding Flow

### Goal: Seamless group → DM onboarding

### Deep Link Strategy:

**Format:** `https://t.me/{bot_username}?start={payload}`

**Payloads:**
- `group_{group_id}` - User came from a specific group
- `admin_{group_id}` - Admin came from group
- `topic_{group_id}_{topic_id}` - User came from specific topic

### Start Command Handler Enhancement:

```python
# In handlers/start.py

@router.message(Command("start"))
async def handle_start(message: Message, command: CommandObject):
    """Handle /start command with deep link support."""
    user_id = message.from_user.id
    
    # Parse deep link payload
    payload = command.args if command.args else None
    
    # Check if user is registered
    profile_service = get_user_profile_service()
    profile = await profile_service.get_profile(user_id)
    
    if payload and payload.startswith("group_"):
        # User came from group
        group_id = int(payload.replace("group_", ""))
        
        if not profile:
            # New user - show onboarding with group context
            await message.answer(
                f"👋 Welcome! I see you came from a group.\n\n"
                f"Let's get you set up (takes ~30 seconds)...",
            )
            # Start onboarding flow
            # ... show language selection, etc.
        else:
            # Existing user - show group integration
            await message.answer(
                f"👋 Welcome back!\n\n"
                f"Would you like to enable features for the group you came from?",
            )
            # Show group integration options
    
    elif payload and payload.startswith("admin_"):
        # Admin user came from group
        group_id = int(payload.replace("admin_", ""))
        
        if not profile:
            # Admin needs to register first
            await message.answer(
                f"👋 Welcome, Admin!\n\n"
                f"Complete quick setup to unlock admin controls...",
            )
            # Start admin onboarding
        else:
            # Show admin controls immediately
            await message.answer(
                f"👋 Welcome back, Admin!",
                reply_markup=create_group_admin_menu(group_id)
            )
    
    else:
        # Normal start (no payload)
        if not profile:
            # New user - standard onboarding
            await show_quick_actions(message)
        else:
            # Existing user - main menu
            await show_quick_actions(message)
```

### Post-Onboarding Actions:

```python
# After user completes onboarding via deep link from group

if user_came_from_group:
    # Send success message
    await message.answer(
        f"✅ <b>Setup Complete!</b>\n\n"
        f"You can now:\n"
        f"• 🔍 Search the group's history using /search\n"
        f"• 💬 Ask me questions in DM\n"
        f"• 🤖 Mention me in the group for help\n\n"
        f"Try it now: Use /search and select the group!",
        parse_mode="HTML"
    )
    
    # If admin, show admin controls
    if is_admin:
        await message.answer(
            "🎉 <b>Admin Bonus!</b>\n\n"
            "You have access to group management:",
            reply_markup=create_group_admin_menu(group_id),
            parse_mode="HTML"
        )
```

## 📦 Implementation Priority

### High Priority (Week 1):
- [x] Add bot personality to welcome messages (Phase 1)
- [x] Add deep links to welcome messages (Phase 1)
- [x] Update LLM welcome prompt (Phase 1)
- [ ] Add "import history" encouragement (Phase 1)
- [ ] Implement admin detection (Phase 2)

### Medium Priority (Week 2):
- [ ] Create admin control menu (Phase 2)
- [ ] Implement admin menu handlers (Phase 2)
- [ ] Set up multi-scope commands (Phase 3)
- [ ] Create group command handlers (Phase 3)

### Low Priority (Week 3):
- [ ] Deep link onboarding flow (Phase 4)
- [ ] Post-onboarding group integration (Phase 4)
- [ ] Admin-specific onboarding path (Phase 4)

## 🎯 Success Metrics

**Onboarding Conversion:**
- % of group members who click deep link
- % who complete registration
- Time to complete onboarding

**Admin Engagement:**
- % of admins who use admin controls
- Most used admin features
- Settings changes per admin

**Command Usage:**
- Group command usage vs DM command usage
- Most popular commands in each scope
- Error rate (users trying wrong commands in wrong place)

## 🚀 Next Steps

1. **Review & approve** this roadmap
2. **Start with Phase 1** - Enhanced welcome messages
3. **Implement incrementally** - Test each phase
4. **Gather feedback** - From real group usage
5. **Iterate** - Based on user behavior

---

**Status:** Ready for implementation
**Estimated effort:** 3-4 days for full implementation
**Dependencies:** None (all self-contained)

