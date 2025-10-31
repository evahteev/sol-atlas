"""
Thread settings keyboards - Phase 4.

Inline keyboards for configuring thread-specific settings:
- Model/Provider selection
- System prompt customization
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_thread_settings_menu(thread_id: str) -> InlineKeyboardMarkup:
    """
    Get main thread settings menu.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        Inline keyboard with settings options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🤖 Change Model/Provider",
                callback_data=f"settings_model:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="💭 Custom System Prompt",
                callback_data=f"settings_prompt:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Reset to Defaults",
                callback_data=f"settings_reset:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Close",
                callback_data=f"settings_close:{thread_id}"
            )
        ],
    ])
    return keyboard


def get_provider_selection_menu(thread_id: str) -> InlineKeyboardMarkup:
    """
    Get LLM provider selection menu.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        Inline keyboard with provider options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🦙 Ollama (Local)",
                callback_data=f"provider_ollama:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 OpenAI (Coming Soon)",
                callback_data=f"provider_openai:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🧠 Anthropic (Coming Soon)",
                callback_data=f"provider_anthropic:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Back",
                callback_data=f"settings_back:{thread_id}"
            )
        ],
    ])
    return keyboard


def get_model_selection_menu(thread_id: str, provider: str) -> InlineKeyboardMarkup:
    """
    Get model selection menu for a specific provider.
    
    Args:
        thread_id: Thread ID
        provider: Provider name (ollama, openai, etc.)
        
    Returns:
        Inline keyboard with model options
    """
    if provider == "ollama":
        models = [
            ("gpt-oss", "GPT OSS (Default)"),
            ("llama3.2", "Llama 3.2"),
            ("llama3", "Llama 3"),
            ("mistral", "Mistral"),
            ("codellama", "Code Llama"),
        ]
    elif provider == "openai":
        models = [
            ("gpt-4", "GPT-4 (CS)"),
            ("gpt-4-turbo", "GPT-4 Turbo (CS)"),
            ("gpt-3.5-turbo", "GPT-3.5 Turbo (CS)"),
        ]
    else:
        models = [
            ("claude-3", "Claude 3 (CS)"),
        ]
    
    keyboard_rows = []
    for model_id, model_name in models:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=model_name,
                callback_data=f"model_{provider}_{model_id}:{thread_id}"
            )
        ])
    
    # Add back button
    keyboard_rows.append([
        InlineKeyboardButton(
            text="◀️ Back to Providers",
            callback_data=f"settings_model:{thread_id}"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    return keyboard


def get_prompt_confirmation_menu(thread_id: str) -> InlineKeyboardMarkup:
    """
    Get confirmation menu after setting custom prompt.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        Inline keyboard with confirmation options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Keep This Prompt",
                callback_data=f"prompt_confirm:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Edit Again",
                callback_data=f"settings_prompt:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Use Default",
                callback_data=f"prompt_reset:{thread_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Close",
                callback_data=f"settings_close:{thread_id}"
            )
        ],
    ])
    return keyboard

