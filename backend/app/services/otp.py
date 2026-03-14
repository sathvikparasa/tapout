"""
OTP service using Firestore.
"""

import random
import string
from datetime import datetime, timedelta, timezone

from google.cloud.firestore_v1 import AsyncClient

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
    async def count_active_otps_for_device(db: AsyncClient, device_id: str) -> int:
        """Count unexpired and unverified OTPs for a device."""
        now = datetime.now(timezone.utc)
        docs = db.collection("email_otps").where("device_id", "==", device_id).where("expires_at", ">", now).where("verified_at", "==", None).stream()
        count = 0
        async for _ in docs:
            count += 1
        return count

    @staticmethod
    async def count_otps_for_email_last_hour(db: AsyncClient, email: str) -> int:
        """Count OTPs sent to an email in the last hour."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        docs = db.collection("email_otps").where("email", "==", email).where("created_at", ">", one_hour_ago).stream()
        count = 0
        async for _ in docs:
            count += 1
        return count

    @staticmethod
    async def create_otp(db: AsyncClient, device_id: str, email: str) -> tuple[EmailOTP, str]:
        """Create a new OTP record. Returns (otp_record, plain_code)."""
        code = OTPService.generate_otp()
        now = datetime.now(timezone.utc)
        ref = db.collection("email_otps").document()
        otp = EmailOTP(
            id=ref.id,
            device_id=device_id,
            email=email,
            otp_code=code,
            expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            created_at=now,
            attempts=0,
        )
        await ref.set(otp.to_dict())
        return otp, code

    @staticmethod
    async def get_pending_otp(db: AsyncClient, device_id: str, email: str) -> EmailOTP | None:
        """Get the most recent unexpired, unverified OTP for a device+email."""
        now = datetime.now(timezone.utc)
        docs = db.collection("email_otps")\
            .where("device_id", "==", device_id)\
            .where("email", "==", email)\
            .where("expires_at", ">", now)\
            .where("verified_at", "==", None)\
            .order_by("created_at", direction="DESCENDING")\
            .limit(1)\
            .stream()
        async for doc in docs:
            return EmailOTP.from_dict(doc.to_dict(), doc_id=doc.id)
        return None

    @staticmethod
    async def verify_otp(db: AsyncClient, otp: EmailOTP, submitted_code: str) -> tuple[bool, str]:
        """
        Verify an OTP code. Increments attempts and checks match/expiry/max attempts.
        Returns (success, message).
        """
        otp.attempts += 1
        ref = db.collection("email_otps").document(otp.id)

        if otp.attempts > MAX_ATTEMPTS:
            await ref.update({"attempts": otp.attempts})
            return False, "Too many attempts. Please request a new code."

        now = datetime.now(timezone.utc)
        expires_at = otp.expires_at
        if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            await ref.update({"attempts": otp.attempts})
            return False, "Code has expired. Please request a new code."

        if otp.otp_code != submitted_code:
            await ref.update({"attempts": otp.attempts})
            remaining = MAX_ATTEMPTS - otp.attempts
            return False, f"Invalid code. {remaining} attempt(s) remaining."

        await ref.update({"attempts": otp.attempts, "verified_at": now})
        return True, "Email verified successfully."

    @staticmethod
    async def scrub_device_otps(db: AsyncClient, device_id: str) -> None:
        """Delete all OTP records for a device."""
        docs = db.collection("email_otps").where("device_id", "==", device_id).stream()
        async for doc in docs:
            await doc.reference.delete()
