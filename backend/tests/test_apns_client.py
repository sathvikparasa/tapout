"""Tests for the sync APNs HTTP/2 client."""
import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.apns_client import APNsClient


FAKE_P8 = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgepH63HbgmL1TDAs3
PnVrXUXso4c1/34IG7ZFIToHa/ehRANCAARokOzMTq8mUIfLxlHhqGBk5+UUCXv+
u2CMPhul8iBy7KGLcrLzsUf1RaIz2gsE2sMiLkbaLHzZHVpb1VnFQO/f
-----END PRIVATE KEY-----"""


@pytest.fixture
def client(tmp_path):
    key_file = tmp_path / "AuthKey_TEST.p8"
    key_file.write_text(FAKE_P8)
    return APNsClient(
        key_path=str(key_file),
        key_id="TESTKEYID1",
        team_id="TESTTEAMID",
        bundle_id="com.test.app",
        use_sandbox=True,
    )


class TestAPNsClientJWT:
    def test_jwt_generated(self, client):
        """JWT is generated and cached."""
        token = client._get_jwt()
        assert token is not None
        assert token == client._get_jwt()  # cached

    def test_jwt_refreshed_after_50_minutes(self, client):
        """JWT is regenerated after 3000 seconds."""
        first = client._get_jwt()
        client._jwt_issued_at = int(time.time()) - 3001
        second = client._get_jwt()
        assert first != second

    def test_jwt_has_correct_claims(self, client):
        """JWT payload contains iss and iat."""
        from jose import jwt as jose_jwt
        token = client._get_jwt()
        claims = jose_jwt.get_unverified_claims(token)
        assert claims["iss"] == "TESTTEAMID"
        assert "iat" in claims

    def test_jwt_has_correct_header(self, client):
        """JWT header contains alg=ES256 and kid."""
        from jose import jwt as jose_jwt
        token = client._get_jwt()
        header = jose_jwt.get_unverified_header(token)
        assert header["alg"] == "ES256"
        assert header["kid"] == "TESTKEYID1"


class TestAPNsClientSend:
    def test_send_success(self, client):
        """200 response → returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client._http, "post", return_value=mock_response):
            result = client.send("a1b2c3d4" * 8, {"aps": {"alert": "hi"}})

        assert result is True

    def test_send_failure(self, client):
        """Non-200 response → returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"reason": "BadDeviceToken"}'

        with patch.object(client._http, "post", return_value=mock_response):
            result = client.send("a1b2c3d4" * 8, {"aps": {"alert": "hi"}})

        assert result is False

    def test_send_uses_sandbox_url(self, client):
        """Sandbox client posts to api.sandbox.push.apple.com."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client._http, "post", return_value=mock_response) as mock_post:
            client.send("a1b2c3d4" * 8, {"aps": {}})
            url = mock_post.call_args[0][0]

        assert "sandbox" in url

    def test_send_uses_prod_url(self, tmp_path):
        """Production client posts to api.push.apple.com (no sandbox)."""
        key_file = tmp_path / "AuthKey.p8"
        key_file.write_text(FAKE_P8)
        prod_client = APNsClient(
            key_path=str(key_file),
            key_id="KID", team_id="TID",
            bundle_id="com.test.app", use_sandbox=False,
        )
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(prod_client._http, "post", return_value=mock_response) as mock_post:
            prod_client.send("a1b2c3d4" * 8, {"aps": {}})
            url = mock_post.call_args[0][0]

        assert "sandbox" not in url

    def test_send_sets_apns_headers(self, client):
        """Correct APNs headers are sent."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(client._http, "post", return_value=mock_response) as mock_post:
            client.send("a1b2c3d4" * 8, {"aps": {}}, priority=10)
            headers = mock_post.call_args[1]["headers"]

        assert headers["apns-topic"] == "com.test.app"
        assert headers["apns-push-type"] == "alert"
        assert headers["apns-priority"] == "10"
        assert headers["authorization"].startswith("bearer ")
        assert headers["apns-expiration"] == "0"

    def test_send_network_error_propagates(self, client):
        """Network exception propagates — NotificationService catches it."""
        with patch.object(client._http, "post", side_effect=Exception("conn refused")):
            with pytest.raises(Exception, match="conn refused"):
                client.send("a1b2c3d4" * 8, {"aps": {}})

    def test_close(self, client):
        """close() shuts down the httpx client without error."""
        with patch.object(client._http, "close") as mock_close:
            client.close()
        mock_close.assert_called_once()
