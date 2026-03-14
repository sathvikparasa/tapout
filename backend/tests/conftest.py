"""
Test fixtures using the Firestore emulator via gcloud CLI.

Start the emulator before running tests:
    gcloud beta emulators firestore start --host-port=localhost:8080

Then in a separate terminal:
    cd backend && pytest
"""
import os
import uuid
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio

# Point to Firestore emulator
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")
os.environ.setdefault("GCP_PROJECT", "tapout-dev-test")

from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.parking_session import ParkingSession
from app.services.auth import AuthService


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    """Firestore async client pointing at emulator."""
    import firebase_admin
    from firebase_admin import firestore_async

    # Initialize Firebase app if not already done
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(options={"projectId": "tapout-dev-test"})

    client = firestore_async.client(database="warnabrotha")
    yield client

    # Cleanup: delete all test documents
    collections = ["devices", "parking_lots", "parking_sessions", "taps_sightings",
                   "notifications", "votes", "email_otps", "chat_messages"]
    for col in collections:
        async for doc in client.collection(col).stream():
            await doc.reference.delete()


@pytest.fixture(scope="function")
def app(db):
    """Create Flask test app."""
    from unittest.mock import patch
    from app.main import create_app
    flask_app = create_app()
    flask_app.config["TESTING"] = True

    with patch("app.firestore_db.get_db", return_value=db):
        yield flask_app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest_asyncio.fixture
async def test_parking_lot(db) -> ParkingLot:
    lot = ParkingLot(id=1, name="Test Parking Structure", code="TEST",
                     latitude=38.5382, longitude=-121.7617, is_active=True)
    await db.collection("parking_lots").document("1").set(lot.to_dict())
    return lot


@pytest_asyncio.fixture
async def test_device(db) -> Device:
    device = Device(device_id=str(uuid.uuid4()), email_verified=False, is_push_enabled=False)
    await db.collection("devices").document(device.device_id).set(device.to_dict())
    return device


@pytest_asyncio.fixture
async def verified_device(db) -> Device:
    device = Device(device_id=str(uuid.uuid4()), email_verified=True, is_push_enabled=False)
    await db.collection("devices").document(device.device_id).set(device.to_dict())
    return device


@pytest_asyncio.fixture
async def auth_headers(verified_device: Device) -> dict:
    token = AuthService.create_access_token(verified_device.device_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def unverified_auth_headers(test_device: Device) -> dict:
    token = AuthService.create_access_token(test_device.device_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def active_session(db, verified_device: Device, test_parking_lot: ParkingLot) -> ParkingSession:
    ref = db.collection("parking_sessions").document()
    session = ParkingSession(
        id=ref.id,
        device_id=verified_device.device_id,
        parking_lot_id=test_parking_lot.id,
        parking_lot_name=test_parking_lot.name,
        parking_lot_code=test_parking_lot.code,
        checked_in_at=datetime.now(timezone.utc) - timedelta(hours=4),
        is_active=True,
        reminder_sent=False,
    )
    await ref.set(session.to_dict())
    return session
