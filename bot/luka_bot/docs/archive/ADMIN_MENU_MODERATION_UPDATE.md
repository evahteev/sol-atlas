# Admin Menu Moderation Update - October 12, 2025

## Overview

Updated the DM admin control menu to focus on moderation configuration instead of general group management features.

---

## Changes Summary

### ❌ Removed Buttons
1. **⚙️ Group Settings** - Redundant with inline group settings
2. **🔗 Manage Threads** - Not yet implemented
3. **🔍 Search Group KB** - Can use `/search` command instead

### ✅ Added Buttons
1. **🛡️ Moderation Settings** - Main moderation configuration hub
2. **🚫 Configure Stoplist** - Manage banned words list
3. **🗑️ System Messages Filter** - Control which system messages to auto-delete

---

## New Admin Menu Structure

```
┌─────────────────────────────┐
│   👋 Admin Controls         │
├─────────────────────────────┤
│ 📚 Import    │ 📊 Stats     │
├─────────────────────────────┤
│   🛡️ Moderation Settings    │
├─────────────────────────────┤
│   🚫 Configure Stoplist     │
├─────────────────────────────┤
│   🗑️ System Messages Filter │
├─────────────────────────────┤
│        ❌ Close              │
└─────────────────────────────┘
```

---

## Feature Details

### 1. 🛡️ Moderation Settings

**Purpose**: Central hub for all moderation configuration

**Shows**:
- ✅/❌ Moderation Status
- Auto-delete violations toggle
- DM notification toggle
- Public achievements toggle
- Reputation system toggle

**Sub-menus**:
- 📋 Filters (stoplist, links, patterns)
- 🤖 Moderation (prompts, thresholds)
- 🏆 Reputation (points, auto-ban, achievements)
- 🔔 Notifications (DM alerts, public announcements)
- 📊 Leaderboard (top contributors/violators)
- 📝 Templates (pre-configured rulesets)

**Navigation**: Back button to admin menu

---

### 2. 🚫 Configure Stoplist

**Purpose**: Manage banned words that trigger auto-deletion

**Display**:
```
🚫 Stoplist Configuration

Current stoplist (15 words):
spam, scam, phishing, ... (+5 more)

Messages containing these words will be 
automatically deleted.

💡 Click 'Edit Stoplist' to modify
```

**Actions**:
- **✏️ Edit Stoplist** - Interactive editor (FSM-based)
- **🗑️ Clear Stoplist** - Removes all words with confirmation

**Interactive Editor**:
When you click "✏️ Edit Stoplist":
1. Bot prompts you to send the words
2. You reply: `spam, scam, phishing`
3. Bot confirms with preview
4. Send `/cancel` to abort

**Features**:
- ✅ Comma-separated word list
- ✅ Case-insensitive matching
- ✅ Preview shows first 10 words
- ✅ Admin-only access
- ✅ FSM-based conversation flow
- ✅ Instant update with confirmation

---

### 3. 🗑️ System Messages Filter

**Purpose**: Configure which Telegram system messages to auto-delete

**Message Types** (Coming Soon):
- 👤 **User joined/left** - Member join/leave notifications
- 📝 **Name/title changes** - Username/group name updates
- 📌 **Pinned messages** - "X pinned Y message" notifications
- 🎉 **Group created** - Group creation notice

**Current State**:
- All service messages detected by moderation
- Individual toggles coming soon
- Integrated with existing content filtering

**Future Enhancement**:
Each button will toggle individual system message type filtering.

---

## Implementation Details

### File Changes

#### 1. `/luka_bot/keyboards/group_admin.py`
- Removed 3 buttons (Settings, Threads, Search)
- Added 3 moderation-focused buttons
- Restructured layout for better flow

#### 2. `/luka_bot/handlers/group_admin.py`
- Added `StoplistEditForm` FSM states class
- Added `handle_moderation_config()` callback
- Added `handle_stoplist_config()` callback
- Added `handle_system_msg_config()` callback
- Added `handle_stoplist_edit()` callback (FSM-based)
- Added `handle_stoplist_words_input()` message handler
- Added `handle_stoplist_clear()` callback

---

## Usage Flow

### Setting up Stoplist

**Step 1**: Admin accesses admin menu
- From group: Click "⚙️ Settings" in welcome message → Sent to DM
- From DM: Use `/groups` command → Select group

**Step 2**: Click "🚫 Configure Stoplist"
- Shows current stoplist
- Displays count and preview

**Step 3**: Click "✏️ Edit Stoplist"
- Bot prompts: "Please send me the words..."
- Bot shows example format

**Step 4**: Reply with words
```
spam, scam, phishing, porn, drugs
```

**Step 5**: Confirmation
```
✅ Stoplist updated!

Total words: 5
Preview: spam, scam, phishing, porn, drugs

Messages containing these words will be 
automatically deleted.
```

**Cancel**: Send `/cancel` at any time to abort

---

## Technical Notes

### Stoplist Storage
- Stored in `GroupSettings.stoplist` (list of strings)
- Persisted in Redis
- Case-insensitive matching
- Real-time updates

### FSM (Finite State Machine)
Stoplist editing uses aiogram FSM:
```python
class StoplistEditForm(StatesGroup):
    waiting_for_words = State()
    group_id = State()
```

**Flow**:
1. User clicks "Edit" → FSM state set
2. Bot waits for text message
3. User sends words → FSM processes
4. FSM clears after confirmation/cancel

### Admin Verification
All handlers check:
```python
is_admin = await is_user_admin_in_group(
    callback.bot, 
    group_id, 
    callback.from_user.id
)
```

### Integration Points
1. **Moderation Service** - Reads stoplist for content filtering
2. **Content Detection** - `check_stoplist()` utility
3. **Background Tasks** - V2 moderation uses stoplist
4. **GroupSettings** - Persistent storage
5. **FSM Storage** - aiogram's built-in FSM for conversation state

---

## Security

### Admin-Only Access
✅ All handlers verify admin status  
✅ Non-admins see "🔒 Admin only" toast  
✅ Command permissions checked per-group

### Input Validation
✅ Group ID stored in FSM state  
✅ Word list sanitization (trim, lowercase)  
✅ Empty list rejection  
✅ FSM session expiry handling  
✅ `/cancel` command support

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Basic stoplist management
- ✅ System message detection
- ✅ Moderation settings overview

### Phase 2 (Next)
- ⏳ Individual system message toggles
- ⏳ Regex pattern editor
- ⏳ Link whitelist/blacklist
- ⏳ Media type filters

### Phase 3 (Future)
- ⏳ Import/export stoplist
- ⏳ Community-shared stoplist templates
- ⏳ ML-based spam detection
- ⏳ Auto-learning from admin actions

---

## Testing Checklist

### Stoplist Configuration
- [ ] Open admin menu in DM (from group or `/groups`)
- [ ] Click "Configure Stoplist"
- [ ] Verify current list display
- [ ] Click "Edit Stoplist"
- [ ] Bot prompts for words
- [ ] Send comma-separated words
- [ ] Verify confirmation message
- [ ] Test message deletion in group (send message with stoplist word)
- [ ] Try `/cancel` during edit
- [ ] Clear stoplist
- [ ] Verify empty state

### Moderation Settings
- [ ] Click "Moderation Settings"
- [ ] Verify status display
- [ ] Check all toggles
- [ ] Navigate sub-menus
- [ ] Verify back button works

### System Messages Filter
- [ ] Click "System Messages Filter"
- [ ] See current configuration
- [ ] Verify "coming soon" state

### Permissions
- [ ] Test as admin (should work)
- [ ] Test as non-admin (should reject at edit step)
- [ ] Test FSM session expiry (wait > 5 min, then reply)
- [ ] Test empty word list
- [ ] Test with only commas/spaces

---

## Related Documentation

- **`MODERATION_ARCHITECTURE_V2.md`** - Background moderation system
- **`GROUP_ONBOARDING_ROADMAP.md`** - Admin controls overview
- **`GROUPLINK_GROUP_TITLE_FIX.md`** - Recent related fixes

---

**Status**: ✅ IMPLEMENTED  
**Version**: 1.0  
**Date**: October 12, 2025  
**Breaking Changes**: None (additive changes only)

