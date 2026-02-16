"""
OTP service for generating, storing, and verifying one-time passwords.
"""

import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.models.email_otp import EmailOTP

OTP_EXPIRY_MINUTES = 10
MAX_ATTEMPTS = 5
MAX_ACTIVE_PER_DEVICE = 3
MAX_PER_EMAIL_PER_HOUR = 5


class OTPService:
    """Service for OTP generation, storage, and verification."""

    @staticmethod
    def generate_otp() -> str:
        """Generate a random 6-digit OTP code."""
        return "".join(random.choices(string.digits, k=6))

    @staticmethod
    async def count_active_otps_for_device(db: AsyncSession, device_id: int) -> int:
        """Count unexpired and unverified OTPs for a device."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(func.count(EmailOTP.id)).where(
                EmailOTP.device_id == device_id,
                EmailOTP.expires_at > now,
                EmailOTP.verified_at.is_(None),
            )
        )
        return result.scalar_one()

    @staticmethod
    async def count_otps_for_email_last_hour(db: AsyncSession, email: str) -> int:
        """Count OTPs sent to an email in the last hour."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        result = await db.execute(
            select(func.count(EmailOTP.id)).where(
                EmailOTP.email == email,
                EmailOTP.created_at > one_hour_ago,
            )
        )
        return result.scalar_one()

    @staticmethod
    async def create_otp(db: AsyncSession, device_id: int, email: str) -> tuple[EmailOTP, str]:
        """Create a new OTP record. Returns (otp_record, plain_code)."""
        code = OTPService.generate_otp()
        now = datetime.now(timezone.utc)
        otp = EmailOTP(
            device_id=device_id,
            email=email,
            otp_code=code,
            expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            attempts=0,
        )
        db.add(otp)
        await db.commit()
        await db.refresh(otp)
        return otp, code

    @staticmethod
    async def get_pending_otp(db: AsyncSession, device_id: int, email: str) -> EmailOTP | None:
        """Get the most recent unexpired, unverified OTP for a device+email."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(EmailOTP)
            .where(
                EmailOTP.device_id == device_id,
                EmailOTP.email == email,
                EmailOTP.expires_at > now,
                EmailOTP.verified_at.is_(None),
            )
            .order_by(EmailOTP.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_otp(db: AsyncSession, otp: EmailOTP, submitted_code: str) -> tuple[bool, str]:
        """
        Verify an OTP code. Increments attempts and checks match/expiry/max attempts.
        Returns (success, message).
        """
        otp.attempts += 1

        if otp.attempts > MAX_ATTEMPTS:
            await db.commit()
            return False, "Too many attempts. Please request a new code."

        now = datetime.now(timezone.utc)
        if otp.expires_at < now:
            await db.commit()
            return False, "Code has expired. Please request a new code."

        if otp.otp_code != submitted_code:
            await db.commit()
            remaining = MAX_ATTEMPTS - otp.attempts
            return False, f"Invalid code. {remaining} attempt(s) remaining."

        otp.verified_at = now
        await db.commit()
        return True, "Email verified successfully."

    @staticmethod
    async def scrub_device_otps(db: AsyncSession, device_id: int) -> None:
        """Delete all OTP records for a device."""
        await db.execute(
            delete(EmailOTP).where(EmailOTP.device_id == device_id)
        )
        await db.commit()
