"""
Global anonymous chat API endpoints.

POST saves instantly and returns; AI moderation runs concurrently via
a background thread and deletes the message if rejected.
"""

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import anthropic
from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select, delete as sa_delete

from app.api.auth import limiter
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatListResponse, ChatMessageCreate, ChatMessageResponse
from app.services.auth import require_verified_device
from app.services.cache import cache_get, cache_set, cache_delete, TTL_CHAT

_CHAT_CACHE_KEY = "chat:messages"

logger = logging.getLogger(__name__)

bp = Blueprint("chat", __name__)

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
    Background task: run moderation.
    If rejected, delete the message from the DB and bust the cache.
    """
    allowed, reason = await asyncio.to_thread(_moderate_sync, content)
    if not allowed:
        async with AsyncSessionLocal() as db:
            await db.execute(sa_delete(ChatMessage).where(ChatMessage.id == msg_id))
            await db.commit()
        await cache_delete(_CHAT_CACHE_KEY)
        logger.info("Message %d flagged post-send: %s", msg_id, reason)


def _run_background(coro):
    """Run an async coroutine in a background thread."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    threading.Thread(target=_run, daemon=True).start()


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

@bp.route("/messages", methods=["GET"])
async def get_messages():
    limit = request.args.get("limit", _DEFAULT_LIMIT, type=int)

    cached = await cache_get(_CHAT_CACHE_KEY)
    if cached is not None:
        return jsonify(cached)

    async with AsyncSessionLocal() as db:
        await require_verified_device(db)

        query = select(ChatMessage).order_by(ChatMessage.id.asc()).limit(min(limit, 100))
        result = await db.execute(query)
        messages = result.scalars().all()
        data = ChatListResponse(messages=[_to_response(m) for m in messages]).model_dump(mode="json")
        await cache_set(_CHAT_CACHE_KEY, data, TTL_CHAT)
        return jsonify(data)


@bp.route("/messages", methods=["POST"])
@limiter.limit("30/minute")
async def send_message():
    data = request.get_json(force=True, silent=True) or {}
    try:
        body = ChatMessageCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    async with AsyncSessionLocal() as db:
        await require_verified_device(db)

        # Persist immediately — client gets a response right away
        msg = ChatMessage(content=body.content)
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        response = _to_response(msg)

        await cache_delete(_CHAT_CACHE_KEY)

        # Moderation runs in the background — does not block the response
        _run_background(_moderate_and_flag(msg.id, body.content))

        return jsonify(response.model_dump(mode="json")), 201
