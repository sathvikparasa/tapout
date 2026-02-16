"""
Email service for sending OTP codes via Gmail SMTP.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from concurrent.futures import ThreadPoolExecutor
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class EmailService:
    """Service for sending OTP emails via SMTP."""

    @staticmethod
    def _send_sync(to_email: str, otp_code: str) -> None:
        """Synchronous email send using SMTP_SSL on port 465."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"WarnABrotha - Your verification code is {otp_code}"
        msg["From"] = settings.smtp_email
        msg["To"] = to_email

        text_body = (
            f"Your WarnABrotha verification code is: {otp_code}\n\n"
            f"This code expires in 10 minutes.\n\n"
            f"If you didn't request this, you can safely ignore this email."
        )

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
            <h2 style="color: #1a1a1a; margin-bottom: 8px;">WarnABrotha</h2>
            <p style="color: #666; font-size: 14px;">Enter this code to verify your UC Davis email:</p>
            <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center; margin: 16px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1a1a1a;">{otp_code}</span>
            </div>
            <p style="color: #999; font-size: 12px;">This code expires in 10 minutes.</p>
            <p style="color: #999; font-size: 12px;">If you didn't request this, you can safely ignore this email.</p>
        </div>
        """

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.smtp_email, settings.smtp_password)
            server.sendmail(settings.smtp_email, to_email, msg.as_string())

        logger.info(f"OTP email sent to {to_email}")

    @staticmethod
    async def send_otp_email(to_email: str, otp_code: str) -> None:
        """Send OTP email asynchronously via thread pool."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, EmailService._send_sync, to_email, otp_code)
