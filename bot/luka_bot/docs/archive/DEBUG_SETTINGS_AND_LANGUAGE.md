# Debug: Settings Flags & Language Not Applied 🔍

## 🐛 **Issues Reported**

1. ✅ **Stopwords and moderation prompt ARE copying correctly**
2. ❌ **Flags like AI Assistant are NOT copying correctly**
3. ❌ **Language is Russian in group, even though user set English in defaults**

---

## 🔧 **Fixes Applied**

### **Fix 1: Language Hardcoded to "en"**

**File**: `luka_bot/handlers/group_messages.py`

**Problem** ❌:
```python
language="en",  # Default language for new groups
```

This was **hardcoded** to English, ignoring the user's profile language preference!

**Solution** ✅:
```python
# Get user's preferred language for new group
from luka_bot.utils.i18n_helper import get_user_language
user_language = await get_user_language(user_id)
logger.info(f"📝 Using language '{user_language}' for group {group_id} (from user {user_id} preference)")

# Create group link (which creates Thread automatically)
group_service = await get_group_service()
link = await group_service.create_group_link(
    user_id=user_id,
    group_id=group_id,
    group_title=group_title,
    language=user_language,  # ✅ Use user's language preference
    user_role=user_role
)
```

**Now**: Group language matches the user's profile language (from `/profile`)

---

### **Fix 2: Added Debug Logging**

To diagnose why flags aren't copying correctly, added comprehensive logging:

#### **A) Log user defaults BEFORE creating group settings**
```python
# DEBUG: Log user's defaults first
user_defaults = await moderation_service.get_or_create_user_default_settings(user_id)
logger.info(f"📋 User {user_id} defaults: AI={user_defaults.ai_assistant_enabled}, Silent={user_defaults.silent_mode}, KB={user_defaults.kb_indexation_enabled}, Moderation={user_defaults.moderation_enabled}")
```

#### **B) Log group settings AFTER creation**
```python
logger.info(f"📋 Group {group_id} settings: AI={group_settings.ai_assistant_enabled}, Silent={group_settings.silent_mode}, KB={group_settings.kb_indexation_enabled}, Moderation={group_settings.moderation_enabled}")
```

#### **C) Log settings being SAVED to Redis**
```python
settings_dict = settings.to_dict()
# DEBUG: Log key settings being saved
logger.debug(f"💾 Saving to {key}: AI={settings_dict.get('ai_assistant_enabled')}, Silent={settings_dict.get('silent_mode')}, KB={settings_dict.get('kb_indexation_enabled')}, Moderation={settings_dict.get('moderation_enabled')}")
```

#### **D) Log settings being LOADED from Redis**
```python
# DEBUG: Log key settings being loaded
logger.debug(f"📖 Loading from {key}: AI={decoded_data.get('ai_assistant_enabled')}, Silent={decoded_data.get('silent_mode')}, KB={decoded_data.get('kb_indexation_enabled')}, Moderation={decoded_data.get('moderation_enabled')}")

settings = GroupSettings.from_dict(decoded_data)

# DEBUG: Log parsed settings
logger.debug(f"✅ Parsed settings: AI={settings.ai_assistant_enabled}, Silent={settings.silent_mode}, KB={settings.kb_indexation_enabled}, Moderation={settings.moderation_enabled}")
```

---

## 🧪 **Testing Instructions**

### **Prerequisites**
1. Delete any existing test groups first (use "Delete Group" button)
2. Clear Redis cache (or restart bot to ensure clean state)
3. Set your profile language to English: `/profile` → Change language → English

### **Test 1: Verify User Defaults**

1. Go to `/groups` → "Default Settings"
2. Configure specific settings:
   ```
   AI Assistant: OFF ❌
   Silent Mode: ON ✅
   KB Indexation: OFF ❌
   Moderation: ON ✅
   ```
3. Save settings
4. **Check logs** - you should see:
   ```
   ✅ Saved group settings: user_default_group_settings:922705
   💾 Saving to user_default_group_settings:922705: AI=False, Silent=True, KB=False, Moderation=True
   ```

### **Test 2: Add Bot to Fresh Group**

1. Create a **brand new** Telegram group
2. Add bot to this group
3. **Check logs** - you should see this sequence:

```
📝 Using language 'en' for group -1001902150742 (from user 922705 preference)

📋 User 922705 defaults: AI=False, Silent=True, KB=False, Moderation=True
✅ Created GroupSettings for group -1001902150742 from user 922705 template
📋 Group -1001902150742 settings: AI=False, Silent=True, KB=False, Moderation=True

💾 Saving to group_settings:-1001902150742: AI=False, Silent=True, KB=False, Moderation=True
✅ Saved group settings: group_settings:-1001902150742
```

### **Test 3: Verify Group Settings**

1. Go to `/groups` → Click the group → Settings
2. **Expected** ✅:
   ```
   AI Assistant: OFF ❌  (should match your defaults)
   Silent Mode: ON ✅    (should match your defaults)
   KB Indexation: OFF ❌ (should match your defaults)
   Moderation: ON ✅     (should match your defaults)
   Language: English 🇬🇧  (should match your profile)
   ```

### **Test 4: Verify Settings Persistence**

1. Exit and re-enter `/groups` → Group → Settings
2. **Check logs** for the LOAD operation:
   ```
   📖 Loading from group_settings:-1001902150742: AI=False, Silent=True, KB=False, Moderation=True
   ✅ Parsed settings: AI=False, Silent=True, KB=False, Moderation=True
   ```
3. Verify UI matches loaded settings

---

## 🔍 **What the Logs Will Tell Us**

### **Scenario A: Settings Copy Correctly, But Display is Wrong**

**Logs show**:
```
📋 User defaults: AI=False
📋 Group settings: AI=False  ✅ Copied correctly
💾 Saving: AI=False  ✅ Saved correctly
📖 Loading: AI=False  ✅ Loaded correctly
```

**But UI shows**: AI Assistant: ON ❌

**Diagnosis**: Issue is in the **UI rendering** (keyboards/group_admin.py), not the data layer

---

### **Scenario B: Settings Don't Copy**

**Logs show**:
```
📋 User defaults: AI=False
📋 Group settings: AI=True  ❌ NOT copied!
```

**Diagnosis**: Issue in `create_group_settings_from_user_defaults()` (line 281)

---

### **Scenario C: Settings Copy But Don't Save**

**Logs show**:
```
📋 User defaults: AI=False
📋 Group settings: AI=False  ✅ Copied
💾 Saving: AI=True  ❌ Changed during save!
```

**Diagnosis**: Issue in `to_dict()` serialization (models/group_settings.py line 173)

---

### **Scenario D: Settings Save But Don't Load**

**Logs show**:
```
💾 Saving: AI=False  ✅ Saved correctly
📖 Loading: AI=True  ❌ Loaded wrong!
```

**Diagnosis**: Issue in `from_dict()` deserialization (models/group_settings.py line 256)

---

## 📊 **Files Modified**

| File | Lines | Purpose |
|------|-------|---------|
| `handlers/group_messages.py` | 48-61, 78-87 | Get user language + debug logging |
| `services/moderation_service.py` | 67-73, 87-89 | Debug logging for save/load |

**Total**: 2 files, ~15 new lines (mostly logging)

---

## 🎯 **Expected Outcomes**

After these changes:

1. ✅ **Language issue FIXED** - Groups use user's profile language
2. 🔍 **Debug logging ADDED** - Can trace exact data flow
3. 📊 **Can diagnose** - Logs will show WHERE the issue is:
   - Copy phase
   - Save phase
   - Load phase
   - Display phase

---

## 🚨 **Next Steps**

### **Step 1: Test with Fresh Group**

Follow "Testing Instructions" above and **copy the full logs** from bot startup through group addition.

### **Step 2: Share Logs**

Look for these log lines:
```
📝 Using language
📋 User {user_id} defaults:
📋 Group {group_id} settings:
💾 Saving to group_settings
📖 Loading from group_settings
✅ Parsed settings:
```

### **Step 3: Check UI**

Compare what the logs say vs. what the UI shows. This will tell us if it's:
- ❌ Data layer issue (settings not copying/saving/loading)
- ❌ UI layer issue (data correct but display wrong)

---

## 💡 **Hypothesis**

Based on "stopwords and moderation prompt work correctly":

**Most likely**: The issue is in the **UI rendering**, not the data layer.

**Reason**: 
- `stoplist_words` (list) and `moderation_prompt` (string) are complex types
- They work, which means `to_dict()` / `from_dict()` work correctly
- Boolean flags might have a UI-specific rendering issue

**Alternative**: 
- Boolean serialization issue (unlikely, but possible)
- The logs will confirm or rule this out

---

## 🔧 **If Logs Show Settings ARE Correct**

If logs show:
```
📋 Group settings: AI=False ✅
💾 Saving: AI=False ✅
📖 Loading: AI=False ✅
```

But UI shows: "AI Assistant: ON ❌"

**Then fix**: `luka_bot/keyboards/group_admin.py` - The button rendering logic

Look for:
```python
ai_status = "ON ✅" if ai_assistant_enabled else "OFF ❌"
```

Ensure it's reading from the correct variable.

---

## 📝 **Summary**

**Language**: ✅ FIXED (now uses user's profile language)  
**Settings Flags**: 🔍 DEBUG LOGGING ADDED  
**Next**: Test and share logs to diagnose

**Status**: Ready for testing! 🚀

