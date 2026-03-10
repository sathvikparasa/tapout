"""
Global anonymous chat API endpoints.

Provides REST (GET/POST) and a WebSocket endpoint for real-time delivery.
POST saves instantly and returns; AI moderation runs concurrently via
asyncio.create_task and broadcasts a `message_removed` event if rejected.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.auth import limiter
from app.config import settings
from app.database import AsyncSessionLocal, get_db
from app.models.chat_message import ChatMessage
from app.models.device import Device
from app.schemas.chat import ChatListResponse, ChatMessageCreate, ChatMessageResponse
from app.services.auth import require_verified_device
from app.services.cache import cache_get, cache_set, cache_delete, TTL_CHAT

_CHAT_CACHE_KEY = "chat:messages"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Global Chat"])

_DEFAULT_LIMIT = 50


# ---------------------------------------------------------------------------
# Moderation helpers
# ---------------------------------------------------------------------------

_UNSAFE_CATEGORIES = {
    "Hate Speech": (
        "Slurs, dehumanizing language, or content that attacks or degrades people based on "
        "race, ethnicity, national origin, religion, gender identity, sexual orientation, or "
        "disability. This includes both explicit slurs and coded/implied hate."
    ),
    "Harassment": (
        "Targeted threats, intimidation, or content designed to make a specific person or "
        "group feel unsafe. Includes calls to harm, doxxing, or sustained personal attacks."
    ),
    "Sexual Content": "Explicit sexual descriptions or graphic depictions of sex acts.",
    "Personal Information": (
        "Sharing private information about real individuals such as phone numbers, home "
        "addresses, or student IDs."
    ),
    "Spam": "Meaningless repeated characters, gibberish floods, or copy-paste spam.",
}

_UNSAFE_CATEGORY_STR = "\n".join(
    f"{cat}: {defn}" for cat, defn in _UNSAFE_CATEGORIES.items()
)

_MODERATION_PROMPT = """\
You moderate a campus parking app chat. Determine whether the message below should be removed.

Message:
<message>{content}</message>

Unsafe categories:
<categories>
{categories}
</categories>

Important: regular profanity (fuck, shit, ass, damn, bitch, crap, etc.) is NOT a violation. \
Complaints about parking, TAPS officers, or the university are NOT violations. \
Only flag clear violations of the categories above.

Respond with ONLY a JSON object:
{{"violation": <true|false>, "categories": [<violated category names>], "explanation": <only if violation is true>}}"""


def _moderate_sync(content: str) -> tuple[bool, Optional[str]]:
    """Synchronous Claude moderation call (run via asyncio.to_thread). Fails open."""
    if not settings.anthropic_api_key:
        return True, None
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            temperature=0,
            messages=[{
                "role": "user",
                "content": _MODERATION_PROMPT.format(
                    content=content,
                    categories=_UNSAFE_CATEGORY_STR,
                ),
            }],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].removeprefix("json").strip()
        data = json.loads(raw)
        if data.get("violation"):
            categories = ", ".join(data.get("categories", []))
            return False, categories or "content policy violation"
        return True, None
    except Exception as exc:
        logger.warning("Moderation check failed (allowing message): %s", exc)
        return True, None


async def _moderate_and_flag(msg_id: int, content: str) -> None:
    """
    Background task: run moderation concurrently with the response.
    If rejected, flag the message in the DB and broadcast `message_removed`
    to all connected WebSocket clients.
    """
    allowed, reason = await asyncio.to_thread(_moderate_sync, content)
    if not allowed:
        async with AsyncSessionLocal() as db:
            await db.execute(sa_delete(ChatMessage).where(ChatMessage.id == msg_id))
            await db.commit()
        await cache_delete(_CHAT_CACHE_KEY)
        logger.info("Message %d flagged post-send: %s", msg_id, reason)


def _to_response(msg: ChatMessage) -> ChatMessageResponse:
    now = datetime.now(timezone.utc)
    sent = msg.sent_at
    if sent.tzinfo is None:
        sent = sent.replace(tzinfo=timezone.utc)
    minutes_ago = max(0, int((now - sent).total_seconds() / 60))
    return ChatMessageResponse(
        id=msg.id,
        content=msg.content,
        sent_at=msg.sent_at,
        minutes_ago=minutes_ago,
    )


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/messages",
    response_model=ChatListResponse,
    summary="Get recent chat messages",
    description="Returns messages in chronological order. Pass after_id to poll for new messages. Pass known_ids to get back which ones were removed.",
)
async def get_messages(
    limit: int = _DEFAULT_LIMIT,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db),
) -> ChatListResponse:
    cached = await cache_get(_CHAT_CACHE_KEY)
    if cached is not None:
        return cached

    query = select(ChatMessage).order_by(ChatMessage.id.asc()).limit(min(limit, 100))
    result = await db.execute(query)
    messages = result.scalars().all()
    data = ChatListResponse(messages=[_to_response(m) for m in messages]).model_dump(mode="json")
    await cache_set(_CHAT_CACHE_KEY, data, TTL_CHAT)
    return data


@router.post(
    "/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send an anonymous chat message",
    description=(
        "Saves the message immediately and returns — no blocking moderation. "
        "AI moderation runs concurrently; if rejected the message is flagged and "
        "a `message_removed` WebSocket event is broadcast to all clients."
    ),
)
@limiter.limit("10/minute")
async def send_message(
    request: Request,
    body: ChatMessageCreate,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    # Persist immediately — client gets a response right away
    msg = ChatMessage(content=body.content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    response = _to_response(msg)

    await cache_delete(_CHAT_CACHE_KEY)

    # Moderation runs in the background — does not block the response
    asyncio.create_task(_moderate_and_flag(msg.id, body.content))

    return response
