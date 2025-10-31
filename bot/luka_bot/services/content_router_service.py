"""
Content Router Service for Knowledge Base Gathering System.

This service routes detected content to appropriate analysis tools and
manages the workflow for adding content to the knowledge base.

Phase 1: Simple routing to Twitter tool with inline confirmation
Phase 2+: Full Camunda workflow integration with moderation

Related to: docs/feature/knowledge-base-gathering-system.md
"""
from typing import Optional, Dict, Any
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from luka_bot.services.content_detection_service import DetectedContent, get_content_detection_service
from luka_bot.agents.context import ConversationContext
from luka_bot.agents.tools.twitter_tools import get_twitter_account_info
from luka_bot.utils.i18n_helper import _


class ContentRouterService:
	"""Service for routing content to appropriate analysis tools."""

	def __init__(self):
		"""Initialize the content router service."""
		logger.info("🚦 ContentRouterService initialized")

	async def route_content(
		self,
		content: DetectedContent,
		message: Message,
		user_id: int,
		group_id: int,
		language: str = "en"
	) -> Optional[str]:
		"""
		Route content to appropriate analysis tool and return analysis result.

		Args:
			content: Detected content item
			message: Original Telegram message
			user_id: User who submitted the content
			group_id: Group where content was submitted
			language: User's language preference

		Returns:
			Analysis result text or None if routing failed
		"""
		logger.info(f"🚦 Routing content: type={content.content_type}, platform={content.source_platform}")

		try:
			# Route based on content type
			if content.content_type == "twitter_profile":
				return await self._route_twitter_profile(content, message, user_id, group_id, language)

			elif content.content_type == "twitter_tweet":
				# Phase 2: Analyze tweet content
				logger.info(f"📝 Twitter tweet detected (Phase 2): {content.content_url}")
				return None

			elif content.content_type == "telegram_channel":
				# Phase 2: Analyze Telegram channel
				logger.info(f"📝 Telegram channel detected (Phase 2): {content.content_url}")
				return None

			elif content.content_type == "website":
				# Phase 2: Analyze website content
				logger.info(f"📝 Website detected (Phase 2): {content.content_url}")
				return None

			elif content.content_type == "attachment":
				# Phase 2: Analyze attachment
				logger.info(f"📝 Attachment detected (Phase 2): {content.metadata}")
				return None

			elif content.content_type == "forwarded":
				# Phase 2: Analyze forwarded content
				logger.info(f"📝 Forwarded content detected (Phase 2): {content.content_url}")
				return None

			else:
				logger.warning(f"⚠️ Unknown content type: {content.content_type}")
				return None

		except Exception as e:
			logger.error(f"❌ Error routing content: {e}", exc_info=True)
			return None

	async def _route_twitter_profile(
		self,
		content: DetectedContent,
		message: Message,
		user_id: int,
		group_id: int,
		language: str
	) -> Optional[str]:
		"""Route Twitter profile to twitter_tools for analysis."""
		try:
			# Create conversation context
			ctx = ConversationContext(
				user_id=user_id,
				metadata={"language": language}
			)

			# Get Twitter account info using the tool
			username = content.metadata.get("username") if content.metadata else None
			if not username and content.content_url:
				# Extract from URL as fallback
				username = content.content_url

			logger.info(f"🐦 Analyzing Twitter account: {username}")

			# Call the Twitter tool directly
			analysis_result = await get_twitter_account_info(ctx, username)

			# Store analysis result in metadata for downstream processing
			usefulness_score = ctx.metadata.get("twitter_usefulness_score", 0)

			logger.info(f"✅ Twitter analysis complete: score={usefulness_score}/10")

			return analysis_result

		except Exception as e:
			logger.error(f"❌ Error analyzing Twitter profile: {e}", exc_info=True)
			return None

	async def should_prompt_for_kb_addition(self, content: DetectedContent, usefulness_score: int) -> bool:
		"""
		Determine if we should prompt user to add content to KB.

		Phase 1: Simple threshold check
		Phase 2+: ML-based decision with user preferences

		Args:
			content: Detected content
			usefulness_score: Calculated usefulness score (-10 to +10)

		Returns:
			True if we should prompt user
		"""
		# Threshold from PRD: score >= 7
		MIN_SCORE_THRESHOLD = 7

		if usefulness_score >= MIN_SCORE_THRESHOLD:
			logger.info(f"✅ Content meets threshold (score={usefulness_score} >= {MIN_SCORE_THRESHOLD})")
			return True
		else:
			logger.info(f"⏭️ Content below threshold (score={usefulness_score} < {MIN_SCORE_THRESHOLD})")
			return False

	def create_kb_addition_keyboard(
		self,
		content: DetectedContent,
		usefulness_score: int,
		language: str = "en"
	) -> InlineKeyboardMarkup:
		"""
		Create inline keyboard for KB addition confirmation.

		Phase 1: Simple Yes/No buttons
		Phase 2+: Advanced options (edit, skip, settings)

		Args:
			content: Detected content
			usefulness_score: Calculated usefulness score
			language: User's language

		Returns:
			Inline keyboard markup
		"""
		# Create callback data with content info
		callback_data_prefix = f"kb_add:{content.content_type}:"

		# Truncate URL for callback data (max 64 bytes)
		url_hash = hash(content.content_url or "") % 10000
		callback_yes = f"{callback_data_prefix}yes:{url_hash}"
		callback_no = f"{callback_data_prefix}no:{url_hash}"

		buttons = [
			[
				InlineKeyboardButton(
					text=_("kb_gathering.button_yes", language) if language == "ru" else "✅ Yes, Add to KB",
					callback_data=callback_yes
				),
				InlineKeyboardButton(
					text=_("kb_gathering.button_no", language) if language == "ru" else "❌ No, Skip",
					callback_data=callback_no
				)
			]
		]

		# Phase 2: Add "Edit Score" button for admins
		# buttons.append([
		#     InlineKeyboardButton(text="✏️ Edit Score", callback_data=f"{callback_data_prefix}edit:{url_hash}")
		# ])

		return InlineKeyboardMarkup(inline_keyboard=buttons)

	async def format_kb_prompt_message(
		self,
		content: DetectedContent,
		analysis_result: str,
		usefulness_score: int,
		language: str = "en"
	) -> str:
		"""
		Format the prompt message asking user to add content to KB.

		Args:
			content: Detected content
			analysis_result: Tool analysis result
			usefulness_score: Calculated score
			language: User's language

		Returns:
			Formatted message text
		"""
		# Build prompt message
		prompt_lines = [
			"",
			"━━━━━━━━━━━━━━━━━━━━",
			"",
			_("kb_gathering.prompt_header", language) if language == "ru" else "📚 **Add to Knowledge Base?**",
			"",
			_("kb_gathering.prompt_score", language, score=usefulness_score) if language == "ru"
				else f"**Usefulness Score:** {usefulness_score}/10",
			_("kb_gathering.prompt_potential_reward", language, reward=usefulness_score * 10) if language == "ru"
				else f"**Potential Reward:** {usefulness_score * 10} Atlas tokens",
			"",
			_("kb_gathering.prompt_question", language) if language == "ru"
				else "Would you like to submit this for moderation and add it to the knowledge base?",
		]

		return "\n".join(prompt_lines)


# Singleton instance
_content_router_service: Optional[ContentRouterService] = None


async def get_content_router_service() -> ContentRouterService:
	"""Get or create the content router service instance."""
	global _content_router_service
	if _content_router_service is None:
		_content_router_service = ContentRouterService()
	return _content_router_service
