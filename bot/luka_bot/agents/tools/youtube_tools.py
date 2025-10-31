from typing import Optional
from urllib.parse import urlparse, parse_qs
from pydantic import Field
from pydantic_ai.tools import Tool
from loguru import logger

from luka_bot.agents.context import ConversationContext
from luka_bot.core.config import settings  # added

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
	TranscriptsDisabled,
	NoTranscriptFound,
	VideoUnavailable,
	RequestBlocked,
	VideoUnplayable,
)


from googleapiclient.discovery import build
google_client_available = True


def _extract_video_id(video_url: str) -> Optional[str]:
	"""Extract YouTube video ID from a URL (supports youtube.com and youtu.be)."""
	try:
		parsed = urlparse(video_url)
		host = (parsed.netloc or '').lower()
		if 'youtube.com' in host:
			qs = parse_qs(parsed.query)
			vid = qs.get('v', [''])[0]
			return vid or None
		if 'youtu.be' in host:
			vid = parsed.path.lstrip('/')
			return vid or None
		return None
	except Exception:
		return None


def _get_video_info(video_id: str) -> Optional[dict]:
	"""Fetch video metadata using YouTube Data API if API key is configured."""
	api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
	if not api_key or not google_client_available:
		return None
	try:
		youtube = build('youtube', 'v3', developerKey=api_key)
		resp = youtube.videos().list(part='snippet,contentDetails', id=video_id).execute()
		items = resp.get('items') or []
		if not items:
			return None
		item = items[0]
		snippet = item.get('snippet', {})
		cd = item.get('contentDetails', {})
		return {
			'title': snippet.get('title', ''),
			'channel_title': snippet.get('channelTitle', ''),
			'published_at': snippet.get('publishedAt', ''),
			'duration': cd.get('duration', ''),
		}
	except Exception as e:
		logger.warning(f"YouTube API get_video_info failed: {e}")
		return None


async def get_youtube_transcript(
	ctx: ConversationContext,
	video_url: str = Field(description="YouTube video URL to get transcript from"),
	language: str = Field(default="en", description="Preferred transcript/caption language to retrieve (not the response language). Default is 'en'.")
) -> str:
	"""Fetch YouTube transcript using youtube-transcript-api without OAuth.
	
	Product-oriented approach:
	1. Return video info + short summary (≤500 chars) to user immediately
	2. Store full transcript in thread history for LLM context
	3. Prompt user about available actions (analyze, extract key points, etc.)
	
	- Parses the URL to video id
	- Tries requested language, then English, then any available
	- If YouTube Data API key is configured, includes basic video metadata
	"""
	try:
		from luka_bot.utils.i18n_helper import _
		
		# Get user language from context
		user_lang = ctx.metadata.get('language', 'en') if hasattr(ctx, 'metadata') and isinstance(ctx.metadata, dict) else 'en'
		
		video_id = _extract_video_id(video_url)
		if not video_id:
			return _("youtube.error_invalid_url", user_lang)
		
		# Optionally fetch video info (title, channel, published, duration)
		video_info = _get_video_info(video_id)
		
		languages_order = [language] if language else []
		if 'en' not in languages_order:
			languages_order.append('en')
		for code in ['en-US', 'en-GB']:
			if code not in languages_order:
				languages_order.append(code)
		
		segments = None
		last_error: Optional[str] = None
		api = YouTubeTranscriptApi()
		
		# Preferred: list transcripts and fetch
		try:
			try:
				transcript_list_obj = api.list_transcripts(video_id)  # newer API
			except AttributeError:
				transcript_list_obj = api.list(video_id)  # older API fallback
			
			transcript = None
			# Try manual first
			try:
				transcript = transcript_list_obj.find_manually_created_transcript(languages_order)
			except Exception:
				pass
			# Then generated
			if not transcript:
				try:
					transcript = transcript_list_obj.find_generated_transcript(languages_order)
				except Exception:
					pass
			# Then any preferred
			if not transcript:
				try:
					transcript = transcript_list_obj.find_transcript(languages_order)
				except Exception:
					pass
			# Fetch content
			if transcript:
				segments = transcript.fetch()
		except Exception as e:
			last_error = f"list/fetch failed: {e}"
			# Fallback to direct fetch
			try:
				segments = api.fetch(video_id, languages=languages_order)
			except Exception as ee:
				last_error = f"direct fetch failed: {ee}"
				segments = None
		
		if not segments:
			logger.info(f"YouTube transcript not available for {video_id}: {last_error}")
			return _("youtube.error_not_available", user_lang)
		
		# Concatenate segments
		if isinstance(segments, list):
			text = " ".join(s.get('text', '') for s in segments if isinstance(s, dict) and s.get('text'))
		else:
			# Some implementations return iterable custom objects
			parts = []
			for s in segments:
				try:
					parts.append(getattr(s, 'text', '') or '')
				except Exception:
					continue
			text = " ".join(p for p in parts if p)
		text = ' '.join(text.split())
		
		if not text:
			return _("youtube.error_empty", user_lang)
		
		# Store full transcript in context metadata for LLM access in subsequent turns
		# The full transcript will be available in ctx.metadata['youtube_full_transcript']
		# and should be stored as a system/assistant message in thread history by the caller
		ctx.metadata['youtube_full_transcript'] = text
		ctx.metadata['youtube_video_id'] = video_id
		if video_info:
			ctx.metadata['youtube_video_info'] = video_info
			ctx.metadata['youtube_video_title'] = video_info.get('title', '')
		
		# Build user-facing response: video info + short summary + action prompts
		response_lines = [_("youtube.processed_header", user_lang), ""]
		
		if video_info:
			response_lines.extend([
				f"{_('youtube.title', user_lang)} {video_info.get('title')}",
				f"{_('youtube.channel', user_lang)} {video_info.get('channel_title')}",
				f"{_('youtube.duration', user_lang)} {video_info.get('duration')}",
				"",
			])
		
		# Generate short summary in user's language using LLM
		try:
			from pydantic_ai import Agent
			from pydantic_ai.models.openai import OpenAIModel
			from luka_bot.core.config import settings
			
			# Language name mapping for better prompts
			lang_names = {'en': 'English', 'ru': 'Russian'}
			lang_name = lang_names.get(user_lang, user_lang)
			
			# Create a simple agent for summarization (using OpenAIModel for Ollama compatibility)
			summary_agent = Agent(
				OpenAIModel(settings.OLLAMA_MODEL_NAME, base_url=settings.OLLAMA_URL),
				system_prompt=f"You are a helpful assistant that creates brief video summaries in {lang_name}. Generate a concise summary (max 500 characters) that captures the main topic and key points. Respond ONLY in {lang_name}."
			)
			
			# Use first 2000 chars of transcript for summary generation
			excerpt = text[:2000] if len(text) > 2000 else text
			summary_prompt = f"Create a brief summary (max 500 characters) of this video transcript in {lang_name}:\n\n{excerpt}"
			
			result = await summary_agent.run(summary_prompt)
			summary_text = result.output
			
			# Fallback: trim if too long
			if len(summary_text) > 500:
				last_space = summary_text[:500].rfind(' ')
				if last_space > 400:
					summary_text = summary_text[:last_space] + '...'
				else:
					summary_text = summary_text[:500] + '...'
					
		except Exception as e:
			logger.warning(f"Failed to generate LLM summary, using excerpt: {e}")
			# Fallback: use first 500 chars of transcript
			summary_text = text[:500]
			if len(text) > 500:
				last_space = summary_text.rfind(' ')
				if last_space > 400:
					summary_text = summary_text[:last_space] + '...'
		
		response_lines.extend([
			_("youtube.preview_header", user_lang),
			summary_text,
			"",
			_("youtube.saved_to_history", user_lang),
			"",
			_("youtube.actions_header", user_lang),
			_("youtube.action_summarize", user_lang),
			_("youtube.action_analyze", user_lang),
			_("youtube.action_insights", user_lang),
			_("youtube.action_search", user_lang),
			_("youtube.action_ask", user_lang),
		])
		
		logger.info(f"✅ Processed YouTube transcript for {video_id}: {len(text)} chars, stored in context")
		
		return "\n".join(response_lines)
		
	except (TranscriptsDisabled, VideoUnavailable, VideoUnplayable, RequestBlocked) as e:
		from luka_bot.utils.i18n_helper import _
		user_lang = 'en'
		try:
			user_lang = ctx.metadata.get('language', 'en') if hasattr(ctx, 'metadata') and isinstance(ctx.metadata, dict) else 'en'
		except Exception:
			pass
		logger.warning(f"YouTube transcript unavailable due to restriction: {type(e).__name__}: {e}")
		return _("youtube.error_restricted", user_lang)
	except NoTranscriptFound as e:
		from luka_bot.utils.i18n_helper import _
		user_lang = 'en'
		try:
			user_lang = ctx.metadata.get('language', 'en') if hasattr(ctx, 'metadata') and isinstance(ctx.metadata, dict) else 'en'
		except Exception:
			pass
		logger.info(f"No transcript found for video: {e}")
		return _("youtube.error_no_transcript", user_lang)
	except Exception as e:
		from luka_bot.utils.i18n_helper import _
		user_lang = 'en'
		try:
			user_lang = ctx.metadata.get('language', 'en') if hasattr(ctx, 'metadata') and isinstance(ctx.metadata, dict) else 'en'
		except Exception:
			pass
		logger.warning(f"YouTube transcript tool error: {e}")
		return _("youtube.error_generic", user_lang, error=str(e))


def get_tools():
	"""Expose Tool objects for the agent."""
	return [
		Tool(
			get_youtube_transcript,
			name="get_youtube_transcript",
			description=(
				"Extract transcript/captions from any YouTube video URL (youtube.com or youtu.be). "
				"Use when users share a YouTube link or ask to transcribe a video."
			)
		)
	]


def get_prompt_description() -> str:
	return (
		"You can transcribe YouTube videos when a user shares a YouTube link. "
		"Use the get_youtube_transcript tool automatically when appropriate."
	)
