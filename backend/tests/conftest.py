"""
Test fixtures and configuration for Flask app.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting
from app.models.notification import Notification
from app.models.vote import Vote
from app.models.email_otp import EmailOTP
from app.services.auth import AuthService

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
def app(test_engine):
    """Create Flask test app with overridden database."""
    import app.database as db_module
    from app.main import create_app

    original_session_local = db_module.AsyncSessionLocal
    original_engine = db_module.engine

    test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    db_module.AsyncSessionLocal = test_session_factory
    db_module.engine = test_engine

    flask_app = create_app()
    flask_app.config["TESTING"] = True

    yield flask_app

    db_module.AsyncSessionLocal = original_session_local
    db_module.engine = original_engine


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest_asyncio.fixture
async def test_parking_lot(db_session: AsyncSession) -> ParkingLot:
    lot = ParkingLot(name="Test Parking Structure", code="TEST", latitude=38.5382, longitude=-121.7617, is_active=True)
    db_session.add(lot)
    await db_session.commit()
    await db_session.refresh(lot)
    return lot


@pytest_asyncio.fixture
async def test_device(db_session: AsyncSession) -> Device:
    device = Device(device_id=str(uuid.uuid4()), email_verified=False, is_push_enabled=False)
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


@pytest_asyncio.fixture
async def verified_device(db_session: AsyncSession) -> Device:
    device = Device(device_id=str(uuid.uuid4()), email_verified=True, is_push_enabled=False)
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
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
async def active_session(db_session: AsyncSession, verified_device: Device, test_parking_lot: ParkingLot) -> ParkingSession:
    session = ParkingSession(
        device_id=verified_device.id,
        parking_lot_id=test_parking_lot.id,
        checked_in_at=datetime.now(timezone.utc) - timedelta(hours=4),
        reminder_sent=False,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
