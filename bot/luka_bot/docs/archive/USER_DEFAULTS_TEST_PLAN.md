# User Defaults Application - Test Plan 🧪

## 🐛 **Bug Fixed**

**Issue**: User defaults were NOT being applied when bot was added to groups.

**Root Cause**: `create_group_settings_from_user_defaults()` was hardcoding settings instead of copying from user defaults.

**Fix**: ✅ Now properly copies ALL 25+ settings from user defaults.

---

## 🧪 **Testing Required**

### **Important Note**
If you're testing with a group that existed BEFORE this fix:
- ⚠️ Old settings might still be cached from before the fix
- 🔄 Solution: Use the "Delete Group" button to fully clean it
- 🎯 Then re-add the bot to test with fresh settings

---

## 📋 **Test Scenarios**

### **Scenario 1: Brand New Group (Recommended)**
**Purpose**: Verify defaults are applied to completely new groups

**Steps**:
1. Configure your default settings in `/groups` → "Default Settings":
   ```
   ✅ Moderation: ON
   ✅ Stoplist: Add "spam", "test"
   ❌ AI Assistant: OFF
   ✅ Delete Links: ON
   ❌ KB Indexation: OFF
   ```

2. Create a BRAND NEW Telegram group (never added bot before)

3. Add bot to this new group

4. Go to `/groups` → Click the group → Check settings

5. **Expected Result**: ✅
   ```
   All your defaults should be applied:
   - Moderation: ON ✅
   - Stoplist: "spam", "test" ✅
   - AI Assistant: OFF ❌
   - Delete Links: ON ✅
   - KB Indexation: OFF ❌
   ```

---

### **Scenario 2: Previously Added Group (Delete & Re-add)**
**Purpose**: Verify delete button cleans everything properly

**Steps**:
1. Add bot to a group (any settings)

2. Go to `/groups` → Click the group → "Delete Group" button

3. Confirm deletion

4. Re-add bot to THE SAME group

5. Check group settings

6. **Expected Result**: ✅
   ```
   Group should have FRESH settings from your current defaults
   (Not the old settings from before deletion)
   ```

---

### **Scenario 3: Multiple Groups with Different Defaults**
**Purpose**: Verify each group gets the defaults that were active when it was added

**Steps**:
1. Configure defaults:
   ```
   Moderation: OFF
   AI Assistant: ON
   ```

2. Add bot to Group A

3. Change defaults:
   ```
   Moderation: ON
   AI Assistant: OFF
   ```

4. Add bot to Group B

5. Check both groups

6. **Expected Result**: ✅
   ```
   Group A: Moderation OFF, AI ON (from step 1)
   Group B: Moderation ON, AI OFF (from step 3)
   ```

---

### **Scenario 4: All Settings Categories**
**Purpose**: Verify ALL setting types are copied

**Configure these defaults**:
```
Bot Behavior:
✅ Silent Mode: ON
❌ AI Assistant: OFF
✅ KB Indexation: ON

Moderation:
✅ Moderate Admins: ON
✅ Moderation: ON
✅ Reputation: ON
✅ Auto-ban: ON
📝 Custom moderation prompt: "Test prompt"

Content Filters:
✅ Delete Links: ON
✅ Delete Images: ON
✅ Delete Videos: ON
❌ Delete Stickers: OFF
❌ Delete Forwarded: OFF
✅ Delete Service Messages: ON

Stoplist:
✅ Stoplist Enabled: ON
📝 Words: "spam, scam, test"
✅ Auto-delete: ON

Thresholds:
🎚️ Auto-delete: 9.0
🎚️ Auto-warn: 6.0
🎚️ Quality: 8.0
```

**Then**:
1. Add bot to a new group
2. Check EVERY setting in group settings

**Expected Result**: ✅ ALL settings match your defaults

---

## 🔍 **What to Check**

For EACH test scenario, verify these setting categories:

### ✅ **Bot Behavior**
- [ ] Silent Mode
- [ ] AI Assistant
- [ ] KB Indexation

### ✅ **Moderation**
- [ ] Moderate Admins
- [ ] Moderation Enabled
- [ ] Custom Moderation Prompt
- [ ] Reputation System
- [ ] Auto-ban

### ✅ **Content Filters**
- [ ] Delete Links
- [ ] Delete Images
- [ ] Delete Videos
- [ ] Delete Stickers
- [ ] Delete Forwarded
- [ ] Delete Service Messages
- [ ] Service Message Types

### ✅ **Stoplist**
- [ ] Stoplist Enabled
- [ ] Stoplist Words (full list)
- [ ] Case Sensitive
- [ ] Auto-delete

### ✅ **Thresholds**
- [ ] Auto-delete threshold
- [ ] Auto-warn threshold
- [ ] Quality threshold

---

## 🚨 **Known Issues to Watch For**

### **Issue 1: Old Settings Persist**
**Symptom**: Group has old settings, not defaults

**Cause**: Group was added before the fix, settings are cached

**Solution**: Delete group using "Delete Group" button, then re-add

---

### **Issue 2: Some Settings Missing**
**Symptom**: Some settings are correct, others are default

**Cause**: This WAS the bug (now fixed)

**Action**: If you still see this after the fix:
1. Check that you're using the updated code
2. Delete and re-add the group
3. Report which specific settings are missing

---

### **Issue 3: Delete Button Doesn't Work**
**Symptom**: After delete + re-add, group has old settings

**Cause**: Delete logic might not be cleaning Redis properly

**Action**: Check logs for:
```
🗑️ Deleted group settings: group_settings:{group_id}
```

---

## 📊 **Test Results Template**

Please fill this out when testing:

```markdown
## Test Results

**Date**: [Date]
**Bot Version**: [commit hash or date]

### Scenario 1: New Group
- [ ] ✅ All defaults applied correctly
- [ ] ❌ Issue: [describe]

### Scenario 2: Delete & Re-add
- [ ] ✅ Old settings removed
- [ ] ✅ New defaults applied
- [ ] ❌ Issue: [describe]

### Scenario 3: Multiple Groups
- [ ] ✅ Each group has correct defaults
- [ ] ❌ Issue: [describe]

### Scenario 4: All Settings
Settings not applied correctly:
- [ ] None - all working! ✅
- [ ] [List any issues]

### Overall
- [ ] ✅ Bug is fixed - defaults work perfectly
- [ ] ⚠️ Partial fix - some issues remain
- [ ] ❌ Bug still present

**Additional Notes**: [Any observations]
```

---

## 🎯 **Success Criteria**

The bug is considered FIXED when:

1. ✅ **New groups** get user's defaults (Scenario 1)
2. ✅ **Deleted groups** get fresh defaults on re-add (Scenario 2)
3. ✅ **Multiple groups** each get the defaults active when added (Scenario 3)
4. ✅ **ALL 25+ settings** are copied correctly (Scenario 4)

---

## 🔧 **Rollback Plan**

If the fix causes issues:

1. The changes are in: `luka_bot/services/moderation_service.py` lines 272-320
2. Can revert to hardcoded defaults if needed
3. No database migrations required - this is business logic only

---

## 📝 **Notes for Developer**

### **What Changed**
- File: `services/moderation_service.py`
- Function: `create_group_settings_from_user_defaults()`
- Change: Added 15+ lines to copy ALL settings from user defaults

### **Settings Now Copied** (that weren't before)
- `kb_indexation_enabled` ✅
- `moderate_admins_enabled` ✅
- `delete_links` ✅
- `delete_images` ✅
- `delete_videos` ✅
- `delete_stickers` ✅
- `delete_forwarded` ✅
- `delete_service_messages` ✅
- `service_message_types` ✅
- `stoplist_enabled` ✅
- `stoplist_words` ✅
- `stoplist_case_sensitive` ✅
- `stoplist_auto_delete` ✅

### **Always Copied** (were working before)
- `silent_mode`
- `ai_assistant_enabled`
- `moderation_enabled`
- `moderation_prompt`
- `reputation_enabled`
- `auto_ban_enabled`
- `auto_delete_threshold`
- `auto_warn_threshold`
- `quality_threshold`

---

**Test Status**: ⏳ Awaiting User Testing  
**Fix Status**: ✅ Implemented  
**Documentation**: ✅ Complete

