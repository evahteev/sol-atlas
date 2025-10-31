# 🌍 Luka Bot Localization

This directory contains all translation files for the Luka bot using **Gettext/Babel .po files**.

## 📁 Directory Structure

```
locales/
├── README.md           # This file
├── babel.cfg           # Babel extraction config
├── messages.pot        # Translation template (auto-generated)
├── en/                 # English
│   └── LC_MESSAGES/
│       ├── messages.po # Source translations (EDIT THIS)
│       └── messages.mo # Compiled binary (auto-generated)
└── ru/                 # Russian
    └── LC_MESSAGES/
        ├── messages.po # Russian translations (EDIT THIS)
        └── messages.mo # Compiled binary (auto-generated)
```

## 🚀 Quick Start

### For Developers: Adding New Strings

1. **Use in code:**
   ```python
   from luka_bot.utils.i18n_helper import _, get_user_language
   
   lang = await get_user_language(user_id)
   text = _("my.new.key", lang, name="Value")
   ```

2. **Extract new strings:**
   ```bash
   pybabel extract \
     --input-dirs=luka_bot \
     --output-file=luka_bot/locales/messages.pot \
     --keywords=_ \
     --project=LukaBot
   ```

3. **Update .po files:**
   ```bash
   pybabel update \
     --input-file=luka_bot/locales/messages.pot \
     --output-dir=luka_bot/locales
   ```

4. **Edit translations** in `en/LC_MESSAGES/messages.po` and `ru/LC_MESSAGES/messages.po`

5. **Compile:**
   ```bash
   pybabel compile --directory=luka_bot/locales
   ```

6. **Restart bot**

### For Translators: Editing Translations

**Recommended Tool:** [Poedit](https://poedit.net/) (free, visual editor)

**Manual Editing:**
```gettext
# English (en/LC_MESSAGES/messages.po)
msgid "profile.title"
msgstr "👤 <b>Your Profile</b>"

# Russian (ru/LC_MESSAGES/messages.po)
msgid "profile.title"
msgstr "👤 <b>Ваш профиль</b>"
```

After editing, compile:
```bash
pybabel compile --directory=luka_bot/locales
```

## 🔑 Translation Keys

### Namespaces
- `onboarding.*` - First-time user experience
- `actions.*` - /start menu actions
- `chat.*` - Thread/conversation management
- `profile.*` - User profile & settings
- `tasks.*` - Task management (GTD)
- `reset.*` - Reset command
- `common.*` - Shared UI elements
- `keyboard.*` - Button labels
- `error.*` - Error messages
- `notification.*` - Success messages

### Placeholders

Strings can include `{placeholders}` for dynamic values:

```python
_("onboarding.welcome_title", "en", bot_name="Luka")
# Returns: "👋 Welcome to Luka!"
```

Common placeholders:
- `{bot_name}` - Bot's name (from settings)
- `{first_name}` - User's first name
- `{count}` - Number of items
- `{name}` - Generic name
- `{language}` - Language name
- `{date}` - Date string

## 📝 Formatting Rules

### HTML Markup
Telegram supports a subset of HTML in messages:

```html
<b>Bold text</b>
<i>Italic text</i>
<code>Monospace</code>
<a href="url">Link</a>
<pre>Preformatted</pre>
```

### Emoji
Use emoji freely! They work across all languages:
```
✅ ❌ 🔄 👋 💬 📋 🎯 etc.
```

### Special Characters
Some characters need escaping in Telegram HTML:
- `<` → `&lt;`
- `>` → `&gt;`
- `&` → `&amp;`

(The bot's `formatting.py` handles this automatically)

## 🌐 Supported Languages

| Code | Language | Status | Coverage |
|------|----------|--------|----------|
| `en` | English | ✅ Complete | 100% |
| `ru` | Russian | ✅ Complete | 100% |

Want to add a language? See [Adding New Languages](#adding-new-languages) below.

## 🔧 Advanced Usage

### Adding New Languages

1. **Initialize new locale:**
   ```bash
   pybabel init \
     --input-file=luka_bot/locales/messages.pot \
     --output-dir=luka_bot/locales \
     --locale=es
   ```

2. **Translate strings** in `es/LC_MESSAGES/messages.po`

3. **Compile:**
   ```bash
   pybabel compile --directory=luka_bot/locales
   ```

4. **Update code** to support new language:
   - Add to `UserProfile.language` validation
   - Add to `/profile` language selection menu
   - Add to default commands setup

### Updating Translations from Code Changes

When code changes and new strings are added:

```bash
# 1. Extract new strings
pybabel extract --input-dirs=luka_bot --output-file=luka_bot/locales/messages.pot --keywords=_

# 2. Update all .po files (preserves existing translations)
pybabel update --input-file=luka_bot/locales/messages.pot --output-dir=luka_bot/locales

# 3. Look for "#, fuzzy" comments - these need review
# 4. Translate new msgid entries
# 5. Compile
pybabel compile --directory=luka_bot/locales
```

### Translation Status

Check for untranslated strings:
```bash
# Count missing translations
msgfmt --statistics luka_bot/locales/ru/LC_MESSAGES/messages.po
```

## 🐛 Troubleshooting

### Bot shows key instead of translation
- ❌ **Issue:** Missing or incorrect key
- ✅ **Fix:** Check spelling in code and .po file
- ✅ **Verify:** Run `pybabel compile` after editing .po files

### Translation not updating
- ❌ **Issue:** `.mo` file not recompiled
- ✅ **Fix:** Run `pybabel compile --directory=luka_bot/locales`
- ✅ **Restart:** Bot loads translations at startup

### New strings not appearing
- ❌ **Issue:** Not extracted with pybabel
- ✅ **Fix:** Ensure using `_()` function in code
- ✅ **Extract:** Run `pybabel extract ...` command

### Formatting issues
- ❌ **Issue:** Placeholders not matching
- ✅ **Fix:** Ensure `{placeholder}` names are identical in code and .po
- ✅ **Example:** `{count}` in code must be `{count}` in translation

## 📚 Resources

- **Babel Docs:** https://babel.pocoo.org/
- **Gettext Manual:** https://www.gnu.org/software/gettext/manual/
- **Poedit:** https://poedit.net/
- **Aiogram i18n:** https://docs.aiogram.dev/en/latest/utils/i18n.html

---

**Questions?** Check the main docs at `docs/I18N_PO_MIGRATION_COMPLETE.md`

