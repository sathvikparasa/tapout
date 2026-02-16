"""
Pydantic schemas for device registration and authentication.
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class DeviceCreate(BaseModel):
    """Schema for registering a new device."""
    device_id: str = Field(..., min_length=1, max_length=255, description="Unique device identifier (UUID)")
    push_token: Optional[str] = Field(None, max_length=255, description="APNs push notification token")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "push_token": "abc123..."
            }
        }


class DeviceUpdate(BaseModel):
    """Schema for updating device information."""
    push_token: Optional[str] = Field(None, max_length=255, description="APNs push notification token")
    is_push_enabled: Optional[bool] = Field(None, description="Enable/disable push notifications")


class DeviceResponse(BaseModel):
    """Schema for device response."""
    id: int
    device_id: str
    email_verified: bool
    is_push_enabled: bool
    created_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class EmailVerificationRequest(BaseModel):
    """Schema for requesting email verification."""
    email: EmailStr = Field(..., description="UC Davis email address to verify")
    device_id: str = Field(..., min_length=1, max_length=255, description="Device ID")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@ucdavis.edu",
                "device_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class EmailVerificationResponse(BaseModel):
    """Schema for email verification response."""
    success: bool
    message: str
    email_verified: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email verified successfully",
                "email_verified": True
            }
        }


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")
    email_verified: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 604800,
                "email_verified": False
            }
        }


class SendOTPRequest(BaseModel):
    """Schema for requesting an OTP code."""
    email: EmailStr = Field(..., description="UC Davis email address")
    device_id: str = Field(..., min_length=1, max_length=255, description="Device ID")


class SendOTPResponse(BaseModel):
    """Schema for OTP send response."""
    success: bool
    message: str


class VerifyOTPRequest(BaseModel):
    """Schema for verifying an OTP code."""
    email: EmailStr = Field(..., description="UC Davis email address")
    device_id: str = Field(..., min_length=1, max_length=255, description="Device ID")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class VerifyOTPResponse(BaseModel):
    """Schema for OTP verification response."""
    success: bool
    message: str
    email_verified: bool = False
    access_token: str = ""
    token_type: str = "bearer"
    expires_in: int = 0
