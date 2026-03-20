"""
Synchronous APNs (Apple Push Notification service) client.

Uses httpx (HTTP/2) + python-jose (ES256 JWT) — no asyncio required.
JWT tokens are cached for 50 minutes then rotated (Apple max is 60 min).
apns-expiration=0 means do not attempt delivery if device is offline.
"""
import logging
import threading
import time

import httpx
from jose import jwt

logger = logging.getLogger(__name__)

_PROD_URL = "https://api.push.apple.com/3/device/{token}"
_SANDBOX_URL = "https://api.sandbox.push.apple.com/3/device/{token}"
_JWT_TTL = 3000  # 50 minutes


class APNsClient:
    """Sync HTTP/2 client for Apple Push Notification service."""

    def __init__(
        self,
        key_path: str,
        key_id: str,
        team_id: str,
        bundle_id: str,
        use_sandbox: bool = False,
    ):
        with open(key_path) as f:
            self._private_key = f.read()

        self._key_id = key_id
        self._team_id = team_id
        self._bundle_id = bundle_id
        self._base_url = _SANDBOX_URL if use_sandbox else _PROD_URL

        self._jwt_token: str | None = None
        self._jwt_issued_at: int = 0
        self._jwt_lock = threading.Lock()

        self._http = httpx.Client(http2=True)

    def _get_jwt(self) -> str:
        now = int(time.time())
        with self._jwt_lock:
            if self._jwt_token is None or (now - self._jwt_issued_at) > _JWT_TTL:
                self._jwt_token = jwt.encode(
                    {"iss": self._team_id, "iat": now},
                    self._private_key,
                    algorithm="ES256",
                    headers={"kid": self._key_id},
                )
                self._jwt_issued_at = now
        return self._jwt_token

    def send(
        self,
        device_token: str,
        payload: dict,
        push_type: str = "alert",
        priority: int = 10,
    ) -> bool:
        """
        Send a push notification.

        Returns True on success (HTTP 200), False on APNs error response.
        Raises on network/connection errors — caller is responsible for catching.
        """
        url = self._base_url.format(token=device_token)
        headers = {
            "authorization": f"bearer {self._get_jwt()}",
            "apns-topic": self._bundle_id,
            "apns-push-type": push_type,
            "apns-priority": str(priority),
            "apns-expiration": "0",  # don't retry if device offline
        }
        response = self._http.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.warning(
                "APNs rejected notification: status=%s body=%s",
                response.status_code,
                response.text,
            )
            return False
        return True

    def close(self) -> None:
        """Release the underlying HTTP/2 connection."""
        self._http.close()
