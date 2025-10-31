# Group Settings Enhancement Implementation

**Date**: October 2025  
**Feature**: User Default Group Settings & Enhanced Group Behavior Controls

---

## 📋 Overview

This implementation adds two-level group settings management:

1. **User-Level Defaults** (`/groups` → "Default Settings")  
   - Template for all new groups added by the user
   - Persisted in Redis with key: `user_default_group_settings:{user_id}`
   
2. **Per-Group Settings** (Admin menu in each group)  
   - Override user defaults for specific groups
   - New toggles: Silent Mode & AI Assistant

---

## 🏗️ Architecture Changes

### 1. Model Extension: `GroupSettings`

**File**: `luka_bot/models/group_settings.py`

#### New Fields Added:

```python
@dataclass
class GroupSettings:
    # ... existing fields ...
    
    # Identity
    is_user_default: bool = False  # True if this is a user template
    
    # Bot behavior
    silent_addition: bool = False  # Don't send welcome in group, send DM instead
    silent_mode: bool = False      # Suppress bot service messages in group
    ai_assistant_enabled: bool = True  # Enable/disable @mentions and replies
```

#### New Redis Key Format:

- **User defaults**: `user_default_group_settings:{user_id}`
- **Group settings**: `group_settings:{group_id}` (unchanged)
- **Topic settings**: `group_settings:{group_id}:topic_{topic_id}` (unchanged)

#### New Methods:

```python
# Static method for user default key
@staticmethod
def get_user_default_key(user_id: int) -> str:
    return f"user_default_group_settings:{user_id}"
```

---

### 2. Service Layer: `ModerationService`

**File**: `luka_bot/services/moderation_service.py`

#### New Methods Added:

```python
async def get_user_default_settings(user_id: int) -> Optional[GroupSettings]:
    """Get user's default template for new groups."""

async def get_or_create_user_default_settings(user_id: int) -> GroupSettings:
    """Get or create user defaults with sensible initial values."""

async def create_group_settings_from_user_defaults(
    group_id: int, 
    user_id: int, 
    created_by: int
) -> GroupSettings:
    """Create group settings by copying user's template."""
```

---

### 3. Silent Addition Flow

**File**: `luka_bot/utils/group_onboarding.py` (NEW)

#### Core Functionality:

```python
async def send_group_onboarding_to_dm(
    bot: Bot,
    user_id: int,
    group_id: int,
    group_title: str,
    welcome_text: str,
    inline_keyboard: InlineKeyboardMarkup,
    metadata: GroupMetadata,
    thread: Thread,
    language: str = "en"
) -> bool:
    """
    Sends welcome message + controls to user's DM when silent addition is enabled.
    Also adds onboarding context to user's /start thread for LLM awareness.
    """
```

#### Flow:

1. **User adds bot with `silent_addition=True`**
2. **Bot skips group welcome message**
3. **Sends DM to user** with:
   - Welcome message + group info
   - Full admin controls (inline keyboard)
   - Instructions on managing settings
4. **Adds to user's thread context** for LLM:
   ```
   [System: You added Luka to "{Group Name}" at {timestamp}. 
   Silent mode enabled - notifications sent here instead.]
   ```

---

### 4. Integration Points

#### A. Bot Addition Handler

**File**: `luka_bot/handlers/group_messages.py`  
**Function**: `handle_bot_added_to_group()`

**Changes**:
```python
# OLD: Always create default settings
group_settings = await moderation_service.create_default_group_settings(
    group_id=group_id,
    created_by=user_id
)

# NEW: Apply user's template
group_settings = await moderation_service.create_group_settings_from_user_defaults(
    group_id=group_id,
    user_id=user_id,
    created_by=user_id
)

# Check silent addition
if group_settings.silent_addition:
    # Send to DM
    dm_success = await send_group_onboarding_to_dm(...)
    if dm_success:
        logger.info(f"✅ Sent silent onboarding to user {user_id}")
    else:
        # Fallback: send in group anyway
        await event.answer(welcome_text, reply_markup=inline_keyboard, parse_mode="HTML")
else:
    # Normal flow: send in group
    await event.answer(welcome_text, reply_markup=inline_keyboard, parse_mode="HTML")
```

#### B. AI Assistant Check

**File**: `luka_bot/handlers/group_messages.py`  
**Function**: `handle_group_message()` (mention detection section)

**Changes**:
```python
# If mentioned OR replied to bot, generate LLM response
if is_mentioned or is_reply_to_bot:
    # NEW: Check if AI assistant is enabled
    group_settings = await moderation_service.get_group_settings(group_id)
    if group_settings and not group_settings.ai_assistant_enabled:
        logger.info(f"AI assistant disabled for group {group_id}, ignoring mention/reply")
        return
    
    # Continue with LLM response...
```

#### C. Group Admin Menu

**File**: `luka_bot/keyboards/group_admin.py`  
**Function**: `create_group_admin_menu()`

**New Parameters**:
```python
def create_group_admin_menu(
    group_id: int, 
    group_title: str = None,
    moderation_enabled: bool = True,
    stoplist_count: int = 0,
    current_language: str = "en",
    silent_mode: bool = False,          # NEW
    ai_assistant_enabled: bool = True   # NEW
) -> InlineKeyboardMarkup:
```

**New Buttons**:
```
Row 3 (Bot Behavior):
┌────────────────────────────────────┬────────────────────────────────────┐
│ 🔇 Silent Mode: OFF                │ 🤖 AI Assistant: ON                │
└────────────────────────────────────┴────────────────────────────────────┘
```

#### D. Toggle Handlers

**File**: `luka_bot/handlers/group_admin.py`

**New Handlers**:
```python
@router.callback_query(F.data.startswith("group_toggle_silent:"))
async def handle_toggle_silent_mode(callback: CallbackQuery):
    """Toggle silent mode for group (suppresses bot service messages)."""

@router.callback_query(F.data.startswith("group_toggle_ai:"))
async def handle_toggle_ai_assistant(callback: CallbackQuery):
    """Toggle AI assistant (enable/disable @mentions and replies)."""
```

---

### 5. User Defaults UI

**File**: `luka_bot/handlers/groups_enhanced.py`

#### A. Button in `/groups` Menu

Added before "Refresh/Close" buttons:
```
⚙️ Default Settings (EN) / ⚙️ Настройки по умолчанию (RU)
```

#### B. User Defaults Menu Handler

```python
@router.callback_query(F.data == "user_group_defaults")
async def handle_user_group_defaults(callback: CallbackQuery):
    """Show user's default group settings - comprehensive menu with ALL settings."""
```

**Menu Display**:
```
📋 Default Group Settings

These settings apply when you add me to a new group.

Bot Behavior:
• Welcome Message: Silent (DM)
• Silent Mode: ON
• AI Assistant: Enabled ✅

Moderation:
• Background Moderation: ON ✅
• Stoplist Filter: ON (5 words)
• Reputation System: ON ✅

You can change these for each group individually via /groups menu.

┌─────────────────────────────────────┐
│  📢 Welcome: Silent / Show          │
├─────────────────────────────────────┤
│  🔇 Silent: ON  │  🤖 AI: ON        │
├─────────────────────────────────────┤
│  🛡️ Moderation: ON ✅               │
├─────────────────────────────────────┤
│  ⭐ Reputation: ON ✅                │
├─────────────────────────────────────┤
│  🚫 Stoplist: ON (5 words)          │
├─────────────────────────────────────┤
│  ⚙️ Advanced Settings               │
├─────────────────────────────────────┤
│  ⬅️ Back to Groups                  │
└─────────────────────────────────────┘
```

#### C. Stoplist Submenu

```python
@router.callback_query(F.data == "user_default_stoplist")
async def handle_user_default_stoplist(callback: CallbackQuery):
    """Show stoplist configuration for user defaults."""
```

**Displays**:
- Stoplist enabled/disabled status
- Case sensitivity toggle
- Word count
- Note about full editing in group admin menu

**Toggles**:
- `stoplist_enabled`
- `stoplist_case_sensitive`

#### D. Advanced Settings Submenu

```python
@router.callback_query(F.data == "user_default_advanced")
async def handle_user_default_advanced(callback: CallbackQuery):
    """Show advanced content filters and thresholds."""
```

**Displays**:
- Content Filters (links, images, videos, stickers, forwarded)
- Service message deletion
- Moderation thresholds (auto-delete, auto-warn, quality)

**Toggles**:
- All 6 content filter types
- Service message deletion

#### C. Toggle Handler

```python
@router.callback_query(F.data.startswith("toggle_user_default:"))
async def handle_toggle_user_default(callback: CallbackQuery):
    """Toggle user default setting (silent_addition or ai_assistant)."""
```

---

## 🌐 Internationalization (i18n)

**Files**: 
- `luka_bot/locales/en/LC_MESSAGES/messages.po`
- `luka_bot/locales/ru/LC_MESSAGES/messages.po`

### New Translation Keys Added:

#### User Defaults Section:
```
user_group_defaults.title
user_group_defaults.intro
user_group_defaults.current_values
user_group_defaults.silent_addition
user_group_defaults.silent_addition_on
user_group_defaults.silent_addition_off
user_group_defaults.ai_assistant
user_group_defaults.ai_enabled
user_group_defaults.ai_disabled
user_group_defaults.hint
user_group_defaults.btn_back
```

#### Group Settings Section:
```
group_settings.silent_mode
group_settings.silent_on
group_settings.silent_off
group_settings.ai_assistant
group_settings.ai_enabled
group_settings.ai_disabled
group_settings.ai_disabled_notice (optional, for when user mentions disabled bot)
```

#### Group Onboarding Section:
```
group_onboarding.title
group_onboarding.intro
group_onboarding.controls_hint
group_onboarding.find_settings_hint
```

---

## 🔄 User Flows

### Flow 1: User Sets Defaults Before Adding Bot

```
1. User opens /groups
2. Clicks "⚙️ Default Settings"
3. Toggles "Silent Addition" → ON
4. Toggles "AI Assistant" → ON (or OFF)
5. Adds bot to new group
   → Bot created group settings from user template
   → Sends welcome DM to user
   → Adds context to user's /start thread
   → No message in group
```

### Flow 2: User Adds Bot Without Setting Defaults

```
1. User adds bot to group (no defaults set)
2. Bot detects no user defaults
3. Creates default template automatically with:
   - silent_addition: False (show in group)
   - ai_assistant_enabled: True
4. Applies template to new group
5. Sends normal welcome in group
```

### Flow 3: User Toggles Group Settings After Addition

```
1. User opens group admin menu
2. Sees new row: "🔇 Silent Mode: OFF | 🤖 AI Assistant: ON"
3. Clicks "🔇 Silent Mode"
   → Toggles to ON
   → Future bot service messages suppressed
4. Clicks "🤖 AI Assistant"
   → Toggles to OFF
   → Bot ignores @mentions and replies
```

### Flow 4: AI Assistant Disabled

```
1. Admin disables AI Assistant in group settings
2. User @mentions bot in group
3. Bot detects ai_assistant_enabled=False
4. Logs: "AI assistant disabled for group {group_id}, ignoring mention/reply"
5. Bot does not respond
6. (Optional) Sends notice: "AI Assistant is disabled in this group"
```

---

## 🧪 Testing Checklist

### Model & Service Layer:
- [ ] **Test 1**: GroupSettings serialization with new fields (user-default mode)
- [ ] **Test 2**: GroupSettings serialization with new fields (group mode)
- [ ] **Test 3**: Create user defaults via `get_or_create_user_default_settings()`
- [ ] **Test 4**: Verify Redis key format: `user_default_group_settings:{user_id}`
- [ ] **Test 5**: Apply template via `create_group_settings_from_user_defaults()`
- [ ] **Test 6**: Verify group inherits correct values from template

### Silent Addition Flow:
- [ ] **Test 7**: Enable silent addition in user defaults
- [ ] **Test 8**: Add bot to group
- [ ] **Test 9**: Verify DM sent to user with controls
- [ ] **Test 10**: Verify no welcome message in group
- [ ] **Test 11**: Verify context added to /start thread
- [ ] **Test 12**: Check LLM can see onboarding in thread context

### Normal Addition Flow:
- [ ] **Test 13**: Disable silent addition in user defaults
- [ ] **Test 14**: Add bot to group
- [ ] **Test 15**: Verify welcome message sent in group
- [ ] **Test 16**: Verify no DM sent to user

### AI Assistant Toggle:
- [ ] **Test 17**: Disable AI Assistant in group settings
- [ ] **Test 18**: @mention bot in group
- [ ] **Test 19**: Verify bot does not respond
- [ ] **Test 20**: Enable AI Assistant again
- [ ] **Test 21**: @mention bot
- [ ] **Test 22**: Verify bot responds normally

### Silent Mode Toggle:
- [ ] **Test 23**: Enable Silent Mode in group settings
- [ ] **Test 24**: Trigger bot service message (e.g., moderation action)
- [ ] **Test 25**: Verify message is suppressed (implementation TBD)

### User Defaults UI:
- [ ] **Test 26**: Open /groups → "Default Settings"
- [ ] **Test 27**: Toggle Silent Addition
- [ ] **Test 28**: Verify persistence (close & reopen)
- [ ] **Test 29**: Toggle AI Assistant
- [ ] **Test 30**: Verify both settings persist across sessions

### Group Settings UI:
- [ ] **Test 31**: Open group admin menu
- [ ] **Test 32**: Verify Silent Mode button appears
- [ ] **Test 33**: Verify AI Assistant button appears
- [ ] **Test 34**: Toggle both settings
- [ ] **Test 35**: Verify menu refreshes with new values

### Internationalization:
- [ ] **Test 36**: User Defaults UI in English
- [ ] **Test 37**: User Defaults UI in Russian
- [ ] **Test 38**: Group Settings UI in English
- [ ] **Test 39**: Group Settings UI in Russian
- [ ] **Test 40**: Group Onboarding DM in English
- [ ] **Test 41**: Group Onboarding DM in Russian

### Admin Permissions:
- [ ] **Test 42**: Non-admin tries to toggle group settings
- [ ] **Test 43**: Verify "🔒 Admin only" error

### Edge Cases:
- [ ] **Test 44**: User has no defaults, adds bot → default template created
- [ ] **Test 45**: Silent addition enabled, but user blocked bot → fallback to group message
- [ ] **Test 46**: Existing groups without new fields → verify default values applied
- [ ] **Test 47**: Bot added by non-admin → verify graceful handling

---

## 📂 Files Modified

### Core Model & Service:
1. ✅ `luka_bot/models/group_settings.py` - Extended with 4 new fields
2. ✅ `luka_bot/services/moderation_service.py` - Added 3 new methods

### New Utility:
3. ✅ `luka_bot/utils/group_onboarding.py` - Silent addition DM flow

### Handlers:
4. ✅ `luka_bot/handlers/group_messages.py` - Bot addition & AI check
5. ✅ `luka_bot/handlers/group_admin.py` - Toggle handlers & menu update
6. ✅ `luka_bot/handlers/groups_enhanced.py` - User defaults UI

### UI Components:
7. ✅ `luka_bot/keyboards/group_admin.py` - New buttons & parameters

### Internationalization:
8. ✅ `luka_bot/locales/en/LC_MESSAGES/messages.po` - 20+ new keys
9. ✅ `luka_bot/locales/ru/LC_MESSAGES/messages.po` - 20+ new keys

---

## 🔍 Code Review Notes

### Design Decisions:

1. **Why reuse `GroupSettings` instead of creating `UserPreferences`?**
   - Avoids code duplication
   - Single source of truth for settings schema
   - Easy template application (copy all fields)
   - Unified serialization logic

2. **Why store user defaults in Redis with special ID?**
   - Consistent with existing pattern
   - Same TTL and eviction policy
   - No schema migration needed
   - Easy to query and update

3. **Why add context to /start thread for silent addition?**
   - Makes LLM aware of group additions
   - Enables future tool-based settings management
   - Provides user with conversational access to settings

4. **Why fallback to group message if DM fails?**
   - Better UX than complete failure
   - User still gets controls (can click in group)
   - Graceful degradation

### Future Enhancements:

1. **LLM Tools for Settings Management** (mentioned by user)
   - Add tools for reading/updating group settings
   - Enable conversational interface: "Disable AI in MyGroup"
   - Thread context awareness already prepared

2. **Silent Mode Implementation**
   - Currently toggles exist but enforcement is TBD
   - Need to identify all "bot service messages"
   - Add check before sending those messages

3. **Notification Settings**
   - Extend with more granular controls
   - Per-message-type notifications
   - DM vs. group preferences

4. **Bulk Settings Management**
   - Apply user defaults to all existing groups
   - Batch operations via /groups menu

---

## 🚀 Deployment Checklist

Before deploying to production:

1. ✅ All files have no linter errors
2. ✅ i18n keys compiled (`msgfmt`)
3. ⚠️ Manual testing completed (see Testing Checklist above)
4. ⚠️ Redis migration plan (existing groups get default values)
5. ⚠️ Rollback plan if issues arise
6. ⚠️ Monitor logs for DM failures during silent addition
7. ⚠️ User documentation updated

---

## 📞 Support & Maintenance

### Common Issues:

**Issue**: User complains they didn't get welcome message  
**Solution**: Check if silent_addition=True, verify DM was sent, check if user blocked bot

**Issue**: Bot not responding to @mentions  
**Solution**: Check if ai_assistant_enabled=False in group settings

**Issue**: Existing groups showing wrong settings  
**Solution**: GroupSettings.from_dict() provides defaults for missing fields

### Monitoring:

**Key Metrics to Track**:
- % of users using silent addition
- % of groups with AI assistant disabled
- DM failure rate during silent addition
- User defaults usage rate

**Log Grep Patterns**:
```bash
# Silent addition flows
grep "Created group settings from user defaults" bot.log

# DM successes/failures
grep "Sent silent onboarding to user" bot.log
grep "Failed to send onboarding DM" bot.log

# AI assistant disabled events
grep "AI assistant disabled for group" bot.log
```

---

## 📚 References

- Original planning document: `GROUPS_MENU_SETTINGS_UPDATE.md` (if exists)
- Related: `luka_bot/models/thread.py` - Thread context structure
- Related: `luka_bot/services/group_service.py` - Group metadata management
- Related: `luka_bot/handlers/start.py` - User /start thread management

---

**Implementation Status**: ✅ **COMPLETE**  
**Linter Errors**: ✅ **NONE**  
**Ready for Testing**: ✅ **YES**

