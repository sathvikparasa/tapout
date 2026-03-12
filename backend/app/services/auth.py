"""
Authentication service for UC Davis email verification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import re

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from flask import request, abort

from app.config import settings
from app.models.device import Device


class AuthService:
    UCD_EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@" + re.escape(settings.ucd_email_domain) + r"$",
        re.IGNORECASE
    )

    @classmethod
    def is_valid_ucd_email(cls, email: str) -> bool:
        return bool(cls.UCD_EMAIL_PATTERN.match(email))

    @staticmethod
    def create_access_token(device_id: str, expires_delta: Optional[timedelta] = None) -> str:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
        to_encode = {"sub": device_id, "exp": expire, "type": "access"}
        return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            device_id: str = payload.get("sub")
            return device_id if device_id else None
        except JWTError:
            return None

    @staticmethod
    async def get_or_create_device(db: AsyncSession, device_id: str, push_token: Optional[str] = None) -> Device:
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()
        if device:
            if push_token:
                device.push_token = push_token
                device.is_push_enabled = True
            await db.commit()
            await db.refresh(device)
            return device
        device = Device(
            device_id=device_id,
            push_token=push_token,
            is_push_enabled=push_token is not None,
            email_verified=False,
        )
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def verify_email_for_device(db: AsyncSession, device_id: str, email: str) -> tuple[bool, str]:
        if not AuthService.is_valid_ucd_email(email):
            return False, f"Email must be a valid {settings.ucd_email_domain} address"
        result = await db.execute(select(Device).where(Device.device_id == device_id))
        device = result.scalar_one_or_none()
        if not device:
            return False, "Device not registered"
        device.email_verified = True
        await db.commit()
        return True, "Email verified successfully"


async def get_current_device(db: AsyncSession) -> Device:
    """
    Extract Bearer token from Flask request, validate it, and return the Device.
    Calls abort(401) if token is missing/invalid or device not found.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Missing or invalid authorization header")
    token = auth_header[7:]
    device_id = AuthService.decode_token(token)
    if not device_id:
        abort(401, description="Invalid or expired token")
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        abort(401, description="Device not found")
    return device


async def require_verified_device(db: AsyncSession) -> Device:
    """
    Like get_current_device but also requires email_verified == True.
    Calls abort(403) if not verified.
    """
    device = await get_current_device(db)
    if not device.email_verified:
        abort(403, description="Email verification required")
    return device
