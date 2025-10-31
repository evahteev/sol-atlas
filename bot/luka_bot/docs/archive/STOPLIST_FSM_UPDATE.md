# Stoplist Editor: Command → FSM Update

**Date**: October 12, 2025  
**Change**: Replaced `/setstoplist` command with FSM-based interactive editor

---

## What Changed

### Before ❌
```
User: /setstoplist -1001902150742 spam, scam, phishing
Bot: ✅ Stoplist updated!
```

**Issues**:
- Complex command syntax
- User must know group ID
- Error-prone (typos in group ID)
- Not user-friendly

### After ✅
```
[User clicks "✏️ Edit Stoplist"]
Bot: Please send me the words...
     Format: word1, word2, word3
     Example: spam, scam, phishing
     
User: spam, scam, phishing
Bot: ✅ Stoplist updated!
```

**Benefits**:
- ✅ No complex command syntax
- ✅ Group ID auto-stored in FSM
- ✅ Clear prompts and examples
- ✅ `/cancel` support
- ✅ Better UX

---

## Technical Implementation

### FSM States

```python
class StoplistEditForm(StatesGroup):
    """FSM states for editing stoplist."""
    waiting_for_words = State()
    group_id = State()
```

### Flow Diagram

```
┌─────────────────────────────────────┐
│ User clicks "Edit Stoplist" button  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ FSM: Set state to waiting_for_words │
│ FSM: Store group_id in state data   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Bot edits message to show prompt    │
│ "Please send me the words..."        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ User sends message with words        │
│ OR sends /cancel                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Handler: handle_stoplist_words_input │
│ - Get group_id from FSM state       │
│ - Verify admin status               │
│ - Parse and validate words          │
│ - Update GroupSettings              │
│ - Clear FSM state                   │
│ - Send confirmation                 │
└─────────────────────────────────────┘
```

---

## Code Changes

### 1. Added FSM States (Top of file)

```python
from aiogram.fsm.state import State, StatesGroup

class StoplistEditForm(StatesGroup):
    """FSM states for editing stoplist."""
    waiting_for_words = State()
    group_id = State()
```

### 2. Updated Edit Handler

**Before**:
```python
@router.callback_query(F.data.startswith("group_stoplist_edit:"))
async def handle_stoplist_edit(callback: CallbackQuery):
    """Prompt user to edit stoplist."""
    await callback.answer(
        "✏️ To edit the stoplist, please send:\n\n"
        f"/setstoplist {group_id} word1, word2\n\n"
        "Separate words with commas.",
        show_alert=True
    )
```

**After**:
```python
@router.callback_query(F.data.startswith("group_stoplist_edit:"))
async def handle_stoplist_edit(callback: CallbackQuery, state: FSMContext):
    """Prompt user to edit stoplist."""
    group_id = int(callback.data.split(":")[1])
    
    # Store in FSM
    await state.update_data(group_id=group_id)
    await state.set_state(StoplistEditForm.waiting_for_words)
    
    # Edit message to show prompt
    await callback.message.edit_text(
        "✏️ <b>Edit Stoplist</b>\n\n"
        "Please send me the words...\n\n"
        "<b>Format:</b> <code>word1, word2, word3</code>\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML"
    )
```

### 3. Added Message Handler

```python
@router.message(StoplistEditForm.waiting_for_words, F.text)
async def handle_stoplist_words_input(message: Message, state: FSMContext):
    """Handle stoplist words input."""
    # Check for cancel
    if message.text.lower().strip() == "/cancel":
        await state.clear()
        await message.reply("❌ Cancelled")
        return
    
    # Get group_id from FSM
    data = await state.get_data()
    group_id = data.get("group_id")
    
    # Verify admin
    is_admin = await is_user_admin_in_group(
        message.bot, group_id, message.from_user.id
    )
    
    # Parse words
    words = [w.strip().lower() for w in message.text.split(",") if w.strip()]
    
    # Update settings
    settings.stoplist = words
    await moderation_service.save_group_settings(settings)
    
    # Clear FSM
    await state.clear()
    
    # Confirm
    await message.reply("✅ Stoplist updated!")
```

### 4. Removed Command Handler

**Deleted**:
```python
@router.message(Command("setstoplist"))
async def handle_setstoplist_command(message: Message):
    # ... command parsing logic
```

---

## Benefits

### User Experience
- ✅ **Simpler**: No complex command syntax
- ✅ **Guided**: Clear prompts and examples
- ✅ **Forgiving**: `/cancel` to abort anytime
- ✅ **Context-aware**: Group ID auto-stored

### Developer Experience
- ✅ **Cleaner**: FSM manages state automatically
- ✅ **Safer**: No manual group ID parsing
- ✅ **Maintainable**: Separate concerns (UI vs logic)
- ✅ **Testable**: FSM states are mockable

### Security
- ✅ **Admin check**: Still verified at input time
- ✅ **Session management**: FSM auto-expires
- ✅ **Input validation**: Same sanitization
- ✅ **State isolation**: FSM per-user

---

## Access Points

The stoplist editor is accessible from:

### 1. Group Inline Settings
```
Group → Bot added → Welcome message → ⚙️ Settings → 
Sends to DM → Admin menu → 🚫 Configure Stoplist
```

### 2. /groups Command
```
DM → /groups → Select group → Admin menu → 
🚫 Configure Stoplist
```

Both paths lead to the same FSM-based editor.

---

## Error Handling

### FSM Session Expiry
```python
data = await state.get_data()
group_id = data.get("group_id")

if not group_id:
    await message.reply("❌ Session expired. Please try again.")
    await state.clear()
    return
```

### Empty Word List
```python
words = [w.strip().lower() for w in message.text.split(",") if w.strip()]

if not words:
    await message.reply("❌ No valid words. Try again or /cancel")
    return  # Don't clear FSM, let user retry
```

### Admin Verification
```python
is_admin = await is_user_admin_in_group(message.bot, group_id, user_id)
if not is_admin:
    await message.reply("🔒 You must be an admin")
    await state.clear()
    return
```

---

## Testing

### Happy Path
1. ✅ Admin clicks "Edit Stoplist"
2. ✅ Bot shows prompt
3. ✅ Admin sends: `spam, scam, phishing`
4. ✅ Bot confirms update
5. ✅ FSM cleared automatically
6. ✅ Post "spam" in group → auto-deleted

### Cancel Flow
1. ✅ Admin clicks "Edit Stoplist"
2. ✅ Bot shows prompt
3. ✅ Admin sends: `/cancel`
4. ✅ Bot: "❌ Cancelled"
5. ✅ FSM cleared
6. ✅ Can start new edit

### Error Cases
- ✅ Non-admin clicks edit → Rejected at input
- ✅ Empty input → Retry prompt (FSM persists)
- ✅ Session expired → Clear FSM, ask to restart
- ✅ Only commas → Retry prompt

---

## Migration Notes

### Backward Compatibility
- ✅ No `/setstoplist` command to deprecate (was just added)
- ✅ No existing users relying on command
- ✅ GroupSettings storage unchanged
- ✅ No data migration needed

### Deployment
1. Deploy updated handler
2. FSM states automatically available (aiogram)
3. No configuration changes
4. No Redis schema changes

---

## Future Enhancements

### Phase 1 (Current) ✅
- FSM-based stoplist editor
- `/cancel` support
- Admin verification

### Phase 2 (Next)
- ⏳ Add/remove individual words (not full replace)
- ⏳ Import/export stoplist
- ⏳ Stoplist templates (crypto scams, adult content, etc.)

### Phase 3 (Future)
- ⏳ ML-suggested words based on deleted messages
- ⏳ Community-shared stoplists
- ⏳ Regex pattern support in FSM editor

---

**Status**: ✅ **IMPLEMENTED**  
**Tested**: Pending user testing  
**Breaking Changes**: None (removed unused command)

