"""
Performance smoke tests — response times and concurrency.
"""

import uuid
import time
import asyncio
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.parking_lot import ParkingLot
from app.services.auth import AuthService
from app.services.notification import NotificationService

API = "/api/v1"


async def create_verified_device_with_headers(
    db_session: AsyncSession,
    push_token: str | None = None,
    is_push_enabled: bool = False,
) -> tuple[Device, dict]:
    device = Device(
        device_id=str(uuid.uuid4()),
        email_verified=True,
        is_push_enabled=is_push_enabled,
        push_token=push_token,
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    token = AuthService.create_access_token(device.device_id)
    return device, {"Authorization": f"Bearer {token}"}


async def _create_lot(db: AsyncSession, name: str, code: str) -> ParkingLot:
    lot = ParkingLot(name=name, code=code, latitude=38.54, longitude=-121.76, is_active=True)
    db.add(lot)
    await db.commit()
    await db.refresh(lot)
    return lot


# ---------------------------------------------------------------------------
# Response Times
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestResponseTimes:

    async def test_health_check_fast(self, client: AsyncClient):
        start = time.perf_counter()
        r = await client.get("/health")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert elapsed_ms < 200

    async def test_list_lots_fast(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict,
    ):
        start = time.perf_counter()
        r = await client.get(f"{API}/lots", headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert elapsed_ms < 500

    async def test_prediction_fast(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict,
    ):
        start = time.perf_counter()
        r = await client.get(f"{API}/predictions", headers=auth_headers)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert r.status_code == 200
        assert elapsed_ms < 500


# ---------------------------------------------------------------------------
# Concurrent Operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestConcurrentOperations:

    async def test_concurrent_sighting_reports(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Conc Sight", "CS01")
        devices = [await create_verified_device_with_headers(db_session) for _ in range(10)]

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            results = await asyncio.gather(
                *[
                    client.post(
                        f"{API}/sightings",
                        json={"parking_lot_id": lot.id},
                        headers=hdrs,
                    )
                    for _, hdrs in devices
                ],
                return_exceptions=True,
            )

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        assert all(s == 201 for s in statuses), f"statuses={statuses}"

    async def test_concurrent_votes_same_sighting(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Conc Vote", "CV01")
        creator, c_hdrs = await create_verified_device_with_headers(db_session)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            r = await client.post(
                f"{API}/sightings",
                json={"parking_lot_id": lot.id},
                headers=c_hdrs,
            )
        sid = r.json()["id"]

        voters = [await create_verified_device_with_headers(db_session) for _ in range(10)]
        vote_types = ["upvote"] * 5 + ["downvote"] * 5

        results = await asyncio.gather(
            *[
                client.post(
                    f"{API}/feed/sightings/{sid}/vote",
                    json={"vote_type": vt},
                    headers=hdrs,
                )
                for (_, hdrs), vt in zip(voters, vote_types)
            ],
            return_exceptions=True,
        )

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        assert all(s == 200 for s in statuses), f"statuses={statuses}"

        # Verify tallies
        r = await client.get(f"{API}/feed/sightings/{sid}/votes", headers=c_hdrs)
        data = r.json()
        assert data["upvotes"] == 5
        assert data["downvotes"] == 5

    async def test_concurrent_checkins_different_lots(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lots = [await _create_lot(db_session, f"Conc Lot {i}", f"CL{i:02d}") for i in range(10)]
        devices = [await create_verified_device_with_headers(db_session) for _ in range(10)]

        results = await asyncio.gather(
            *[
                client.post(
                    f"{API}/sessions/checkin",
                    json={"parking_lot_id": lot.id},
                    headers=hdrs,
                )
                for (_, hdrs), lot in zip(devices, lots)
            ],
            return_exceptions=True,
        )

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        assert all(s == 201 for s in statuses), f"statuses={statuses}"
