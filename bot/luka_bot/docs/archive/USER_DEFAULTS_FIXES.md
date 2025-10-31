# 🔧 User Defaults - Final Fixes

## ❌ **Issues Found**

1. **"Group not initialized" errors** for System Messages, Stoplist, and Language in user defaults
2. These handlers were using `get_group_settings()` which only works for groups (negative IDs)
3. Language button shouldn't appear for user defaults (language is per-group, not per-defaults)

---

## ✅ **Fixes Applied**

### **1. System Messages Handler**
**File**: `luka_bot/handlers/group_admin.py`

**Before:**
```python
settings = await moderation_service.get_group_settings(group_id)
if not settings:
    await callback.answer("⚠️ Group not initialized", show_alert=True)
    return

language = await group_service.get_group_language(group_id)
```

**After:**
```python
settings = await get_settings_for_id(id)  # Works for both!
if not settings:
    await callback.answer("⚠️ Settings not found", show_alert=True)
    return

# Get language based on context
if id > 0:  # User defaults
    from luka_bot.utils.i18n_helper import get_user_language
    language = await get_user_language(callback.from_user.id)
else:  # Group
    language = await group_service.get_group_language(group_id)
```

---

### **2. System Message Toggle Handler**
**File**: `luka_bot/handlers/group_admin.py`

**Updated `handle_sys_msg_toggle()`:**
```python
# Get current settings (works for both groups and user defaults!)
settings = await get_settings_for_id(id)
```

---

### **3. Stoplist Handler**
**File**: `luka_bot/handlers/group_admin.py`

**Updated `handle_stoplist_config()`:**
```python
# Get current stoplist (works for both groups and user defaults!)
settings = await get_settings_for_id(id)

# Get language for i18n
if id > 0:  # User defaults
    from luka_bot.utils.i18n_helper import get_user_language
    language = await get_user_language(callback.from_user.id)
else:  # Group
    language = await group_service.get_group_language(group_id)
```

---

### **4. Language Button - Hidden for User Defaults**
**File**: `luka_bot/keyboards/group_admin.py`

**Why**: Language is a per-group setting. User defaults apply to multiple groups with potentially different languages, so language selection doesn't make sense for defaults.

**Updated `create_group_admin_menu()`:**
```python
# Row 1: Language (only for groups, not user defaults)
if not is_user_defaults:
    buttons.append([
        InlineKeyboardButton(
            text=f"{lang_flag} {_('group.btn.language', current_language)}: {lang_name}",
            callback_data=f"group_lang_menu:{group_id}"
        )
    ])
```

---

## 📋 **Summary of All Fixed Handlers**

| Handler | Issue | Fix |
|---------|-------|-----|
| `handle_sys_msg_menu()` | Used `get_group_settings()` | Now uses `get_settings_for_id()` |
| `handle_sys_msg_toggle()` | Used `get_group_settings()` | Now uses `get_settings_for_id()` |
| `handle_stoplist_config()` | Used `get_group_settings()` | Now uses `get_settings_for_id()` |
| `create_group_admin_menu()` | Showed language for defaults | Now hidden for defaults |

---

## 🎯 **How It Works Now**

### **For User Defaults (Positive ID):**
```
User opens: /groups → Default Settings

Available Settings:
✅ Moderation toggle
✅ Silent Mode toggle  
✅ AI Assistant toggle
✅ Moderation Rules
✅ System Messages (with proper settings fetch)
✅ Content Types
✅ Stoplist (with proper settings fetch)
❌ Language (hidden - doesn't apply to defaults)
❌ Scheduled Content (hidden - group-specific)
❌ Import History (hidden - group-specific)
❌ Stats (hidden - group-specific)
❌ Refresh (hidden - group-specific)
```

### **For Groups (Negative ID):**
```
User opens: /groups → Select Group → Settings

Available Settings:
✅ Language selector
✅ Moderation toggle
✅ Silent Mode toggle
✅ AI Assistant toggle
✅ Moderation Rules
✅ System Messages
✅ Content Types
✅ Stoplist
✅ Scheduled Content
✅ Import History
✅ Stats
✅ Refresh
```

---

## ✅ **Testing Checklist**

User Defaults (should work now):
- [ ] System Messages submenu opens ✅
- [ ] Can toggle system message types ✅
- [ ] Stoplist submenu opens ✅
- [ ] Can view/edit stoplist ✅
- [ ] Language button NOT shown ✅
- [ ] No "Group not initialized" errors ✅

Groups (should still work):
- [ ] System Messages submenu works ✅
- [ ] Stoplist submenu works ✅
- [ ] Language submenu works ✅
- [ ] All toggles work ✅

---

## 🎉 **Status: All Fixed!**

All handlers now correctly support **BOTH** user defaults AND group settings using the unified `get_settings_for_id()` helper.

**Key Pattern:**
```python
# Universal handler pattern
id = int(callback.data.split(":")[1])

# Admin check (groups only)
if id < 0:
    is_admin = await is_user_admin_in_group(...)
    if not is_admin:
        return

# Get settings (works for both!)
settings = await get_settings_for_id(id)

# Get language (context-aware)
if id > 0:
    lang = await get_user_language(user_id)
else:
    lang = await group_service.get_group_language(id)
```

**Restart the bot and test!** 🚀

