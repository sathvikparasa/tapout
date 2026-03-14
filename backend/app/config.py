"""
Application configuration settings.
Loads environment variables and provides typed configuration access.
In production (GCP App Engine), secrets are loaded from Secret Manager.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

# Set GCP_PROJECT to your dev project (starts with 'tapout-dev') or prod project
GCP_PROJECT = os.environ.get("GCP_PROJECT", "")
SECRET_NAMES = ["SECRET_KEY", "FIREBASE_CREDENTIALS_JSON", "RESEND_API_KEY", "ANTHROPIC_API_KEY", "APNS_KEY_ID", "APNS_TEAM_ID", "APNS_KEY_CONTENT", "APNS_BUNDLE_ID", "ADMIN_BYPASS_EMAIL", "ADMIN_BYPASS_OTP"]


def _load_secrets_from_gcp():
    """Load secrets from GCP Secret Manager into environment variables.
    Only runs in production (when GAE_ENV is set)."""
    if os.environ.get("GAE_ENV") != "standard":
        return

    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    for name in SECRET_NAMES:
        if name in os.environ:
            val = os.environ[name]
            print(f"[SECRET MANAGER] '{name}' already in env, skipping Secret Manager (len={len(val)}, empty={val == ''})")
            continue
        try:
            secret_path = f"projects/{GCP_PROJECT}/secrets/{name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            value = response.payload.data.decode("UTF-8")
            os.environ[name] = value
            print(f"[SECRET MANAGER] Loaded '{name}' from Secret Manager (len={len(value)}, empty={value == ''})")
        except Exception as e:
            print(f"[SECRET MANAGER] Failed to load secret '{name}': {e}")


_load_secrets_from_gcp()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All settings have sensible defaults for development.
    """

    # Application
    app_name: str = "WarnABrotha API"
    debug: bool = False
    api_version: str = "v1"

    # Authentication
    # Secret key for JWT token signing
    secret_key: str = "development-secret-key-change-in-production"
    # Token expiration time in hours
    access_token_expire_hours: int = 24 * 365 * 10  # 10 years

    # UC Davis email domain for verification
    ucd_email_domain: str = "ucdavis.edu"

    # Admin bypass email (loaded from Secret Manager in production)
    admin_bypass_email: Optional[str] = None
    admin_bypass_otp: Optional[str] = None

    # SMTP settings for OTP emails
    resend_api_key: str = ""

    # APNs (Apple Push Notification service) configuration
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    apns_key_path: Optional[str] = None      # File path (local dev) — set automatically from apns_key_content in production
    apns_key_content: Optional[str] = None   # Raw .p8 key content (GCP Secret Manager)
    apns_bundle_id: Optional[str] = None
    apns_use_sandbox: bool = os.environ.get("GAE_ENV") != "standard"  # Sandbox for local dev, production for GCP

    # Firebase Cloud Messaging (Android push notifications)
    firebase_credentials_json: Optional[str] = None  # JSON string or file path to service account key

    # Anthropic API key for ticket OCR and chat moderation
    anthropic_api_key: str = ""

    # Redis cache (GCP MemoryStore)
    redis_host: Optional[str] = None
    redis_port: int = 6379

    # Reminder settings
    parking_reminder_hours: int = 3  # Hours before sending checkout reminder

    # Polling settings
    notification_poll_interval_seconds: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore unknown env vars (e.g. legacy DATABASE_URL)


# Global settings instance
settings = Settings()

# If APNS_KEY_CONTENT is provided but APNS_KEY_PATH is not,
# write the key content to a temp file so aioapns can read it.
if settings.apns_key_content and not settings.apns_key_path:
    import tempfile
    _apns_key_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".p8", delete=False
    )
    _apns_key_file.write(settings.apns_key_content)
    _apns_key_file.close()
    settings.apns_key_path = _apns_key_file.name
