# Group Defaults - Proper Refactor Plan

## 🎯 **Problem**

We've been duplicating UI code for user defaults when we should just **REUSE** the existing group admin menus and handlers.

**Current State (Wrong)**:
- Separate `handle_user_group_defaults()` with duplicate UI
- Separate `handle_user_default_system_messages()` 
- Separate `handle_user_default_content_types()`
- Separate `handle_user_default_stoplist()`
- All duplicating logic that already exists for groups

**What We Should Do (Right)**:
- Use `create_group_admin_menu()` for BOTH groups AND user defaults
- Use existing handlers by passing `user_id` as `group_id` for defaults
- Detect user defaults vs group by ID sign:
  - **Positive ID** = User defaults
  - **Negative ID** = Group settings

---

## 🏗️ **Architecture**

### Key Insight

```python
# User defaults ARE group settings, just stored with user_id
GroupSettings(group_id=user_id, is_user_default=True)  # User defaults
GroupSettings(group_id=-1001234567, is_user_default=False)  # Group settings
```

### ID Convention

```python
def is_user_default(id: int) -> bool:
    """Check if ID represents user defaults (positive) or group (negative)."""
    return id > 0
```

---

## 📋 **Refactor Steps**

### **Step 1: Helper Function**

Add to handlers or utils:

```python
async def get_settings_for_id(id: int) -> GroupSettings:
    """
    Get settings for ID (user defaults if positive, group if negative).
    
    Args:
        id: user_id (positive) or group_id (negative)
    
    Returns:
        GroupSettings object
    """
    moderation_service = await get_moderation_service()
    
    if id > 0:
        # User defaults
        return await moderation_service.get_or_create_user_default_settings(id)
    else:
        # Group settings
        return await moderation_service.get_group_settings(id)
```

### **Step 2: Reuse Group Admin Menu**

Replace `handle_user_group_defaults()`:

```python
@router.callback_query(F.data == "user_group_defaults")
async def handle_user_group_defaults(callback: CallbackQuery):
    """Show user defaults - REUSES group admin menu!"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Get user defaults
    settings = await get_settings_for_id(user_id)
    
    # Build header
    text = f"""<b>{_('user_group_defaults.title', lang)}</b>
<i>{_('user_group_defaults.intro', lang)}</i>"""
    
    # REUSE existing group admin menu!
    from luka_bot.keyboards.group_admin import create_group_admin_menu
    
    keyboard = create_group_admin_menu(
        group_id=user_id,  # Pass user_id as group_id!
        group_title=None,
        moderation_enabled=settings.moderation_enabled,
        stoplist_count=len(settings.stoplist_words),
        current_language=lang,
        silent_mode=settings.silent_mode,
        ai_assistant_enabled=settings.ai_assistant_enabled
    )
    
    # Only thing to change: close button → back button
    # Modify last row's callback
    ...
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
```

### **Step 3: Update Existing Handlers**

Modify existing group handlers to support user defaults:

#### Example: System Messages Handler

```python
@router.callback_query(F.data.startswith("sys_msg_menu:"))
async def handle_system_messages_menu(callback: CallbackQuery):
    """Show system messages menu - works for BOTH groups AND user defaults!"""
    id = int(callback.data.split(":")[1])  # Can be user_id or group_id
    lang = await get_user_language(callback.from_user.id)
    
    # Get settings (auto-detects user defaults vs group)
    settings = await get_settings_for_id(id)
    
    # Existing logic works as-is!
    from luka_bot.keyboards.group_admin import create_system_messages_menu
    
    keyboard = create_system_messages_menu(
        group_id=id,  # Works for both!
        enabled_types=settings.service_message_types,
        language=lang
    )
    
    # Same text for both
    text = f"""🔧 <b>{_('group.btn.system_messages', lang)}</b>
...
"""
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
```

#### Example: Toggle Handler

```python
@router.callback_query(F.data.startswith("sys_msg_toggle:"))
async def handle_system_message_toggle(callback: CallbackQuery):
    """Toggle system message type - works for BOTH!"""
    parts = callback.data.split(":")
    type_key = parts[1]
    id = int(parts[2])  # Can be user_id or group_id
    
    # Get settings (auto-detects)
    moderation_service = await get_moderation_service()
    settings = await get_settings_for_id(id)
    
    # Toggle logic (same for both)
    ...
    settings.updated_at = datetime.utcnow()
    
    # Save (same method works for both!)
    await moderation_service.save_group_settings(settings)
    
    # Refresh view
    callback.data = f"sys_msg_menu:{id}"
    await handle_system_messages_menu(callback)
```

### **Step 4: Remove Duplicate Handlers**

Delete these (no longer needed):
- ❌ `handle_user_default_system_messages()`
- ❌ `handle_user_default_content_types()`
- ❌ `handle_user_default_stoplist()`
- ❌ `handle_toggle_user_default()` (partially - some logic may stay)

---

## ✅ **Benefits**

1. **Single Source of Truth** - One menu, one set of handlers
2. **No Code Duplication** - DRY principle
3. **Easier Maintenance** - Fix once, works everywhere
4. **Consistent UX** - Guaranteed same look & feel
5. **Less Bugs** - Fewer places for bugs to hide
6. **Smaller Codebase** - Less code to maintain

---

## 🎯 **Implementation Checklist**

- [ ] Add `get_settings_for_id()` helper
- [ ] Refactor `handle_user_group_defaults()` to reuse group menu
- [ ] Update `handle_system_messages_menu()` to support both
- [ ] Update `handle_system_message_toggle()` to support both
- [ ] Update stoplist handlers to support both
- [ ] Update moderation prompt handler to support both
- [ ] Remove duplicate user_default_* handlers
- [ ] Test with both user defaults and group settings
- [ ] Update documentation

---

## 🤔 **Open Questions**

1. **Callback Data Format**: Should we keep separate prefixes or unified?
   - Option A: Keep `group_*` prefix, detect by ID sign
   - Option B: Add `is_default` flag to callback data
   - **Recommendation**: Option A (cleaner)

2. **Back Button**: How to handle different "back" destinations?
   - User defaults → back to `/groups`
   - Group settings → close menu
   - **Solution**: Check ID sign in handler

3. **Header Text**: Different headers for defaults vs groups?
   - **Solution**: Pass header text as parameter or detect by ID

---

## 🚀 **Expected Result**

**Before**: ~500 lines of duplicate UI code  
**After**: ~100 lines of shared logic  
**Savings**: 80% less code!

**Code Reuse**:
```
create_group_admin_menu()          ← Used by both
create_system_messages_menu()      ← Used by both
handle_system_messages_menu()      ← Works for both
handle_system_message_toggle()     ← Works for both
handle_stoplist_config()           ← Works for both
...
```

---

## 💬 **User Feedback Summary**

> "those are incorrect... it should work same way... we need to reuse..."
> "why we can't just simply render the same menu for defaults as already exist for particular group"
> "why have two different menus managing the same GroupSettings model"

**User is 100% correct!** The refactor above implements exactly what was requested.

---

**Status**: 📝 **PLAN READY FOR APPROVAL**

Please review and approve to proceed with implementation.

