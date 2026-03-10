"""
Email service for sending OTP codes via Resend.
"""

import resend
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class EmailService:
    """Service for sending OTP emails via Resend."""

    @staticmethod
    def _send_sync(to_email: str, otp_code: str) -> None:
        """Synchronous email send using Resend API."""
        resend.api_key = settings.resend_api_key

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
            <a href="https://tapoutparking.info" style="text-decoration: none;">
                <h2 style="color: #1a1a1a; margin-bottom: 8px;">TapOut</h2>
            </a>
            <p style="color: #666; font-size: 14px;">Enter this code to verify your UC Davis email:</p>
            <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center; margin: 16px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1a1a1a;">{otp_code}</span>
            </div>
            <p style="color: #999; font-size: 12px;">This code expires in 10 minutes.</p>
            <p style="color: #999; font-size: 12px;">If you didn't request this, you can safely ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
                Having trouble? Contact us at
                <a href="mailto:ucd.tapout@gmail.com" style="color: #666;">ucd.tapout@gmail.com</a>
                or visit <a href="https://tapoutparking.info" style="color: #666;">tapoutparking.info</a>.
            </p>
        </div>
        """

        params: resend.Emails.SendParams = {
            "from": "TapOut <noreply@tapoutparking.info>",
            "to": [to_email],
            "subject": f"TapOut - Your verification code is {otp_code}",
            "html": html_body,
        }

        resend.Emails.send(params)
        logger.info(f"OTP email sent to {to_email}")

    @staticmethod
    async def send_otp_email(to_email: str, otp_code: str) -> None:
        """Send OTP email asynchronously via thread pool."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            _executor, EmailService._send_sync, to_email, otp_code
        )
