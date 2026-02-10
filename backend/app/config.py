"""
Application configuration settings.
Loads environment variables and provides typed configuration access.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All settings have sensible defaults for development.
    """

    # Application
    app_name: str = "WarnABrotha API"
    debug: bool = False
    api_version: str = "v1"

    # Database (Supabase PostgreSQL)
    database_url: str
    database_url_sync: str

    # Authentication
    # Secret key for JWT token signing
    secret_key: str = "development-secret-key-change-in-production"
    # Token expiration time in hours
    access_token_expire_hours: int = 24 * 7  # 1 week

    # UC Davis email domain for verification
    ucd_email_domain: str = "ucdavis.edu"

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
