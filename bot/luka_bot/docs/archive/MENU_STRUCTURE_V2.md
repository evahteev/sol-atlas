# Group Admin Menu Structure V2 - Ultra-Flat Design

## Overview
This document describes the **maximally flattened** group admin menu structure focused on moderation and content filtering controls. The new design eliminates complex nested menus in favor of a single-level interface where all primary controls are immediately accessible.

## Design Philosophy
- **Flat is better**: Maximum 2 levels (Main Menu → Submenu → Done)
- **One-click actions**: Toggles update immediately with visual feedback
- **Smart button states**: Buttons show current state (✅/❌, counts, language)
- **Focused on moderation**: Primary controls for content filtering, not general settings

## Menu Hierarchy

### Main Menu (DM)
**Title**: 🛡️ Group Moderation & Filters

```
┌────────────────────────────────────┐
│   🛡️ Group Moderation & Filters    │
├────────────────────────────────────┤
│                                    │
│  [🇬🇧 Language: English]           │
│                                    │
│  [🛡️ Moderation: ✅ Enabled]      │
│                                    │
│  [🗑️ System Messages]              │
│                                    │
│  [🚫 Stoplist (5 words)]           │
│                                    │
│  [⏰ Scheduled Content]             │
│                                    │
├────────────────────────────────────┤
│      [📊 Stats]    [❌ Close]      │
└────────────────────────────────────┘
```

**Access Points**:
- In-group inline settings button "⚙️ Settings"
- `/settings` command in group
- `/moderation` command in group
- Deep link from admin onboarding

**Button States** (Dynamic):
- Language shows current flag and name (🇬🇧 English / 🇷🇺 Русский)
- Moderation shows toggle state (✅ Enabled / ❌ Disabled)
- Stoplist shows word count ((5 words) / (Empty))

### Level 2 Menus

#### 1. Language Submenu
```
┌────────────────────────────────────┐
│   🌐 Select Language                │
├────────────────────────────────────┤
│                                    │
│         [🇬🇧 English]              │
│                                    │
│         [🇷🇺 Русский]              │
│                                    │
│         [🔙 Back]                  │
└────────────────────────────────────┘
```

**Behavior**:
- Click → Language updates → Menu regenerates in new language
- LLM generates personalized welcome in the new language
- Sent to group as confirmation

**Callback**: `group_set_lang:{group_id}:{language}`

#### 2. System Messages Submenu
```
┌────────────────────────────────────┐
│   🗑️ System Messages Filter        │
├────────────────────────────────────┤
│                                    │
│ Select types to auto-delete:      │
│                                    │
│  [✅ User joined/left]             │
│  [✅ Name/title changes]           │
│  [❌ Pinned messages]              │
│  [❌ Voice chat events]            │
│  [❌ Group/photo changed]          │
│                                    │
│         [🔙 Back]                  │
└────────────────────────────────────┘
```

**Behavior**:
- Each button toggles independently
- Checkmarks update immediately (✅ ↔ ❌)
- Settings persist to `GroupSettings.service_message_types`
- `delete_service_messages` auto-enabled if any type is active

**Callback**: `sys_msg_toggle:{type}:{group_id}`

**Type Mapping**:
```python
type_groups = {
    "joined": ["new_chat_members", "left_chat_member"],
    "title": ["new_chat_title"],
    "pinned": ["pinned_message"],
    "voice": ["voice_chat_started", "voice_chat_ended", "voice_chat_scheduled"],
    "photo": ["new_chat_photo", "delete_chat_photo"]
}
```

#### 3. Stoplist Submenu
```
┌────────────────────────────────────┐
│   🚫 Stoplist (5 words)            │
├────────────────────────────────────┤
│                                    │
│ Current stoplist:                  │
│ spam, scam, phishing, porn, drugs  │
│                                    │
│ Messages containing these words    │
│ are automatically deleted.         │
│                                    │
│  [✏️ Edit List]  [🗑️ Clear All]   │
│         [🔙 Back]                  │
└────────────────────────────────────┘
```

**Behavior**:
- **Edit List** → Opens FSM conversation to input comma-separated words
- **Clear All** → Immediate confirmation → Clears stoplist
- Parent button updates with count after edit

**FSM Flow** (Edit):
1. User clicks "✏️ Edit List"
2. Bot prompts for comma-separated words
3. User sends: `spam, scam, phishing`
4. Bot validates and saves
5. Confirmation shows preview
6. Menu button updates to `🚫 Stoplist (3 words)`

**Callback**: 
- `group_stoplist_edit:{group_id}` (starts FSM)
- `group_stoplist_clear:{group_id}` (clears)

**Data Model**: `GroupSettings.stoplist_words`, `stoplist_enabled`

#### 4. Scheduled Content Submenu
```
┌────────────────────────────────────┐
│   ⏰ Scheduled Content              │
├────────────────────────────────────┤
│                                    │
│      🚧 Coming Soon! 🚧            │
│                                    │
│ This feature will allow:           │
│ • Schedule announcements           │
│ • Auto-post reminders              │
│ • Recurring messages               │
│ • Content calendar                 │
│                                    │
│         [🔙 Back]                  │
└────────────────────────────────────┘
```

**Behavior**:
- Placeholder for future feature
- Returns to main menu

**Callback**: `scheduled_content:{group_id}`

## Data Flow

### Models

#### Thread (Unified Configuration)
```python
class Thread:
    thread_id: str
    thread_type: str  # "dm", "group", "topic"
    owner_id: int
    group_id: Optional[int]
    name: str
    language: str  # "en" or "ru"
    knowledge_bases: List[str]
    agent_name: Optional[str]
    # ...other fields
```

#### GroupSettings (Moderation)
```python
class GroupSettings:
    group_id: int
    moderation_enabled: bool
    stoplist_words: List[str]
    stoplist_enabled: bool
    service_message_types: List[str]  # ["new_chat_members", "pinned_message", ...]
    delete_service_messages: bool
    # ...other fields
```

### State Persistence

**Menu Button States** are fetched dynamically on menu render:
```python
# Fetch current state
moderation_service = await get_moderation_service()
group_service = await get_group_service()
thread_service = get_thread_service()

settings = await moderation_service.get_group_settings(group_id)
thread = await thread_service.get_group_thread(group_id)

# Extract dynamic values
moderation_enabled = settings.moderation_enabled if settings else True
stoplist_count = len(settings.stoplist_words) if settings else 0
current_language = thread.language if thread else "en"

# Create menu with current state
menu = create_group_admin_menu(
    group_id, 
    group_title,
    moderation_enabled,
    stoplist_count,
    current_language
)
```

## Implementation Details

### File Structure
```
luka_bot/
├── keyboards/
│   └── group_admin.py              # create_group_admin_menu, create_system_messages_menu
└── handlers/
    ├── group_admin.py              # Main menu handlers, back navigation
    ├── group_settings_inline.py    # Inline settings (language, moderation toggle)
    └── group_commands.py           # /settings, /moderation commands
```

### Key Functions

#### `create_group_admin_menu()`
```python
def create_group_admin_menu(
    group_id: int, 
    group_title: str = None,
    moderation_enabled: bool = True,
    stoplist_count: int = 0,
    current_language: str = "en"
) -> InlineKeyboardMarkup
```

**Generates dynamic button text**:
- `🇬🇧 Language: English` or `🇷🇺 Language: Русский`
- `🛡️ Moderation: ✅ Enabled` or `🛡️ Moderation: ❌ Disabled`
- `🚫 Stoplist (5 words)` or `🚫 Stoplist (Empty)`

#### `create_system_messages_menu()`
```python
def create_system_messages_menu(
    group_id: int, 
    enabled_types: list[str]
) -> InlineKeyboardMarkup
```

**Generates checkmarks** based on `enabled_types`:
- `✅ User joined/left` if any of `["new_chat_members", "left_chat_member"]` in enabled_types
- `❌ User joined/left` otherwise

### Handler Logic

#### Moderation Toggle (`group_toggle_mod`)
1. Check admin
2. Toggle `moderation_enabled`
3. Save settings
4. Detect context (DM admin menu vs. in-group inline)
5. Refresh appropriate keyboard
6. Show toast notification

#### Stoplist Edit (FSM)
1. User clicks "✏️ Edit List"
2. Handler sets FSM state `StoplistEditForm.waiting_for_words`
3. User sends message with words
4. Handler parses comma-separated list
5. Updates `GroupSettings.stoplist_words` and `stoplist_enabled`
6. Clears FSM
7. Shows confirmation with word count

#### Back Navigation
All submenus have "🔙 Back" button that calls:
```python
callback_data=f"group_admin_menu:{group_id}"
```

This handler:
1. Fetches fresh dynamic state
2. Regenerates main menu with current values
3. Edits message

## User Experience

### Admin Workflow (Typical)

1. **Bot added to group** → Auto-sends welcome with inline "⚙️ Settings" button
2. **Admin clicks "⚙️ Settings"** → Bot sends full admin menu to DM
3. **Admin clicks "🛡️ Moderation: ❌ Disabled"** → Toggles to ✅, button updates
4. **Admin clicks "🗑️ System Messages"** → Opens submenu with 5 toggle buttons
5. **Admin clicks "✅ User joined/left"** → Disables (changes to ❌), checkmark updates
6. **Admin clicks "🔙 Back"** → Returns to main menu (all states preserved)
7. **Admin clicks "🚫 Stoplist (Empty)"** → Opens stoplist submenu
8. **Admin clicks "✏️ Edit List"** → FSM conversation starts
9. **Admin sends**: `spam, scam, porn`
10. **Bot confirms**: `✅ Stoplist updated! Total words: 3`
11. **Menu button updates**: `🚫 Stoplist (3 words)`

### Speed & Efficiency
- **0 clicks**: View current state (all info on main menu buttons)
- **1 click**: Toggle moderation, open submenus
- **2 clicks**: Toggle system message filters, access language/stoplist
- **Max 3 clicks + input**: Edit stoplist with FSM

## Migration from Old Structure

### What Changed
**Before** (Complex nested structure):
```
Admin Menu
├── Import History
├── Group Stats
├── Moderation Settings ───> Submenu with many options
│   ├── Enable/Disable
│   ├── Templates
│   ├── Thresholds
│   └── Back
├── Configure Stoplist ────> Separate submenu
└── System Messages Filter ─> Separate submenu
```

**After** (Flat structure):
```
Admin Menu
├── Language (inline submenu)
├── Moderation (instant toggle)
├── System Messages (submenu with toggles)
├── Stoplist (submenu with FSM)
├── Scheduled Content (coming soon)
└── Stats (read-only info)
```

### Benefits
1. **Fewer levels**: No more nested moderation settings hub
2. **Immediate feedback**: Buttons show current state without navigation
3. **Faster actions**: Toggles work inline without submenus
4. **Focused**: Only moderation & filtering, not general settings
5. **Consistent**: All commands (`/settings`, `/moderation`) lead to same unified menu

## Testing Checklist

### Manual Testing
- [ ] Moderation toggle updates button text immediately (✅ ↔ ❌)
- [ ] Stoplist count updates in button text after FSM edit
- [ ] System message toggles persist to `GroupSettings.service_message_types`
- [ ] Language change regenerates menu in new language
- [ ] Scheduled content shows placeholder and returns to menu
- [ ] Back buttons work correctly at all levels
- [ ] Button states reflect actual database values
- [ ] Multiple admins see consistent state
- [ ] FSM cancellation (`/cancel`) works
- [ ] Error handling for invalid stoplist input

### Integration Points
- In-group inline settings button
- `/settings` command
- `/moderation` command
- Deep link onboarding (`?start=admin_{group_id}`)
- `/groups` command in DM (shows same menu when clicking group name)

## Future Enhancements

### Planned
- **Scheduled Content**: Full implementation with calendar UI
- **Advanced Filters**: Regex patterns, link detection toggles
- **Moderation Templates**: Pre-configured rulesets for different group types
- **Analytics Dashboard**: Message stats, violation trends, user reputation leaderboard

### Considered
- **Inline moderation toggle in group**: Instead of redirecting to DM
- **Quick stats badge**: Show violation count on main menu
- **Bulk actions**: Export/import stoplist, copy settings between groups

## Related Documentation
- `THREAD_ARCHITECTURE.md` - Unified Thread model design
- `GROUP_ONBOARDING_ROADMAP.md` - Group initialization and admin controls
- `MODERATION_ARCHITECTURE_V2.md` - Background moderation system
- `GROUP_RESET_FEATURE.md` - /reset command and data deletion

