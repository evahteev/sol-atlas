from __future__ import annotations
from typing import List
from aiogram.types import Message
from loguru import logger
import re

# Import bot instance
from luka_bot.core.loader import bot

# Telegram hard limit
TELEGRAM_LIMIT = 4096

# Flag to control collapsible formatting for "Found X messages" sections
# Set to False to disable expandable blockquotes
COLLAPSE_FOUND_MESSAGES = True


def apply_collapsible_formatting(text: str) -> str:
	"""
	Apply collapsible blockquote formatting to "Found X messages" sections.
	
	This transforms knowledge base search results into expandable sections:
	- Detects pattern: "━━━━...\\n📚 Found X messages (showing Y samples)\\n..."
	- Wraps entire section (header + samples) in <blockquote expandable> tags
	- Makes "📚 Found X messages (showing Y samples)" the clickable expand/collapse header
	
	Applied AFTER LLM generation, so LLM never sees HTML tags and won't
	generate unsupported tags like <ol>, <ul>, <li>.
	
	Args:
	    text: The final bot response text
	
	Returns:
	    Text with collapsible formatting applied (if feature enabled)
	"""
	if not COLLAPSE_FOUND_MESSAGES:
		return text
	
	# Pattern to match KB results section:
	# ━━━━━━━━━━━━━━━━━━━━
	# 📚 Found 15 messages (showing 5 samples)
	# <samples>
	# ━━━━━━━━━━━━━━━━━━━━
	
	# Use regex to find and transform the section
	# Match: separator line + "Found X messages (showing Y samples)" + content + separator
	pattern = r'(━{20,}\n)(📚 Found \d+ [^\n]+ )\(showing (\d+ samples)\)\n(.*?)(━{20,})'
	
	def replace_func(match):
		separator_start = match.group(1)  # ━━━━━━━━━━━━━━━━━━━━\n
		found_header = match.group(2)     # 📚 Found 15 messages 
		showing_text = match.group(3)     # 5 samples
		samples_content = match.group(4)  # The actual message cards
		separator_end = match.group(5)    # ━━━━━━━━━━━━━━━━━━━━
		
		# Reconstruct with expandable blockquote starting from "📚 Found..." line
		# "(showing X samples)" goes on second line
		return (
			f"{separator_start}"
			f"<blockquote expandable>{found_header}\n"
			f"(showing {showing_text})\n"
			f"{samples_content}"
			f"</blockquote>\n"
			f"{separator_end}"
		)
	
	# Apply transformation (DOTALL flag to match across newlines)
	transformed = re.sub(pattern, replace_func, text, flags=re.DOTALL)
	
	return transformed


def split_long_message(text: str, max_length: int = TELEGRAM_LIMIT) -> List[str]:
	"""Split text into parts within Telegram limit, preferring newline boundaries."""
	if not text:
		return [""]
	
	# Fast path
	if len(text) <= max_length:
		return [text]
	
	parts: List[str] = []
	start = 0
	while start < len(text):
		end = min(start + max_length, len(text))
		# Prefer split on last newline within window
		slice_chunk = text[start:end]
		newline_pos = slice_chunk.rfind("\n")
		if newline_pos > 200:  # avoid tiny tail when possible
			end = start + newline_pos
			parts.append(text[start:end])
			start = end + 1
		else:
			parts.append(text[start:end])
			start = end
	return parts


async def edit_and_send_parts(initial_message: Message, html_text: str) -> None:
	"""Edit the initial message with first part and send remaining parts as new messages."""
	# Apply collapsible formatting BEFORE splitting/sending
	html_text = apply_collapsible_formatting(html_text)
	
	parts = split_long_message(html_text)
	first = parts[0] if parts else ""
	try:
		await initial_message.edit_text(text=first or "No response", parse_mode="HTML")
	except Exception as e:
		logger.debug(f"edit_and_send_parts: failed to edit initial message: {e}")
		# fallback to sending a new message
		await bot.send_message(chat_id=initial_message.chat.id, text=first or "No response", parse_mode="HTML")
	
	# Send the rest
	for idx, part in enumerate(parts[1:], start=2):
		try:
			await bot.send_message(chat_id=initial_message.chat.id, text=part, parse_mode="HTML")
		except Exception as e:
			logger.warning(f"edit_and_send_parts: failed to send part {idx}: {e}")


async def send_long_message(chat_id: int, html_text: str) -> List[Message]:
	"""Send a long HTML message split into multiple Telegram messages."""
	# Apply collapsible formatting BEFORE splitting/sending
	html_text = apply_collapsible_formatting(html_text)
	
	parts = split_long_message(html_text)
	sent: List[Message] = []
	for idx, part in enumerate(parts, start=1):
		try:
			m = await bot.send_message(chat_id=chat_id, text=part, parse_mode="HTML")
			sent.append(m)
		except Exception as e:
			logger.warning(f"send_long_message: failed to send part {idx}: {e}")
	return sent
