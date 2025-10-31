"""
Content Detection Service for Knowledge Base Gathering System.

This service detects various content types from group messages including:
- Twitter/X links (profile URLs, tweet URLs)
- Telegram channel links
- Website URLs
- Attachments (PDF, DOC, images, videos)
- Forwarded messages

Phase 1: Basic content type detection
Phase 2+: Advanced content extraction and analysis

Related to: docs/feature/knowledge-base-gathering-system.md
"""
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlparse
from aiogram.types import Message
from loguru import logger


@dataclass
class DetectedContent:
	"""Represents detected content in a message."""
	content_type: str  # "twitter_profile", "twitter_tweet", "telegram_channel", "website", "attachment", "forwarded"
	content_url: Optional[str] = None
	source_platform: Optional[str] = None  # "twitter", "telegram", "web", "direct"
	metadata: Optional[Dict[str, Any]] = None  # Additional context
	raw_text: Optional[str] = None  # Original message text
	attachment_info: Optional[Dict[str, Any]] = None  # File info for attachments


class ContentDetectionService:
	"""Service for detecting content types in group messages."""

	# URL patterns for various platforms
	TWITTER_PROFILE_PATTERN = re.compile(
		r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/?$',
		re.IGNORECASE
	)

	TWITTER_TWEET_PATTERN = re.compile(
		r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)/status/(\d+)',
		re.IGNORECASE
	)

	TELEGRAM_CHANNEL_PATTERN = re.compile(
		r'(?:https?://)?(?:www\.)?t\.me/([a-zA-Z0-9_]+)',
		re.IGNORECASE
	)

	TELEGRAM_MESSAGE_PATTERN = re.compile(
		r'(?:https?://)?(?:www\.)?t\.me/([a-zA-Z0-9_]+)/(\d+)',
		re.IGNORECASE
	)

	# Supported attachment types for knowledge base
	SUPPORTED_DOCUMENT_TYPES = {
		'application/pdf',
		'application/msword',
		'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
		'text/plain',
		'application/vnd.ms-excel',
		'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
	}

	SUPPORTED_IMAGE_TYPES = {
		'image/jpeg',
		'image/png',
		'image/gif',
		'image/webp',
	}

	def __init__(self):
		"""Initialize the content detection service."""
		logger.info("📡 ContentDetectionService initialized")

	async def detect_content(self, message: Message) -> List[DetectedContent]:
		"""
		Detect all content types in a message.

		Args:
			message: Telegram message to analyze

		Returns:
			List of detected content items
		"""
		detected_items: List[DetectedContent] = []

		message_text = message.text or message.caption or ""

		# 1. Check for forwarded content
		if message.forward_origin:
			forwarded_content = self._detect_forwarded_content(message)
			if forwarded_content:
				detected_items.append(forwarded_content)

		# 2. Check for attachments
		if message.document or message.photo or message.video:
			attachment_content = await self._detect_attachment(message)
			if attachment_content:
				detected_items.append(attachment_content)

		# 3. Check for URLs in text
		if message_text:
			url_contents = self._detect_urls(message_text)
			detected_items.extend(url_contents)

		if detected_items:
			logger.info(f"📋 Detected {len(detected_items)} content item(s) in message")
			for item in detected_items:
				logger.debug(f"  - {item.content_type}: {item.content_url or 'N/A'}")

		return detected_items

	def _detect_urls(self, text: str) -> List[DetectedContent]:
		"""Detect and classify URLs in message text."""
		detected = []

		# Check for Twitter tweet URLs
		tweet_matches = self.TWITTER_TWEET_PATTERN.findall(text)
		for match in tweet_matches:
			username, tweet_id = match
			detected.append(DetectedContent(
				content_type="twitter_tweet",
				content_url=f"https://twitter.com/{username}/status/{tweet_id}",
				source_platform="twitter",
				metadata={"username": username, "tweet_id": tweet_id}
			))

		# Check for Twitter profile URLs (only if no tweet URLs found in same text)
		if not tweet_matches:
			profile_matches = self.TWITTER_PROFILE_PATTERN.findall(text)
			for username in profile_matches:
				# Skip if it looks like a common word (basic heuristic)
				if len(username) > 2:
					detected.append(DetectedContent(
						content_type="twitter_profile",
						content_url=f"https://twitter.com/{username}",
						source_platform="twitter",
						metadata={"username": username}
					))

		# Check for Telegram message URLs
		tg_msg_matches = self.TELEGRAM_MESSAGE_PATTERN.findall(text)
		for match in tg_msg_matches:
			channel, message_id = match
			detected.append(DetectedContent(
				content_type="telegram_message",
				content_url=f"https://t.me/{channel}/{message_id}",
				source_platform="telegram",
				metadata={"channel": channel, "message_id": message_id}
			))

		# Check for Telegram channel URLs (only if no message URLs found)
		if not tg_msg_matches:
			tg_channel_matches = self.TELEGRAM_CHANNEL_PATTERN.findall(text)
			for channel in tg_channel_matches:
				detected.append(DetectedContent(
					content_type="telegram_channel",
					content_url=f"https://t.me/{channel}",
					source_platform="telegram",
					metadata={"channel": channel}
				))

		# Check for generic website URLs (catch-all for other URLs)
		# Simple URL pattern - will match most http/https URLs
		url_pattern = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)
		urls = url_pattern.findall(text)

		# Filter out URLs we've already detected
		detected_urls = {item.content_url for item in detected}
		for url in urls:
			if url not in detected_urls:
				# Parse URL to get domain
				try:
					parsed = urlparse(url)
					domain = parsed.netloc.lower()

					# Skip if it's a platform we already handle
					if any(platform in domain for platform in ['twitter.com', 'x.com', 't.me', 'telegram']):
						continue

					detected.append(DetectedContent(
						content_type="website",
						content_url=url,
						source_platform="web",
						metadata={"domain": domain}
					))
				except Exception as e:
					logger.debug(f"Failed to parse URL {url}: {e}")

		return detected

	async def _detect_attachment(self, message: Message) -> Optional[DetectedContent]:
		"""Detect and classify message attachments."""

		# Handle documents (PDF, DOC, etc.)
		if message.document:
			doc = message.document
			mime_type = doc.mime_type or ""

			if mime_type in self.SUPPORTED_DOCUMENT_TYPES:
				return DetectedContent(
					content_type="attachment",
					source_platform="direct",
					metadata={
						"attachment_type": "document",
						"file_name": doc.file_name,
						"file_size": doc.file_size,
						"mime_type": mime_type
					},
					attachment_info={
						"file_id": doc.file_id,
						"file_unique_id": doc.file_unique_id,
						"file_name": doc.file_name,
						"file_size": doc.file_size,
						"mime_type": mime_type
					},
					raw_text=message.caption
				)

		# Handle photos
		if message.photo:
			# Get largest photo size
			largest_photo = max(message.photo, key=lambda p: p.file_size or 0)

			return DetectedContent(
				content_type="attachment",
				source_platform="direct",
				metadata={
					"attachment_type": "image",
					"file_size": largest_photo.file_size,
					"mime_type": "image/jpeg"  # Telegram photos are usually JPEG
				},
				attachment_info={
					"file_id": largest_photo.file_id,
					"file_unique_id": largest_photo.file_unique_id,
					"width": largest_photo.width,
					"height": largest_photo.height,
					"file_size": largest_photo.file_size
				},
				raw_text=message.caption
			)

		# Handle videos
		if message.video:
			video = message.video

			return DetectedContent(
				content_type="attachment",
				source_platform="direct",
				metadata={
					"attachment_type": "video",
					"file_name": video.file_name,
					"file_size": video.file_size,
					"mime_type": video.mime_type or "video/mp4",
					"duration": video.duration
				},
				attachment_info={
					"file_id": video.file_id,
					"file_unique_id": video.file_unique_id,
					"width": video.width,
					"height": video.height,
					"file_size": video.file_size,
					"duration": video.duration
				},
				raw_text=message.caption
			)

		return None

	def _detect_forwarded_content(self, message: Message) -> Optional[DetectedContent]:
		"""Detect forwarded message content."""
		if not message.forward_origin:
			return None

		forward_origin = message.forward_origin
		metadata = {"forward_date": message.forward_date.isoformat() if message.forward_date else None}

		# Channel forwarded message
		if hasattr(forward_origin, 'chat') and forward_origin.chat:
			chat = forward_origin.chat
			metadata.update({
				"from_chat_id": chat.id,
				"from_chat_title": chat.title,
				"from_chat_username": chat.username,
				"from_chat_type": chat.type
			})

			# If forwarded from channel, include message link if available
			if chat.username:
				content_url = f"https://t.me/{chat.username}"
				if hasattr(forward_origin, 'message_id'):
					content_url += f"/{forward_origin.message_id}"

				return DetectedContent(
					content_type="forwarded",
					content_url=content_url,
					source_platform="telegram",
					metadata=metadata,
					raw_text=message.text or message.caption
				)

		# User forwarded message
		if hasattr(forward_origin, 'sender_user') and forward_origin.sender_user:
			user = forward_origin.sender_user
			metadata.update({
				"from_user_id": user.id,
				"from_user_name": user.full_name,
				"from_user_username": user.username
			})

		return DetectedContent(
			content_type="forwarded",
			source_platform="telegram",
			metadata=metadata,
			raw_text=message.text or message.caption
		)

	def is_content_worthy_of_kb(self, content: DetectedContent) -> bool:
		"""
		Quick heuristic check if content is potentially worthy of knowledge base.

		Phase 1: Simple rules based on content type
		Phase 2+: ML-based filtering

		Args:
			content: Detected content item

		Returns:
			True if content should be analyzed for KB inclusion
		"""
		# Phase 1: All detected content is potentially worthy
		# In Phase 2, we can add filters like:
		# - Minimum file size for documents
		# - Domain reputation for websites
		# - Account follower count for Twitter

		worthy_types = {
			"twitter_profile",
			"twitter_tweet",
			"telegram_channel",
			"telegram_message",
			"website",
			"attachment",
			"forwarded"
		}

		return content.content_type in worthy_types


# Singleton instance
_content_detection_service: Optional[ContentDetectionService] = None


async def get_content_detection_service() -> ContentDetectionService:
	"""Get or create the content detection service instance."""
	global _content_detection_service
	if _content_detection_service is None:
		_content_detection_service = ContentDetectionService()
	return _content_detection_service
