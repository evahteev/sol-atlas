# I18N Refactoring TODO

## 🎯 **Goal**
Replace all inline `if lang == "en":` / `else:` blocks with proper `_()` i18n helper function calls using message keys from `.po` files.

## 📊 **Current State**
- **Total instances**: ~92 across 9 Python files
- **Pattern**: Hardcoded English/Russian strings in if/else blocks
- **Problem**: Difficult to maintain, inconsistent, translation changes require code changes

## ✅ **Target Pattern**

### ❌ **BEFORE (Bad):**
```python
if lang == "en":
    text = "⚙️ Default Settings"
else:
    text = "⚙️ Настройки по умолчанию"
```

### ✅ **AFTER (Good):**
```python
text = _('groups.btn.default_settings', lang)
```

With `.po` entries:
```po
msgid "groups.btn.default_settings"
msgstr "⚙️ Default Settings"  # en

msgid "groups.btn.default_settings"
msgstr "⚙️ Настройки по умолчанию"  # ru
```

---

## 📝 **TODO List by File**

### **1. handlers/groups_enhanced.py** (15 instances)

#### Line 84-111: Groups intro text
- [ ] Extract `/groups` command intro to i18n key
- [ ] Keys needed:
  - `groups.intro.title` 
  - `groups.intro.how_to_add`
  - `groups.intro.what_i_do`

#### Line 122-125: No groups message
- [ ] Extract "not in any groups yet" message
- [ ] Key: `groups.no_groups.message`

#### Line 129-134: Groups list header/footer
- [ ] Extract groups list header
- [ ] Keys:
  - `groups.list.header` (with count placeholder)
  - `groups.list.footer`

#### Line 167-173: Default Settings button
- [ ] Extract "Default Settings" / "Настройки по умолчанию"
- [ ] Key: `groups.btn.default_settings`

#### Line 177-186: Refresh/Close buttons
- [ ] Extract "Refresh" / "Обновить"
- [ ] Extract "Close" / "Закрыть"
- [ ] Keys:
  - `common.btn.refresh`
  - `common.btn.close`

#### Line 283-323: Group view info text
- [ ] Extract group info template
- [ ] Keys:
  - `groups.view.setup_complete`
  - `groups.view.type`
  - `groups.view.connected_topics`
  - `groups.view.quick_actions`

#### Line 367-407: Groups back - no groups text
- [ ] Duplicate of intro text - use same keys

#### Line 413-418: Groups back - list header/footer
- [ ] Duplicate - use same keys as above

#### Line 450-469: Groups back - buttons
- [ ] Duplicate - use same keys as above

#### Line 509-512: Close confirmation
- [ ] Extract "Groups menu closed"
- [ ] Key: `groups.menu_closed`

#### Line 530-543: Context switching coming soon
- [ ] Extract "coming soon" alert
- [ ] Key: `groups.context_switch.coming_soon`

#### Line 555-566: Digest coming soon
- [ ] Extract digest preview alert
- [ ] Key: `groups.digest.coming_soon`

#### Line 585-591: Moderation tip
- [ ] Extract moderation tip alert
- [ ] Key: `groups.moderation_tip`

---

### **2. handlers/group_admin.py** (7 instances)

#### Line 167-245: Group admin menu header
- [ ] Extract admin menu metadata display
- [ ] Keys:
  - `group_admin.menu.type`
  - `group_admin.menu.members`
  - `group_admin.menu.agent`
  - `group_admin.menu.kb_status`
  - `group_admin.menu.thread_id`
  - `group_admin.menu.admins`

#### Line 469-489: Stoplist config menu
- [ ] Extract stoplist menu text and buttons
- [ ] Keys:
  - `group.stoplist.menu.title`
  - `group.stoplist.menu.status`
  - `group.stoplist.btn.edit`
  - `group.stoplist.btn.clear`

#### Line 572-602: System messages menu
- [ ] Extract system messages header
- [ ] Keys:
  - `group.sys_msg.menu.title`
  - `group.sys_msg.menu.description`
  - `group.sys_msg.menu.status`

#### Line 795-836: Import history prompt
- [ ] Extract import instructions
- [ ] Keys:
  - `group.import.instructions`
  - `group.import.format_example`

#### Line 892-920: Stoplist input confirmation
- [ ] **ALREADY DONE** (has hardcoded English/Russian but needs `.po` entries)
- [ ] Verify keys exist:
  - `group.stoplist.updated`
  - `group.stoplist.total_words`
  - `group.stoplist.preview`

#### Line 1426-1461: Moderation prompt input confirmation
- [ ] Extract confirmation messages
- [ ] Keys already exist, but code has inline fallback

---

### **3. handlers/group_settings_inline.py** (4 instances)

#### Line 141-160: Language change confirmation
- [ ] Extract language update messages
- [ ] Keys:
  - `group.language.updated`

#### Line 189-195: Welcome toggle notification
- [ ] Extract welcome toggle status
- [ ] Keys:
  - `group.welcome.enabled`
  - `group.welcome.disabled`

#### Line 229-264: Group language menu display
- [ ] Extract language selection menu
- [ ] Keys:
  - `group.language.menu.title`
  - `group.language.menu.current`

---

### **4. handlers/group_commands.py** (15 instances)

#### Line 45-87: /help command
- [ ] Extract help text
- [ ] Keys:
  - `group.help.title`
  - `group.help.commands`
  - `group.help.mention`

#### Line 130-156: /stats command
- [ ] Extract stats display
- [ ] Keys:
  - `group.stats.title`
  - `group.stats.members`
  - `group.stats.messages`

#### Line 196-245: /reputation command
- [ ] Extract reputation display
- [ ] Keys:
  - `group.reputation.title`
  - `group.reputation.your_score`
  - `group.reputation.leaderboard`

#### Line 279-320: /reset command confirmation
- [ ] Extract reset warning and confirmation
- [ ] Keys:
  - `group.reset.warning`
  - `group.reset.confirm_prompt`
  - `group.reset.btn.confirm`
  - `group.reset.btn.cancel`

---

### **5. handlers/reputation_viewer.py** (7 instances)

#### Line 32-88: Reputation details display
- [ ] Extract reputation breakdown
- [ ] Keys:
  - `reputation.details.title`
  - `reputation.details.breakdown`
  - `reputation.details.history`

#### Line 128-165: Leaderboard display
- [ ] Extract leaderboard template
- [ ] Keys:
  - `reputation.leaderboard.title`
  - `reputation.leaderboard.position`

---

### **6. handlers/moderation_settings_handlers.py** (3 instances)

#### Line 54-92: Moderation rules menu
- [ ] Extract moderation settings display
- [ ] Keys:
  - `moderation.rules.menu.title`
  - `moderation.rules.current`

---

### **7. keyboards/group_settings_inline.py** (3 instances)

#### Line 48-73: Group language keyboard
- [ ] Extract language selection keyboard
- [ ] Keys already defined, just needs refactoring

---

### **8. keyboards/moderation_settings.py** (5 instances)

#### Line 31-86: Moderation settings keyboard
- [ ] Extract moderation toggles
- [ ] Keys:
  - `moderation.settings.enable`
  - `moderation.settings.auto_delete`
  - `moderation.settings.reputation`

---

### **9. utils/welcome_generator.py** (1 instance)

#### Line 28-92: Welcome message generation
- [ ] Extract welcome message template
- [ ] Keys:
  - `group.welcome.greeting`
  - `group.welcome.capabilities`
  - `group.welcome.cta`

---

## 🎯 **Implementation Strategy**

### **Phase 1: High-Traffic Areas (Priority 1)**
1. ✅ `/groups` command (handlers/groups_enhanced.py)
2. ✅ Group admin menu (handlers/group_admin.py)
3. ✅ Common buttons (Refresh, Close, Back)

### **Phase 2: Admin Features (Priority 2)**
4. ✅ Group settings (handlers/group_settings_inline.py)
5. ✅ System messages menu
6. ✅ Stoplist configuration

### **Phase 3: User-Facing Commands (Priority 3)**
7. ✅ /help, /stats, /reputation (handlers/group_commands.py)
8. ✅ Reputation viewer
9. ✅ Welcome messages

### **Phase 4: Advanced Features (Priority 4)**
10. ✅ Moderation settings
11. ✅ Import history
12. ✅ Reset confirmations

---

## 📋 **Refactoring Checklist Per Instance**

For each occurrence:

1. **[ ] Identify the string pair** (EN/RU)
2. **[ ] Choose appropriate i18n key** (follow naming convention)
3. **[ ] Add entries to `.po` files**:
   - `/luka_bot/locales/en/LC_MESSAGES/messages.po`
   - `/luka_bot/locales/ru/LC_MESSAGES/messages.po`
4. **[ ] Replace inline if/else with `_()` call**
5. **[ ] Test both languages**
6. **[ ] Compile translations**: `msgfmt messages.po -o messages.mo`

---

## 🏗️ **Key Naming Convention**

Follow this hierarchy:
```
{module}.{feature}.{element}

Examples:
- groups.btn.default_settings
- groups.list.header
- group_admin.menu.title
- moderation.rules.current
- common.btn.refresh
```

---

## 📦 **Benefits After Completion**

✅ **Consistency**: One pattern for all i18n  
✅ **Maintainability**: Translations in one place  
✅ **Scalability**: Easy to add new languages  
✅ **Testability**: Can test translation coverage  
✅ **Separation**: Logic separated from presentation  

---

## 🔢 **Progress Tracking**

- **Total instances**: 92
- **Completed**: 0
- **In progress**: 0
- **Remaining**: 92

Update this as you refactor each file!

---

## 🚀 **Quick Start Guide**

### **Example Refactoring:**

**1. Find the code:**
```python
if lang == "en":
    keyboard_buttons.append([
        InlineKeyboardButton(text="⚙️ Default Settings", callback_data="user_group_defaults")
    ])
else:
    keyboard_buttons.append([
        InlineKeyboardButton(text="⚙️ Настройки по умолчанию", callback_data="user_group_defaults")
    ])
```

**2. Add to `.po` files:**
```po
# en/LC_MESSAGES/messages.po
msgid "groups.btn.default_settings"
msgstr "⚙️ Default Settings"

# ru/LC_MESSAGES/messages.po
msgid "groups.btn.default_settings"
msgstr "⚙️ Настройки по умолчанию"
```

**3. Replace code:**
```python
keyboard_buttons.append([
    InlineKeyboardButton(
        text=_('groups.btn.default_settings', lang), 
        callback_data="user_group_defaults"
    )
])
```

**4. Compile and test:**
```bash
cd luka_bot/locales/en/LC_MESSAGES && msgfmt messages.po -o messages.mo
cd ../../ru/LC_MESSAGES && msgfmt messages.po -o messages.mo
```

---

## 📝 **Notes**

- Some instances may already have `.po` entries but still use inline strings as fallback
- Watch for format strings with placeholders: `{count}`, `{name}`, etc.
- Multi-line strings need special handling in `.po` files
- Test emoji rendering in both languages
- Check that line breaks (`\n`) are consistent

---

**Created**: 2025-10-13  
**Priority**: Medium (technical debt)  
**Impact**: High (maintainability & consistency)

