"""
Authentication API endpoints.
"""

import logging

from flask import Blueprint, request, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.firestore_db import get_db
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    EmailVerificationRequest, EmailVerificationResponse,
    TokenResponse, SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, VerifyOTPResponse,
)
from app.services.auth import AuthService, get_current_device
from app.services.otp import OTPService
from app.services.email import EmailService
from app.config import settings

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


def get_real_ip():
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address()


limiter = Limiter(key_func=get_real_ip)


@bp.route("/register", methods=["POST"])
@limiter.limit("10/hour")
async def register_device():
    data = request.get_json(force=True, silent=True) or {}
    try:
        device_data = DeviceCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device = await AuthService.get_or_create_device(
        db=db,
        device_id=device_data.device_id,
        push_token=device_data.push_token,
    )
    access_token = AuthService.create_access_token(device.device_id)
    return jsonify(TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600,
        email_verified=device.email_verified,
    ).model_dump()), 201


@bp.route("/send-otp", methods=["POST"])
@limiter.limit("10/hour")
async def send_otp():
    data = request.get_json(force=True, silent=True) or {}
    try:
        body = SendOTPRequest(**data)
    except Exception as e:
        abort(422, description=str(e))

    if not AuthService.is_valid_ucd_email(body.email):
        abort(400, description=f"Email must be a valid {settings.ucd_email_domain} address")

    db = get_db()
    device_doc = await db.collection("devices").document(body.device_id).get()
    if not device_doc.exists:
        abort(404, description="Device not registered. Call /auth/register first.")

    from app.models.device import Device
    device = Device.from_dict(device_doc.to_dict(), doc_id=device_doc.id)

    if settings.admin_bypass_email and body.email.lower() == settings.admin_bypass_email.lower():
        await db.collection("devices").document(body.device_id).update({"email_verified": True})
        return jsonify(SendOTPResponse(success=True, message="Verification code sent to your email.").model_dump())

    active_count = await OTPService.count_active_otps_for_device(db, device.device_id)
    if active_count >= 3:
        abort(429, description="Too many active codes. Please wait for existing codes to expire.")

    email_count = await OTPService.count_otps_for_email_last_hour(db, body.email)
    if email_count >= 5:
        abort(429, description="Too many codes sent to this email. Please try again later.")

    otp_record, code = await OTPService.create_otp(db, device.device_id, body.email)

    try:
        await EmailService.send_otp_email(body.email, code)
    except Exception as e:
        logger.error(f"Failed to send OTP email to {body.email}: {e}")
        abort(500, description="Failed to send verification email. Please try again.")

    return jsonify(SendOTPResponse(success=True, message="Verification code sent to your email.").model_dump())


@bp.route("/verify-otp", methods=["POST"])
@limiter.limit("20/hour")
async def verify_otp():
    data = request.get_json(force=True, silent=True) or {}
    try:
        body = VerifyOTPRequest(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device_doc = await db.collection("devices").document(body.device_id).get()
    if not device_doc.exists:
        abort(404, description="Device not registered.")

    from app.models.device import Device
    device = Device.from_dict(device_doc.to_dict(), doc_id=device_doc.id)

    if settings.admin_bypass_email and body.email.lower() == settings.admin_bypass_email.lower():
        if body.otp_code != settings.admin_bypass_otp:
            return jsonify(VerifyOTPResponse(success=False, message="Invalid code.", email_verified=False).model_dump())
        await db.collection("devices").document(body.device_id).update({"email_verified": True})
        access_token = AuthService.create_access_token(device.device_id)
        return jsonify(VerifyOTPResponse(
            success=True, message="Email verified successfully.", email_verified=True,
            access_token=access_token, token_type="bearer",
            expires_in=settings.access_token_expire_hours * 3600,
        ).model_dump())

    otp = await OTPService.get_pending_otp(db, device.device_id, body.email)
    if not otp:
        abort(400, description="No pending verification code found. Please request a new one.")

    success, message = await OTPService.verify_otp(db, otp, body.otp_code)
    if not success:
        return jsonify(VerifyOTPResponse(success=False, message=message, email_verified=False).model_dump())

    await db.collection("devices").document(body.device_id).update({"email_verified": True})
    await OTPService.scrub_device_otps(db, device.device_id)
    access_token = AuthService.create_access_token(device.device_id)

    return jsonify(VerifyOTPResponse(
        success=True, message=message, email_verified=True,
        access_token=access_token, token_type="bearer",
        expires_in=settings.access_token_expire_hours * 3600,
    ).model_dump())


@bp.route("/verify-email", methods=["POST"])
async def verify_email():
    """Deprecated: Use /send-otp and /verify-otp instead."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        verification = EmailVerificationRequest(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    success, message = await AuthService.verify_email_for_device(
        db=db, device_id=verification.device_id, email=str(verification.email),
    )
    if not success:
        abort(400, description=message)
    return jsonify(EmailVerificationResponse(success=True, message=message, email_verified=True).model_dump())


@bp.route("/me", methods=["GET"])
async def get_device_info():
    db = get_db()
    device = await get_current_device(db)
    return jsonify(DeviceResponse.from_device(device).model_dump(mode="json"))


@bp.route("/me", methods=["PATCH"])
async def update_device():
    data = request.get_json(force=True, silent=True) or {}
    try:
        updates = DeviceUpdate(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device = await get_current_device(db)
    update_data = {}
    if updates.push_token is not None:
        update_data["push_token"] = updates.push_token
        device.push_token = updates.push_token
    if updates.is_push_enabled is not None:
        update_data["is_push_enabled"] = updates.is_push_enabled
        device.is_push_enabled = updates.is_push_enabled
    if update_data:
        await db.collection("devices").document(device.device_id).update(update_data)
    return jsonify(DeviceResponse.from_device(device).model_dump(mode="json"))
