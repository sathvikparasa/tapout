"""
Application configuration settings.
Loads environment variables and provides typed configuration access.
In production (GCP App Engine), secrets are loaded from Secret Manager.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

GCP_PROJECT = "tapout-485821"
SECRET_NAMES = ["DATABASE_URL", "DATABASE_URL_SYNC", "SECRET_KEY", "FIREBASE_CREDENTIALS_JSON", "SMTP_EMAIL", "SMTP_PASSWORD"]


def _load_secrets_from_gcp():
    """Load secrets from GCP Secret Manager into environment variables.
    Only runs in production (when GAE_ENV is set)."""
    if os.environ.get("GAE_ENV") != "standard":
        return

    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    for name in SECRET_NAMES:
        if name not in os.environ:
            secret_path = f"projects/{GCP_PROJECT}/secrets/{name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            os.environ[name] = response.payload.data.decode("UTF-8")


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

    # Database (Cloud SQL PostgreSQL)
    database_url: str
    database_url_sync: str

    # Authentication
    # Secret key for JWT token signing
    secret_key: str = "development-secret-key-change-in-production"
    # Token expiration time in hours
    access_token_expire_hours: int = 24 * 365 * 10  # 10 years

    # UC Davis email domain for verification
    ucd_email_domain: str = "ucdavis.edu"

    # SMTP settings for OTP emails
    smtp_email: str = ""
    smtp_password: str = ""

    # APNs (Apple Push Notification service) configuration
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    apns_key_path: Optional[str] = None
    apns_bundle_id: Optional[str] = None
    apns_use_sandbox: bool = True  # Use sandbox for development

    # Firebase Cloud Messaging (Android push notifications)
    firebase_credentials_json: Optional[str] = None  # JSON string or file path to service account key

    # Reminder settings
    parking_reminder_hours: int = 3  # Hours before sending checkout reminder

    # Polling settings
    notification_poll_interval_seconds: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
