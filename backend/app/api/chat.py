"""
Global anonymous chat API endpoints.

Provides GET and POST for chat messages, with AI content moderation
on every inbound message using Claude Haiku.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.auth import limiter
from app.config import settings
from app.database import get_db
from app.models.chat_message import ChatMessage
from app.models.device import Device
from app.schemas.chat import ChatListResponse, ChatMessageCreate, ChatMessageResponse
from app.services.auth import require_verified_device

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Global Chat"])

_MODERATION_SYSTEM = """You moderate a campus parking app chat. Decide if a message is appropriate.

REJECT if the message contains:
- Hate speech, slurs, or targeted personal attacks
- Explicit sexual or graphic violent content
- Personal identifying information (phone numbers, addresses, student IDs)
- Pure spam (repeated characters with no meaning, gibberish floods)

ALLOW everything else — complaints, opinions, jokes, parking questions, profanity in context.

Respond with ONLY valid JSON, nothing else:
{"allowed": true}  OR  {"allowed": false, "reason": "brief reason"}"""

_DEFAULT_LIMIT = 50


def _moderate(content: str) -> tuple[bool, Optional[str]]:
    """
    Run AI content moderation synchronously.
    Returns (is_allowed, reason_if_blocked).
    Fails open — if the API is unavailable, the message is allowed.
    """
    if not settings.anthropic_api_key:
        return True, None

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            system=_MODERATION_SYSTEM,
            messages=[{"role": "user", "content": content}],
        )
        data = json.loads(response.content[0].text.strip())
        if data.get("allowed") is False:
            return False, data.get("reason", "Message flagged by content filter.")
        return True, None
    except Exception as exc:
        logger.warning("Moderation check failed (allowing message): %s", exc)
        return True, None


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


@router.get(
    "/messages",
    response_model=ChatListResponse,
    summary="Get recent chat messages",
    description="Returns non-flagged messages in chronological order. Pass after_id to poll for new messages.",
)
async def get_messages(
    after_id: Optional[int] = None,
    limit: int = _DEFAULT_LIMIT,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db),
) -> ChatListResponse:
    query = select(ChatMessage).where(ChatMessage.is_flagged == False)  # noqa: E712
    if after_id is not None:
        query = query.where(ChatMessage.id > after_id)
    query = query.order_by(ChatMessage.id.asc()).limit(min(limit, 100))

    result = await db.execute(query)
    messages = result.scalars().all()
    return ChatListResponse(messages=[_to_response(m) for m in messages])


@router.post(
    "/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send an anonymous chat message",
    description="Runs AI content moderation before storing. Returns 400 if flagged.",
)
@limiter.limit("10/minute")
async def send_message(
    request: Request,
    body: ChatMessageCreate,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    allowed, reason = await asyncio.to_thread(_moderate, body.content)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Your message was flagged by our content filter.",
        )

    msg = ChatMessage(content=body.content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return _to_response(msg)
