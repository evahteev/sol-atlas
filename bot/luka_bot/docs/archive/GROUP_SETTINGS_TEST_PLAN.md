# Group Settings Enhancement - Test Plan

**Status**: Ready for Testing  
**Date**: October 12, 2025

---

## 🧪 Manual Testing Checklist

### Prerequisites
- [ ] Bot is running
- [ ] Redis is running and accessible
- [ ] Test Telegram account ready
- [ ] Test group(s) available
- [ ] Bot has admin rights in test groups

---

## 📋 Test Scenarios

### **Phase 1: Model & Service Layer (Backend)**

#### Test 1: GroupSettings Serialization (User Defaults)
**Objective**: Verify user defaults serialize/deserialize correctly

**Steps**:
1. Create user defaults via service
2. Check Redis key: `user_default_group_settings:{user_id}`
3. Verify all new fields are present in Redis
4. Load from Redis and verify values match

**Expected Result**:
- ✅ Redis key format correct
- ✅ All fields serialized
- ✅ Deserialization reconstructs object correctly
- ✅ `is_user_default=True` flag set

**How to Verify**:
```bash
# Check Redis
redis-cli GET "user_default_group_settings:YOUR_USER_ID"
```

---

#### Test 2: GroupSettings Serialization (Group Settings)
**Objective**: Verify group settings serialize/deserialize correctly

**Steps**:
1. Add bot to test group
2. Check Redis key: `group_settings:{group_id}`
3. Verify all new fields are present
4. Verify `is_user_default=False`

**Expected Result**:
- ✅ Redis key format correct
- ✅ New fields present with correct values
- ✅ `is_user_default=False` flag set

**How to Verify**:
```bash
# Check Redis
redis-cli GET "group_settings:YOUR_GROUP_ID"
```

---

#### Test 3: User Defaults Creation
**Objective**: Verify user defaults are created automatically

**Steps**:
1. Open `/groups` → "Default Settings" (first time)
2. Check logs for creation message
3. Verify Redis contains user defaults
4. Check all default values are correct

**Expected Result**:
- ✅ User defaults created on first access
- ✅ Defaults match initial values:
  - `silent_addition=False`
  - `silent_mode=False`
  - `ai_assistant_enabled=True`
  - `moderation_enabled=True`
  - `reputation_enabled=True`

**How to Verify**:
```bash
# Check logs
grep "Created default user settings" bot.log

# Check Redis
redis-cli GET "user_default_group_settings:YOUR_USER_ID" | python -m json.tool
```

---

#### Test 4: Template Application
**Objective**: Verify group settings inherit from user defaults

**Steps**:
1. Set user defaults (toggle some settings)
2. Add bot to NEW test group
3. Check group settings match user defaults
4. Verify all fields copied correctly

**Expected Result**:
- ✅ Group settings created from template
- ✅ All user default values copied
- ✅ Log shows: "Created group settings from user defaults"

**How to Verify**:
```bash
# Check logs
grep "Created group settings from user defaults" bot.log

# Compare Redis values
redis-cli GET "user_default_group_settings:YOUR_USER_ID"
redis-cli GET "group_settings:YOUR_GROUP_ID"
```

---

### **Phase 2: Silent Addition Flow**

#### Test 5: Silent Addition Enabled
**Objective**: Verify DM sent instead of group message

**Steps**:
1. Enable "Silent Addition" in user defaults
2. Add bot to NEW test group
3. Check for DM from bot
4. Verify NO welcome message in group
5. Check DM contains welcome text + controls

**Expected Result**:
- ✅ No message in group
- ✅ DM received with welcome
- ✅ DM contains inline keyboard with controls
- ✅ Log shows: "Sent silent onboarding to user"

**How to Verify**:
- Check group for messages (should be none)
- Check DM from bot (should contain welcome)
- Check logs for DM success

---

#### Test 6: Silent Addition Disabled
**Objective**: Verify normal welcome in group

**Steps**:
1. Disable "Silent Addition" in user defaults
2. Add bot to NEW test group
3. Verify welcome message appears in group
4. Check NO DM sent

**Expected Result**:
- ✅ Welcome message in group
- ✅ No DM sent
- ✅ Inline keyboard in group message

---

#### Test 7: Thread Context Addition
**Objective**: Verify onboarding added to /start thread

**Steps**:
1. Enable silent addition
2. Add bot to group
3. Open `/start` with bot in DM
4. Ask bot: "What groups do I manage?"
5. Verify bot knows about the group

**Expected Result**:
- ✅ Bot responds with knowledge of group addition
- ✅ Thread context contains group info
- ✅ Log shows: "Added group onboarding to thread"

---

#### Test 8: DM Failure Fallback
**Objective**: Verify graceful fallback when DM fails

**Steps**:
1. Block the bot in DM
2. Enable silent addition in defaults
3. Add bot to NEW test group
4. Verify welcome appears in GROUP (fallback)

**Expected Result**:
- ✅ Welcome message appears in group (fallback)
- ✅ Log shows: "Failed to send onboarding DM"
- ✅ No error/crash

---

### **Phase 3: AI Assistant Toggle**

#### Test 9: AI Assistant Disabled in Group
**Objective**: Verify bot ignores mentions when disabled

**Steps**:
1. Open group admin menu
2. Toggle "AI Assistant" → OFF
3. @mention bot in group
4. Verify bot does NOT respond

**Expected Result**:
- ✅ Bot ignores @mention
- ✅ Log shows: "AI assistant disabled for group {id}, ignoring mention"
- ✅ No response sent

---

#### Test 10: AI Assistant Enabled in Group
**Objective**: Verify bot responds when enabled

**Steps**:
1. Toggle "AI Assistant" → ON
2. @mention bot in group
3. Verify bot responds normally

**Expected Result**:
- ✅ Bot responds to @mention
- ✅ Normal LLM response generated

---

### **Phase 4: User Defaults UI**

#### Test 11: User Defaults - Main Menu
**Objective**: Verify comprehensive UI displays correctly

**Steps**:
1. Open `/groups` → "⚙️ Default Settings"
2. Verify all sections shown:
   - Bot Behavior (3 items)
   - Moderation (3 items)
3. Verify all buttons present:
   - Welcome toggle
   - Silent Mode + AI Assistant (row)
   - Moderation toggle
   - Reputation toggle
   - Stoplist button
   - Advanced Settings button
   - Back button

**Expected Result**:
- ✅ All sections displayed
- ✅ All buttons present
- ✅ Status values correct

---

#### Test 12: Toggle Persistence
**Objective**: Verify settings persist across sessions

**Steps**:
1. Toggle several settings (e.g., Moderation OFF, Silent Mode ON)
2. Close menu
3. Reopen `/groups` → "Default Settings"
4. Verify values persisted

**Expected Result**:
- ✅ All toggles show correct values
- ✅ Values match Redis data

---

#### Test 13: Stoplist Submenu
**Objective**: Verify stoplist UI works

**Steps**:
1. Open User Defaults → "🚫 Stoplist"
2. Verify display shows:
   - Enabled/disabled status
   - Case sensitivity
   - Word count
3. Toggle "Enable Stoplist"
4. Verify status updates

**Expected Result**:
- ✅ Stoplist submenu opens
- ✅ Toggle works
- ✅ View refreshes
- ✅ Back button returns to main menu

---

#### Test 14: Advanced Settings Submenu
**Objective**: Verify advanced settings UI works

**Steps**:
1. Open User Defaults → "⚙️ Advanced Settings"
2. Verify display shows:
   - All 5 content filters
   - Service message toggle
   - Thresholds
3. Toggle a filter (e.g., Delete Links)
4. Verify status updates

**Expected Result**:
- ✅ Advanced submenu opens
- ✅ All toggles present
- ✅ Toggle works
- ✅ View refreshes
- ✅ Back button works

---

### **Phase 5: Group Settings UI**

#### Test 15: Group Admin Menu
**Objective**: Verify new buttons appear in group settings

**Steps**:
1. Open group (with bot)
2. Click group name in `/groups`
3. Verify admin menu shows:
   - 🔇 Silent Mode button
   - 🤖 AI Assistant button

**Expected Result**:
- ✅ Both new buttons visible
- ✅ Buttons show current status (ON/OFF)
- ✅ Positioned correctly in menu

---

#### Test 16: Silent Mode Toggle (Group)
**Objective**: Verify silent mode toggle works per-group

**Steps**:
1. Open group admin menu
2. Toggle "🔇 Silent Mode"
3. Verify button updates
4. Check Redis for persistence

**Expected Result**:
- ✅ Toggle works
- ✅ Menu refreshes
- ✅ Redis updated
- ✅ Independent of user defaults

---

#### Test 17: AI Assistant Toggle (Group)
**Objective**: Verify AI toggle works per-group

**Steps**:
1. Open group admin menu
2. Toggle "🤖 AI Assistant"
3. Verify button updates
4. Test @mention behavior matches setting

**Expected Result**:
- ✅ Toggle works
- ✅ Menu refreshes
- ✅ Mention behavior matches setting

---

### **Phase 6: Internationalization**

#### Test 18: English UI
**Objective**: Verify all strings display correctly in English

**Steps**:
1. Set language to English
2. Navigate through:
   - User Defaults main menu
   - Stoplist submenu
   - Advanced submenu
   - Group admin menu
3. Verify all text is in English

**Expected Result**:
- ✅ All UI elements in English
- ✅ No missing translations
- ✅ No translation keys visible (e.g., "user_group_defaults.title")

---

#### Test 19: Russian UI
**Objective**: Verify all strings display correctly in Russian

**Steps**:
1. Set language to Russian
2. Navigate through all menus
3. Verify all text is in Russian

**Expected Result**:
- ✅ All UI elements in Russian
- ✅ No missing translations
- ✅ Proper Cyrillic characters

---

### **Phase 7: Permissions & Security**

#### Test 20: Admin-Only Restrictions
**Objective**: Verify non-admins cannot toggle group settings

**Steps**:
1. Add bot to test group
2. Use non-admin test account
3. Try to access group settings
4. Try to toggle any setting

**Expected Result**:
- ✅ Error message: "🔒 Admin only"
- ✅ Settings not changed
- ✅ Log shows access denied

---

### **Phase 8: Edge Cases**

#### Test 21: No User Defaults
**Objective**: Verify auto-creation of defaults

**Steps**:
1. Fresh user (never opened /groups before)
2. Add bot to group directly
3. Verify defaults auto-created
4. Check group settings match system defaults

**Expected Result**:
- ✅ User defaults auto-created
- ✅ Group settings use system defaults
- ✅ No errors

---

#### Test 22: Backwards Compatibility
**Objective**: Verify existing groups work with new code

**Steps**:
1. Identify existing group (added before this update)
2. Open group settings
3. Verify new fields present with defaults
4. Toggle new settings
5. Verify old settings still work

**Expected Result**:
- ✅ Existing groups load successfully
- ✅ New fields have default values
- ✅ Old settings unchanged
- ✅ New toggles work

---

### **Phase 9: Integration**

#### Test 23: End-to-End Flow
**Objective**: Complete user journey

**Steps**:
1. New user opens `/groups`
2. Sets user defaults:
   - Enable Silent Addition
   - Disable AI Assistant
   - Enable Stoplist
3. Adds bot to test group
4. Verifies:
   - DM received (silent addition)
   - AI mentions ignored (AI off)
   - Stoplist enabled in group
5. Opens group settings
6. Overrides: Enable AI Assistant
7. Tests @mention works

**Expected Result**:
- ✅ All steps complete successfully
- ✅ Settings flow correctly
- ✅ Overrides work independently

---

## 📊 Test Results Template

Use this template to record test results:

```markdown
### Test #: [Test Name]
**Date**: [Date]
**Tester**: [Name]
**Status**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL

**Results**:
- Step 1: [✅/❌] [Notes]
- Step 2: [✅/❌] [Notes]
- ...

**Issues Found**:
1. [Description]
2. [Description]

**Screenshots**: [Attach if relevant]

**Logs**:
```
[Relevant log entries]
```

**Notes**: [Any additional observations]
```

---

## 🐛 Bug Report Template

If issues are found, use this template:

```markdown
### Bug: [Short Description]
**Severity**: Critical / High / Medium / Low
**Test**: Test # [number]

**Description**:
[Detailed description of the bug]

**Steps to Reproduce**:
1. [Step]
2. [Step]
3. [Step]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Environment**:
- Bot version: [version]
- Redis version: [version]
- Python version: [version]

**Logs**:
```
[Error logs]
```

**Screenshots**: [If applicable]

**Workaround**: [If any found]
```

---

## ✅ Sign-Off

After completing all tests:

```markdown
## Test Summary

**Total Tests**: 23
**Passed**: [#]
**Failed**: [#]
**Partial**: [#]

**Critical Issues**: [#]
**High Priority**: [#]
**Medium Priority**: [#]
**Low Priority**: [#]

**Recommendation**: ✅ APPROVE FOR PRODUCTION / ⚠️ FIX ISSUES FIRST / ❌ MAJOR ISSUES

**Tester**: [Name]
**Date**: [Date]
**Signature**: _______________
```

---

## 📚 Quick Reference

### Useful Redis Commands

```bash
# View all user defaults
redis-cli KEYS "user_default_group_settings:*"

# View all group settings
redis-cli KEYS "group_settings:*"

# Get specific user defaults
redis-cli GET "user_default_group_settings:USER_ID" | python -m json.tool

# Get specific group settings
redis-cli GET "group_settings:GROUP_ID" | python -m json.tool

# Delete test data (BE CAREFUL!)
redis-cli DEL "user_default_group_settings:TEST_USER_ID"
redis-cli DEL "group_settings:TEST_GROUP_ID"
```

### Useful Log Grep Commands

```bash
# Silent addition events
grep "Created group settings from user defaults" bot.log
grep "Sent silent onboarding to user" bot.log
grep "Failed to send onboarding DM" bot.log

# AI assistant events
grep "AI assistant disabled for group" bot.log

# Settings changes
grep "toggled default setting" bot.log
grep "toggled group setting" bot.log
```

---

## 🎓 Testing Best Practices

1. **Test in Order**: Follow the phases sequentially
2. **Document Everything**: Record all results, even passes
3. **Take Screenshots**: Visual proof is helpful
4. **Save Logs**: Capture relevant log entries
5. **Test Both Languages**: Don't skip i18n testing
6. **Test Edge Cases**: They often reveal bugs
7. **Reset Between Tests**: Use fresh data when possible
8. **Verify Redis**: Always check data persistence

---

**Happy Testing!** 🧪✨

