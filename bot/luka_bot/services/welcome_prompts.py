"""
Welcome prompts service - Lazy thread creation.

Provides random inspiring prompts for new conversations.
ChatGPT-style user experience.
"""
import random
from typing import Dict, List


# Welcome prompts by language
WELCOME_PROMPTS: Dict[str, List[str]] = {
    "en": [
        "What would you like to explore today? 🤔",
        "I'm here to help! What's on your mind? 💭",
        "Ask me anything - let's start a conversation! 💬",
        "What can I help you with today? ✨",
        "Ready to chat! What topic interests you? 🚀",
        "Let's dive in! What would you like to discuss? 🌟",
        "I'm all ears! What question do you have? 👂",
        "Fire away! What would you like to know? 🎯",
        "Let's get started! What's your question? 💡",
        "How can I assist you today? 🤝",
    ],
    "ru": [
        "Что бы вы хотели узнать сегодня? 🤔",
        "Я здесь, чтобы помочь! О чём думаете? 💭",
        "Спрашивайте что угодно - начнём разговор! 💬",
        "Чем могу помочь сегодня? ✨",
        "Готов к общению! Какая тема вас интересует? 🚀",
        "Давайте начнём! Что хотите обсудить? 🌟",
        "Весь внимание! Какой у вас вопрос? 👂",
        "Давайте! Что хотите узнать? 🎯",
        "Начнём! Какой ваш вопрос? 💡",
        "Как я могу помочь вам сегодня? 🤝",
    ],
}


def get_random_welcome_prompt(language: str = "en") -> str:
    """
    Get a random welcome prompt for the given language.
    
    Args:
        language: Language code (en, ru)
        
    Returns:
        Random welcome prompt string
    """
    # Fallback to English if language not supported
    lang = language if language in WELCOME_PROMPTS else "en"
    
    prompts = WELCOME_PROMPTS[lang]
    return random.choice(prompts)


def get_welcome_message(first_name: str = "", language: str = "en") -> str:
    """
    Get a complete welcome message with greeting and random prompt.
    
    Args:
        first_name: User's first name
        language: Language code (en, ru)
        
    Returns:
        Complete welcome message
    """
    # Greetings by language
    greetings = {
        "en": f"👋 Welcome{f', {first_name}' if first_name else ''}!\n\n",
        "ru": f"👋 Добро пожаловать{f', {first_name}' if first_name else ''}!\n\n",
    }
    
    lang = language if language in greetings else "en"
    greeting = greetings[lang]
    prompt = get_random_welcome_prompt(lang)
    
    return f"{greeting}{prompt}"


def get_new_thread_prompt(language: str = "en") -> str:
    """
    Get prompt specifically for starting a new thread.
    
    Similar to welcome prompt but without greeting.
    
    Args:
        language: Language code (en, ru)
        
    Returns:
        Prompt for new thread
    """
    return get_random_welcome_prompt(language)

