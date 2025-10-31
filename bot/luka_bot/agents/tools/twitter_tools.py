"""
Twitter tools for Luka Bot - Knowledge Base Gathering System (Phase 1).

This module provides Twitter account info retrieval for content analysis.
Phase 1: Stub implementation with mock data
Phase 2+: Full Twitter API integration for content curation workflow

Related to: docs/feature/knowledge-base-gathering-system.md
"""
from typing import Optional
from urllib.parse import urlparse
from pydantic import Field
from pydantic_ai.tools import Tool
from loguru import logger

from luka_bot.agents.context import ConversationContext


def _extract_twitter_handle(url_or_handle: str) -> Optional[str]:
	"""
	Extract Twitter handle from a URL or plain handle.

	Supports:
	- twitter.com/username
	- x.com/username
	- @username
	- username

	Args:
		url_or_handle: Twitter URL, @handle, or plain handle

	Returns:
		Cleaned handle without @ or None if invalid
	"""
	try:
		# Remove @ if present
		cleaned = url_or_handle.strip().lstrip('@')

		# Check if it's a URL
		if cleaned.startswith('http://') or cleaned.startswith('https://'):
			parsed = urlparse(cleaned)
			host = (parsed.netloc or '').lower()

			# Support both twitter.com and x.com
			if 'twitter.com' in host or 'x.com' in host:
				# Extract handle from path (e.g., /username or /username/status/123)
				path_parts = parsed.path.strip('/').split('/')
				if path_parts and path_parts[0]:
					return path_parts[0]
		else:
			# Plain handle - validate it's alphanumeric + underscore
			if cleaned and cleaned.replace('_', '').isalnum():
				return cleaned

		return None
	except Exception as e:
		logger.warning(f"Error extracting Twitter handle from '{url_or_handle}': {e}")
		return None


async def get_twitter_account_info(
	ctx: ConversationContext,
	url_or_handle: str = Field(description="Twitter profile URL or handle (e.g., @username, https://twitter.com/username)")
) -> str:
	"""
	Get Twitter account information for content analysis and knowledge base curation.

	Phase 1 (Current): Returns stub/mock data for testing workflow
	Phase 2+: Full Twitter API integration with:
	- Account metadata (followers, bio, verification status)
	- Recent tweets analysis
	- Content quality scoring
	- Usefulness evaluation for knowledge base

	Product-oriented approach:
	1. Return account info + content preview
	2. Evaluate account credibility (followers, verification, etc.)
	3. Suggest if account is worthy of knowledge base inclusion
	4. Store analysis in context for moderation workflow

	Args:
		ctx: Conversation context with user info
		url_or_handle: Twitter URL or handle

	Returns:
		Account information and content analysis (stub data for Phase 1)
	"""
	try:
		from luka_bot.utils.i18n_helper import _

		# Get user language from context
		user_lang = ctx.metadata.get('language', 'en') if hasattr(ctx, 'metadata') and isinstance(ctx.metadata, dict) else 'en'

		handle = _extract_twitter_handle(url_or_handle)
		if not handle:
			return _("twitter.error_invalid_handle", user_lang, handle=url_or_handle)

		logger.info(f"🐦 Twitter account info requested for @{handle} by user {ctx.user_id}")

		# PHASE 1: STUB DATA
		# Phase 2+: Replace with actual Twitter API calls
		# api_client = TwitterAPI(bearer_token=settings.TWITTER_BEARER_TOKEN)
		# account_info = await api_client.get_user_by_username(handle)
		# recent_tweets = await api_client.get_user_tweets(account_info['id'], max_results=10)

		stub_account_info = {
			'handle': handle,
			'display_name': f"{handle.capitalize()} (Sample Account)",
			'bio': "This is a stub bio for testing. Phase 2 will include real Twitter API data.",
			'followers': 12345,
			'following': 678,
			'verified': False,
			'created_at': '2020-01-15',
			'tweet_count': 1523,
			'profile_image': 'https://via.placeholder.com/150',
		}

		# Store full account info in context for downstream processing
		ctx.metadata['twitter_account_handle'] = handle
		ctx.metadata['twitter_account_info'] = stub_account_info

		# Calculate stub usefulness score (Phase 1)
		# Phase 2+: Real scoring based on followers, engagement, content quality
		usefulness_score = 7  # Mock score for testing
		ctx.metadata['twitter_usefulness_score'] = usefulness_score

		# Build user-facing response
		response_lines = [
			_("twitter.account_info_header", user_lang),
			"",
			f"**{_('twitter.display_name', user_lang)}** {stub_account_info['display_name']}",
			f"**{_('twitter.handle', user_lang)}** @{handle}",
			f"**{_('twitter.bio', user_lang)}** {stub_account_info['bio']}",
			"",
			f"**{_('twitter.stats_header', user_lang)}**",
			f"👥 {_('twitter.followers', user_lang)} {stub_account_info['followers']:,}",
			f"➡️ {_('twitter.following', user_lang)} {stub_account_info['following']:,}",
			f"✍️ {_('twitter.tweets', user_lang)} {stub_account_info['tweet_count']:,}",
			f"📅 {_('twitter.created', user_lang)} {stub_account_info['created_at']}",
			"",
			f"**{_('twitter.usefulness_score_header', user_lang)}**",
			f"📊 {_('twitter.usefulness_score', user_lang)} {usefulness_score}/10",
			"",
			_("twitter.phase1_notice", user_lang),
			"",
			_("twitter.actions_header", user_lang),
			_("twitter.action_add_kb", user_lang),
			_("twitter.action_analyze_tweets", user_lang),
			_("twitter.action_monitor", user_lang),
		]

		logger.info(f"✅ Processed Twitter account info for @{handle}: usefulness={usefulness_score}/10")

		return "\n".join(response_lines)

	except Exception as e:
		from luka_bot.utils.i18n_helper import _
		user_lang = 'en'
		try:
			user_lang = ctx.metadata.get('language', 'en') if hasattr(ctx, 'metadata') and isinstance(ctx.metadata, dict) else 'en'
		except Exception:
			pass
		logger.warning(f"Twitter account info tool error: {e}")
		return _("twitter.error_generic", user_lang, error=str(e))


def get_tools():
	"""Expose Tool objects for the agent."""
	return [
		Tool(
			get_twitter_account_info,
			name="get_twitter_account_info",
			description=(
				"Get Twitter/X account information including profile, stats, and content quality analysis. "
				"Use when users share a Twitter profile link or ask about a Twitter account. "
				"Helps evaluate if account content is worthy of knowledge base inclusion."
			)
		)
	]


def get_prompt_description() -> str:
	"""Return system prompt description for Twitter tools."""
	return (
		"You can analyze Twitter/X accounts when users share profile links or handles. "
		"Use the get_twitter_account_info tool to evaluate account credibility and content quality. "
		"This is part of the Knowledge Base Gathering System for curating valuable content sources."
	)
