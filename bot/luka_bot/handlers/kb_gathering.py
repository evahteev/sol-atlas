"""
Knowledge Base Gathering handler for group messages.

Automatically detects valuable content in group messages and prompts
users to add it to the knowledge base with moderation workflow.

Phase 1: Basic content detection with Twitter profile analysis
Phase 2+: Full multi-platform support with Camunda workflows

Related to: docs/feature/knowledge-base-gathering-system.md
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import ChatMemberUpdatedFilter
from loguru import logger

from luka_bot.services.content_detection_service import get_content_detection_service
from luka_bot.services.content_router_service import get_content_router_service
from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.utils.i18n_helper import _, get_user_language

router = Router()


async def process_kb_gathering(message: Message, group_id: int, user_id: int, language: str = "en"):
	"""
	Process message for knowledge base gathering.

	This function is called from group_messages handler to analyze
	content and prompt for KB addition.

	Args:
		message: Telegram message
		group_id: Group ID
		user_id: User ID
		language: User's language preference
	"""
	try:
		# Get services
		detection_service = await get_content_detection_service()
		router_service = await get_content_router_service()

		# Detect content in message
		detected_contents = await detection_service.detect_content(message)

		if not detected_contents:
			# No interesting content found
			return

		logger.info(f"📋 KB Gathering: Found {len(detected_contents)} content item(s) in group {group_id}")

		# Process each detected content item
		for content in detected_contents:
			# Check if content is worthy of analysis
			if not detection_service.is_content_worthy_of_kb(content):
				logger.debug(f"⏭️ Skipping content type: {content.content_type}")
				continue

			# Send "analyzing" notification
			analyzing_msg = await message.reply(
				_("kb_gathering.analyzing_content", language),
				parse_mode="HTML"
			)

			try:
				# Route content to appropriate tool for analysis
				analysis_result = await router_service.route_content(
					content=content,
					message=message,
					user_id=user_id,
					group_id=group_id,
					language=language
				)

				# Delete analyzing message
				try:
					await analyzing_msg.delete()
				except Exception:
					pass

				if not analysis_result:
					logger.warning(f"⚠️ No analysis result for content type: {content.content_type}")
					continue

				# Send analysis result
				await message.reply(analysis_result, parse_mode="HTML")

				# Check if we should prompt for KB addition
				# For Phase 1, we'll use a simple heuristic from metadata
				# Phase 2 will use proper scoring from analysis
				usefulness_score = 7  # Stub score for Phase 1

				# TODO: Extract real score from analysis_result or context
				# For now, we'll parse it from the message (hacky but works for Phase 1)
				# In Phase 2, the router will return structured data

				should_prompt = await router_service.should_prompt_for_kb_addition(
					content=content,
					usefulness_score=usefulness_score
				)

				if should_prompt:
					# Create prompt message with inline keyboard
					prompt_text = await router_service.format_kb_prompt_message(
						content=content,
						analysis_result=analysis_result,
						usefulness_score=usefulness_score,
						language=language
					)

					keyboard = router_service.create_kb_addition_keyboard(
						content=content,
						usefulness_score=usefulness_score,
						language=language
					)

					await message.reply(
						prompt_text,
						reply_markup=keyboard,
						parse_mode="Markdown"
					)

					logger.info(f"✅ Prompted user for KB addition: {content.content_type}")

			except Exception as e:
				logger.error(f"❌ Error processing content: {e}", exc_info=True)
				# Delete analyzing message on error
				try:
					await analyzing_msg.delete()
				except Exception:
					pass

	except Exception as e:
		logger.error(f"❌ Error in KB gathering: {e}", exc_info=True)


@router.callback_query(F.data.startswith("kb_add:"))
async def handle_kb_addition_callback(callback: CallbackQuery):
	"""
	Handle KB addition confirmation/cancellation buttons.

	Callback data format: kb_add:{content_type}:{action}:{url_hash}
	"""
	try:
		user_id = callback.from_user.id
		data_parts = callback.data.split(":")

		if len(data_parts) < 3:
			await callback.answer("❌ Invalid callback data", show_alert=True)
			return

		content_type = data_parts[1]
		action = data_parts[2]

		# Get user language
		lang = await get_user_language(user_id)

		if action == "yes":
			# User confirmed - start submission process
			# Phase 1: Just acknowledge
			# Phase 2: Create Camunda process instance

			# For Phase 1, generate a stub submission ID
			import time
			submission_id = int(time.time()) % 100000

			await callback.message.edit_text(
				_("kb_gathering.confirmed_submission", lang, submission_id=submission_id),
				parse_mode="HTML"
			)

			await callback.answer("✅ Submitted!", show_alert=False)

			logger.info(f"✅ KB submission confirmed by user {user_id}, type={content_type}")

		elif action == "no":
			# User cancelled - just acknowledge
			await callback.message.edit_text(
				_("kb_gathering.cancelled", lang),
				parse_mode="HTML"
			)

			await callback.answer("❌ Cancelled", show_alert=False)

			logger.info(f"❌ KB submission cancelled by user {user_id}, type={content_type}")

		else:
			await callback.answer(f"⚠️ Unknown action: {action}", show_alert=True)

	except Exception as e:
		logger.error(f"❌ Error handling KB callback: {e}", exc_info=True)
		await callback.answer("❌ Error processing action", show_alert=True)
