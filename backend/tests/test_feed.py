"""
Tests for feed and voting endpoints.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.taps_sighting import TapsSighting
from app.models.vote import Vote, VoteType


class TestFeedEndpoints:
    """Tests for feed API endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_feeds_empty(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting all feeds when no sightings exist."""
        response = client.get(
            "/api/v1/feed",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "feeds" in data
        assert data["total_sightings"] == 0

    @pytest.mark.asyncio
    async def test_get_all_feeds_with_sightings(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting all feeds with recent sightings."""
        # Create a recent sighting
        sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            notes="Test sighting"
        )
        db_session.add(sighting)
        await db_session.commit()

        response = client.get(
            "/api/v1/feed",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total_sightings"] == 1

        # Find our test lot's feed
        test_feed = next(
            (f for f in data["feeds"] if f["parking_lot_id"] == test_parking_lot.id),
            None
        )
        assert test_feed is not None
        assert test_feed["total_sightings"] == 1
        assert test_feed["sightings"][0]["notes"] == "Test sighting"

    @pytest.mark.asyncio
    async def test_feed_excludes_old_sightings(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that feed excludes sightings older than 3 hours."""
        # Create an old sighting (4 hours ago)
        old_time = datetime.now(timezone.utc) - timedelta(hours=4)
        old_sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            notes="Old sighting",
            reported_at=old_time
        )
        db_session.add(old_sighting)
        await db_session.commit()

        response = client.get(
            "/api/v1/feed",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total_sightings"] == 0

    @pytest.mark.asyncio
    async def test_feed_ordered_by_timestamp(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that feed sightings are ordered by timestamp (newest first)."""
        # Create sightings at different times
        now = datetime.now(timezone.utc)
        for i in range(3):
            sighting = TapsSighting(
                parking_lot_id=test_parking_lot.id,
                notes=f"Sighting {i}",
                reported_at=now - timedelta(minutes=i * 30)
            )
            db_session.add(sighting)
        await db_session.commit()

        response = client.get(
            f"/api/v1/feed/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        sightings = data["sightings"]
        assert len(sightings) == 3

        # Verify order (most recent first)
        assert sightings[0]["notes"] == "Sighting 0"
        assert sightings[1]["notes"] == "Sighting 1"
        assert sightings[2]["notes"] == "Sighting 2"

    @pytest.mark.asyncio
    async def test_get_lot_feed(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting feed for a specific lot."""
        # Create a sighting
        sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            notes="Lot specific sighting"
        )
        db_session.add(sighting)
        await db_session.commit()

        response = client.get(
            f"/api/v1/feed/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["parking_lot_id"] == test_parking_lot.id
        assert data["total_sightings"] == 1

    @pytest.mark.asyncio
    async def test_get_lot_feed_not_found(
        self,
        client,
        auth_headers: dict
    ):
        """Test getting feed for non-existent lot."""
        response = client.get(
            "/api/v1/feed/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_feed_includes_vote_counts(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot
    ):
        """Test that feed includes vote counts."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        # Add votes
        vote = Vote(
            device_id=verified_device.id,
            sighting_id=sighting.id,
            vote_type=VoteType.UPVOTE
        )
        db_session.add(vote)
        await db_session.commit()

        response = client.get(
            f"/api/v1/feed/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        sighting_data = data["sightings"][0]
        assert sighting_data["upvotes"] == 1
        assert sighting_data["downvotes"] == 0
        assert sighting_data["net_score"] == 1
        assert sighting_data["user_vote"] == "upvote"


    @pytest.mark.asyncio
    async def test_feed_user_vote_null_when_not_voted(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """Feed shows user_vote as null when current device hasn't voted."""
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()

        response = client.get(
            f"/api/v1/feed/{test_parking_lot.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["sightings"][0]["user_vote"] is None

    @pytest.mark.asyncio
    async def test_get_lot_feed_empty(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """Lot with no sightings → empty feed."""
        response = client.get(
            f"/api/v1/feed/{test_parking_lot.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["total_sightings"] == 0
        assert data["sightings"] == []

    @pytest.mark.asyncio
    async def test_feed_requires_auth(
        self,
        client,
    ):
        """Feed without auth → 403."""
        response = client.get("/api/v1/feed")
        assert response.status_code == 403


class TestVotingEndpoints:
    """Tests for voting API endpoints."""

    @pytest.mark.asyncio
    async def test_upvote_sighting(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test upvoting a sighting."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        response = client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers,
            json={"vote_type": "upvote"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["action"] == "created"
        assert data["vote_type"] == "upvote"

    @pytest.mark.asyncio
    async def test_downvote_sighting(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test downvoting a sighting."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        response = client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers,
            json={"vote_type": "downvote"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["vote_type"] == "downvote"

    @pytest.mark.asyncio
    async def test_toggle_vote_removes_it(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that voting the same way twice removes the vote."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        # First vote
        client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers,
            json={"vote_type": "upvote"}
        )

        # Second vote (same type) should remove
        response = client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers,
            json={"vote_type": "upvote"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["action"] == "removed"
        assert data["vote_type"] is None

    @pytest.mark.asyncio
    async def test_change_vote(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test changing vote from upvote to downvote."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        # First upvote
        client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers,
            json={"vote_type": "upvote"}
        )

        # Change to downvote
        response = client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers,
            json={"vote_type": "downvote"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["action"] == "updated"
        assert data["vote_type"] == "downvote"

    @pytest.mark.asyncio
    async def test_vote_requires_verification(
        self,
        client,
        db_session: AsyncSession,
        unverified_auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that voting requires email verification."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        response = client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=unverified_auth_headers,
            json={"vote_type": "upvote"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_vote_nonexistent_sighting(
        self,
        client,
        auth_headers: dict
    ):
        """Test voting on non-existent sighting."""
        response = client.post(
            "/api/v1/feed/sightings/99999/vote",
            headers=auth_headers,
            json={"vote_type": "upvote"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_vote(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot
    ):
        """Test removing a vote via DELETE."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        # Create vote directly
        vote = Vote(
            device_id=verified_device.id,
            sighting_id=sighting.id,
            vote_type=VoteType.UPVOTE
        )
        db_session.add(vote)
        await db_session.commit()

        response = client.delete(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_remove_vote_not_exists(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test removing vote that doesn't exist."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        response = client.delete(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sighting_votes(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot
    ):
        """Test getting vote counts for a sighting."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        # Add a vote
        vote = Vote(
            device_id=verified_device.id,
            sighting_id=sighting.id,
            vote_type=VoteType.UPVOTE
        )
        db_session.add(vote)
        await db_session.commit()

        response = client.get(
            f"/api/v1/feed/sightings/{sighting.id}/votes",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["upvotes"] == 1
        assert data["downvotes"] == 0
        assert data["net_score"] == 1
        assert data["user_vote"] == "upvote"

    @pytest.mark.asyncio
    async def test_get_votes_nonexistent_sighting(
        self,
        client,
        auth_headers: dict,
    ):
        """Getting votes for nonexistent sighting → 404."""
        response = client.get(
            "/api/v1/feed/sightings/99999/votes",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_vote_requires_auth(
        self,
        client,
        db_session: AsyncSession,
        test_parking_lot: ParkingLot,
    ):
        """Voting without auth → 403."""
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        response = client.post(
            f"/api/v1/feed/sightings/{sighting.id}/vote",
            json={"vote_type": "upvote"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_feed_minutes_ago(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that feed includes minutes_ago field."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()

        response = client.get(
            f"/api/v1/feed/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        sighting_data = data["sightings"][0]
        assert "minutes_ago" in sighting_data
        assert sighting_data["minutes_ago"] >= 0

    @pytest.mark.asyncio
    async def test_concurrent_same_device_votes_no_500(
        self,
        client,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """Concurrent votes from the same device must not produce 500s or IntegrityErrors."""
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()
        await db_session.refresh(sighting)

        results = await asyncio.gather(
            *[
                client.post(
                    f"/api/v1/feed/sightings/{sighting.id}/vote",
                    headers=auth_headers,
                    json={"vote_type": "upvote"},
                )
                for _ in range(5)
            ],
            return_exceptions=True,
        )

        statuses = [r.status_code for r in results if not isinstance(r, Exception)]
        assert all(s == 200 for s in statuses), f"Got non-200 statuses: {statuses}"

        # Final state: at most 1 upvote from this device, no downvotes
        r = client.get(
            f"/api/v1/feed/sightings/{sighting.id}/votes",
            headers=auth_headers,
        )
        data = r.json()
        assert data["upvotes"] in (0, 1)
        assert data["downvotes"] == 0
