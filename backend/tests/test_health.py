"""
Tests for health check endpoints.
"""

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "database" in data
