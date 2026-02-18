"""
Authentication API endpoints.

Handles device registration, OTP email verification, and rate limiting.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    TokenResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.services.auth import AuthService, get_current_device
from app.services.otp import OTPService
from app.services.email import EmailService
from app.models.device import Device
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a device",
    description="Register a new device and receive an access token."
)
async def register_device(
    request: Request,
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new device or get existing device's token.

    - **device_id**: Unique device identifier (UUID from iOS)
    - **push_token**: Optional APNs push notification token
    """
    device = await AuthService.get_or_create_device(
        db=db,
        device_id=device_data.device_id,
        push_token=device_data.push_token,
    )

    # Generate access token
    access_token = AuthService.create_access_token(device.device_id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600,
        email_verified=device.email_verified,
    )


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send OTP verification code",
    description="Send a 6-digit OTP code to a UC Davis email address."
)
@limiter.limit("10/hour")
async def send_otp(
    request: Request,
    body: SendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a 6-digit OTP code to the provided UC Davis email."""
    # Validate email domain
    if not AuthService.is_valid_ucd_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email must be a valid {settings.ucd_email_domain} address",
        )

    # Get device
    result = await db.execute(
        select(Device).where(Device.device_id == body.device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered. Call /auth/register first.",
        )

    # Check per-device rate limit (max 3 active OTPs)
    active_count = await OTPService.count_active_otps_for_device(db, device.id)
    if active_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many active codes. Please wait for existing codes to expire.",
        )

    # Check per-email rate limit (max 5 per hour)
    email_count = await OTPService.count_otps_for_email_last_hour(db, body.email)
    if email_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many codes sent to this email. Please try again later.",
        )

    # Generate and store OTP
    otp_record, code = await OTPService.create_otp(db, device.id, body.email)

    # Send email
    try:
        await EmailService.send_otp_email(body.email, code)
    except Exception as e:
        logger.error(f"Failed to send OTP email to {body.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again.",
        )

    return SendOTPResponse(
        success=True,
        message="Verification code sent to your email.",
    )


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    summary="Verify OTP code",
    description="Verify the 6-digit OTP code and complete email verification."
)
@limiter.limit("20/hour")
async def verify_otp(
    request: Request,
    body: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify the OTP code and mark the device as email-verified."""
    # Get device
    result = await db.execute(
        select(Device).where(Device.device_id == body.device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered.",
        )

    # Get pending OTP
    otp = await OTPService.get_pending_otp(db, device.id, body.email)
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification code found. Please request a new one.",
        )

    # Verify
    success, message = await OTPService.verify_otp(db, otp, body.otp_code)
    if not success:
        return VerifyOTPResponse(
            success=False,
            message=message,
            email_verified=False,
        )

    # Mark device as verified
    device.email_verified = True
    await db.commit()

    # Scrub all OTPs for this device
    await OTPService.scrub_device_otps(db, device.id)

    # Generate fresh token
    access_token = AuthService.create_access_token(device.device_id)

    return VerifyOTPResponse(
        success=True,
        message=message,
        email_verified=True,
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600,
    )


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    summary="Verify UC Davis email (deprecated)",
    description="Verify a UC Davis email address for the device.",
    deprecated=True,
)
async def verify_email(
    verification: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify a UC Davis email address. DEPRECATED: Use /send-otp and /verify-otp instead.
    """
    success, message = await AuthService.verify_email_for_device(
        db=db,
        device_id=verification.device_id,
        email=verification.email,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return EmailVerificationResponse(
        success=True,
        message=message,
        email_verified=True,
    )


@router.get(
    "/me",
    response_model=DeviceResponse,
    summary="Get current device info",
    description="Get information about the currently authenticated device."
)
async def get_device_info(
    device: Device = Depends(get_current_device)
):
    """Get the current device's information."""
    return DeviceResponse.model_validate(device)


@router.patch(
    "/me",
    response_model=DeviceResponse,
    summary="Update device settings",
    description="Update the current device's settings."
)
async def update_device(
    updates: DeviceUpdate,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Update device settings.

    - **push_token**: Update APNs push notification token
    - **is_push_enabled**: Enable/disable push notifications
    """
    if updates.push_token is not None:
        device.push_token = updates.push_token

    if updates.is_push_enabled is not None:
        device.is_push_enabled = updates.is_push_enabled

    await db.commit()
    await db.refresh(device)

    return DeviceResponse.model_validate(device)
