# 🧪 Group Settings Refactor - Testing Checklist

## ⚠️ **Before Testing**

### **1. Compile i18n translations (if possible):**
```bash
cd luka_bot/locales/en/LC_MESSAGES
msgfmt messages.po -o messages.mo
cd ../../ru/LC_MESSAGES
msgfmt messages.po -o messages.mo
cd ../../../..
```

If `msgfmt` is not available, install gettext:
```bash
# macOS
brew install gettext
brew link gettext --force

# Ubuntu/Debian
sudo apt-get install gettext

# Or skip if translations already compiled
```

### **2. Restart bot (to load new handlers):**
```bash
# Stop current bot process
# Start bot again
```

---

## ✅ **Testing Scenarios**

### **Scenario 1: User Defaults Menu** 🎯

**Steps:**
1. Open Telegram
2. Send `/groups` command to bot
3. Click "📋 Default Settings" button

**Expected Results:**
- ✅ Menu opens showing all settings
- ✅ Language selector present
- ✅ Moderation toggle present
- ✅ Silent Mode toggle present
- ✅ AI Assistant toggle present
- ✅ Moderation Rules button present
- ✅ System Messages button present
- ✅ Content Types button present (**NEW!**)
- ✅ Stoplist button present
- ❌ NO "Scheduled Content" button
- ❌ NO "Import History" button
- ❌ NO "Stats" button
- ❌ NO "Refresh" button

**Verify:**
- [ ] Menu displays correctly
- [ ] All expected buttons present
- [ ] Group-specific buttons hidden
- [ ] Back button returns to `/groups` list

---

### **Scenario 2: Toggle User Defaults** 🔄

**Steps:**
1. In user defaults menu, click each toggle:
   - Moderation toggle
   - Silent Mode toggle
   - AI Assistant toggle

**Expected Results:**
- ✅ Each toggle shows confirmation
- ✅ Menu refreshes with new status
- ✅ Status persists (close and reopen → same status)

**Verify:**
- [ ] Moderation toggle works
- [ ] Silent Mode toggle works (also updates silent_addition)
- [ ] AI Assistant toggle works
- [ ] Menu refreshes properly
- [ ] Settings persist after bot restart

---

### **Scenario 3: System Messages Submenu** 📨

**Steps:**
1. In user defaults menu, click "System Messages"
2. Toggle different message types
3. Click "Back"

**Expected Results:**
- ✅ Submenu shows all message types with checkmarks
- ✅ Types: User joined/left, Title changes, Pinned, Voice chat, Photo
- ✅ Toggles update immediately
- ✅ Back returns to user defaults menu

**Verify:**
- [ ] Submenu displays correctly
- [ ] All message types present
- [ ] Toggles work
- [ ] Back button works

---

### **Scenario 4: Content Types Submenu** 🗂️ **NEW!**

**Steps:**
1. In user defaults menu, click "Content Types"
2. Toggle different content filters
3. Click "Back"

**Expected Results:**
- ✅ Submenu shows all content types
- ✅ Types: Links, Images, Videos, Stickers, Forwarded
- ✅ Each has status (🗑️ Will Delete / ✅ Allowed)
- ✅ Toggles update immediately
- ✅ Back returns to user defaults menu

**Verify:**
- [ ] Submenu displays correctly
- [ ] All content types present
- [ ] Status indicators correct
- [ ] Toggles work
- [ ] Back button works

---

### **Scenario 5: Moderation Rules/Prompt** 📝 **NEW!**

**Steps:**
1. In user defaults menu, click "Moderation Rules"
2. View current prompt
3. Click "Back"

**Expected Results:**
- ✅ Shows current prompt (or "Using default")
- ✅ Has "Edit Prompt" button
- ✅ Has "Reset to Default" button (if custom prompt exists)
- ✅ Back returns to user defaults menu

**Verify:**
- [ ] Prompt display works
- [ ] Default prompt message shows if no custom
- [ ] Custom prompt shows if set
- [ ] Buttons present
- [ ] Back button works

---

### **Scenario 6: Stoplist Submenu** 🚫

**Steps:**
1. In user defaults menu, click "Stoplist"
2. View stoplist
3. Toggle stoplist enabled/disabled
4. Click "Back"

**Expected Results:**
- ✅ Shows current stoplist words
- ✅ Shows regex examples
- ✅ Has toggle button
- ✅ Has "Edit List" button
- ✅ Back returns to user defaults menu

**Verify:**
- [ ] Stoplist displays correctly
- [ ] Regex examples shown
- [ ] Description clear
- [ ] Toggle works
- [ ] Back button works

---

### **Scenario 7: Group Settings Menu** 🏢

**Steps:**
1. Send `/groups` command
2. Select a group from the list
3. Click on group admin settings

**Expected Results:**
- ✅ Menu opens with ALL settings (including group-specific)
- ✅ All buttons from user defaults present
- ✅ PLUS: Scheduled Content button
- ✅ PLUS: Import History button
- ✅ PLUS: Stats button
- ✅ PLUS: Refresh button

**Verify:**
- [ ] Menu displays correctly
- [ ] All user defaults buttons present
- [ ] Group-specific buttons present
- [ ] Menu looks identical to user defaults (except extra buttons)

---

### **Scenario 8: Group Settings Toggles** 🔄

**Steps:**
1. In group admin menu, toggle each setting:
   - Moderation
   - Silent Mode
   - AI Assistant

**Expected Results:**
- ✅ Same behavior as user defaults
- ✅ Settings save
- ✅ Menu refreshes
- ✅ Admin-only restriction works

**Verify:**
- [ ] Toggles work
- [ ] Menu refreshes properly
- [ ] Admin check enforced
- [ ] Non-admins see "Admin only" error

---

### **Scenario 9: Group Settings Submenus** 📂

**Steps:**
1. Test each submenu in group settings:
   - System Messages
   - Content Types
   - Moderation Rules
   - Stoplist

**Expected Results:**
- ✅ All submenus work
- ✅ Identical to user defaults
- ✅ Settings save to group (not user defaults)
- ✅ Back button returns to group admin menu

**Verify:**
- [ ] System Messages submenu works
- [ ] Content Types submenu works
- [ ] Moderation Rules submenu works
- [ ] Stoplist submenu works
- [ ] Back buttons work correctly

---

### **Scenario 10: Cross-Context Behavior** 🔄

**Steps:**
1. Set user defaults:
   - Moderation: ON
   - Silent Mode: ON
   - AI Assistant: OFF
   - Content filters: Delete links

2. Add bot to a NEW test group

3. Open group settings for that new group

**Expected Results:**
- ✅ New group inherits user defaults
- ✅ Moderation ON
- ✅ Silent Mode ON
- ✅ AI Assistant OFF
- ✅ Delete links ON

**Verify:**
- [ ] Defaults applied to new group
- [ ] All settings match user defaults
- [ ] Group can override defaults independently
- [ ] User defaults unchanged when group settings change

---

### **Scenario 11: Existing Groups** 🏛️

**Steps:**
1. Open settings for an EXISTING group (added before refactor)

**Expected Results:**
- ✅ Settings menu works normally
- ✅ All existing settings preserved
- ✅ New fields have default values
- ✅ No errors

**Verify:**
- [ ] Existing groups work
- [ ] No data lost
- [ ] New fields default properly
- [ ] Backwards compatible

---

### **Scenario 12: Language Switching** 🌍

**Steps:**
1. Change user language to Russian
2. Open user defaults menu
3. Check that all text is in Russian
4. Change to English
5. Check that all text is in English

**Expected Results:**
- ✅ All UI strings properly translated
- ✅ No raw i18n keys visible
- ✅ Proper emoji and formatting

**Verify:**
- [ ] English UI works
- [ ] Russian UI works
- [ ] No missing translations
- [ ] No "msgid" strings shown

---

## 🐛 **Edge Cases to Test**

### **Edge Case 1: No User Defaults Exist**
**Test:** User opens defaults menu for first time
**Expected:** Defaults created with sensible defaults

### **Edge Case 2: Corrupted Settings**
**Test:** Delete user defaults from Redis, open menu
**Expected:** New defaults created gracefully

### **Edge Case 3: Admin Permission Changes**
**Test:** Remove admin, try to change group settings
**Expected:** "Admin only" error shown

### **Edge Case 4: Bot Not in Group**
**Test:** Remove bot, try to access group settings from `/groups`
**Expected:** Error message or removed from list

---

## ✅ **Sign-Off Checklist**

After testing all scenarios:

- [ ] User defaults menu works perfectly
- [ ] Group settings menu works perfectly
- [ ] All toggles work in both contexts
- [ ] All submenus work in both contexts
- [ ] Content types feature works (**NEW**)
- [ ] Moderation rules feature works (**NEW**)
- [ ] Cross-context behavior correct
- [ ] No errors in logs
- [ ] No UI glitches
- [ ] i18n working (both English and Russian)
- [ ] Admin restrictions enforced
- [ ] Settings persist correctly

---

## 📝 **Bug Report Template**

If you find issues:

```
**Context:** User Defaults / Group Settings
**Scenario:** [Which test scenario]
**Steps to Reproduce:**
1. 
2. 
3. 

**Expected:** 
**Actual:** 
**Error Logs:** [If any]
**Screenshots:** [If helpful]
```

---

## 🚀 **Ready for Production**

When all tests pass:
- [ ] All checkboxes ticked
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] User experience smooth

**Then**: Deploy to production! 🎉

---

**Good luck with testing!** 🧪✨

