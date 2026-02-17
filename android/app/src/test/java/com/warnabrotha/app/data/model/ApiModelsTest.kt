package com.warnabrotha.app.data.model

import com.google.gson.Gson
import org.junit.Assert.*
import org.junit.Test

class ApiModelsTest {

    private val gson = Gson()

    @Test
    fun tokenResponseDeserialization() {
        val json = """
            {
                "access_token": "eyJhbGciOiJIUzI1NiJ9",
                "token_type": "bearer",
                "expires_in": 3600
            }
        """.trimIndent()

        val result = gson.fromJson(json, TokenResponse::class.java)

        assertEquals("eyJhbGciOiJIUzI1NiJ9", result.accessToken)
        assertEquals("bearer", result.tokenType)
        assertEquals(3600, result.expiresIn)
    }

    @Test
    fun parkingLotDeserialization() {
        val json = """
            {
                "id": 1,
                "name": "Lot A",
                "code": "LOT_A",
                "latitude": 38.5449,
                "longitude": -121.7405,
                "is_active": true
            }
        """.trimIndent()

        val result = gson.fromJson(json, ParkingLot::class.java)

        assertEquals(1, result.id)
        assertEquals("Lot A", result.name)
        assertEquals("LOT_A", result.code)
        assertEquals(38.5449, result.latitude!!, 0.0001)
        assertEquals(-121.7405, result.longitude!!, 0.0001)
        assertTrue(result.isActive)
    }

    @Test
    fun parkingSessionDeserialization() {
        val json = """
            {
                "id": 42,
                "parking_lot_id": 1,
                "parking_lot_name": "Lot A",
                "parking_lot_code": "LOT_A",
                "checked_in_at": "2025-01-15T10:30:00Z",
                "checked_out_at": null,
                "is_active": true,
                "reminder_sent": false
            }
        """.trimIndent()

        val result = gson.fromJson(json, ParkingSession::class.java)

        assertEquals(42, result.id)
        assertEquals(1, result.parkingLotId)
        assertEquals("Lot A", result.parkingLotName)
        assertEquals("LOT_A", result.parkingLotCode)
        assertEquals("2025-01-15T10:30:00Z", result.checkedInAt)
        assertNull(result.checkedOutAt)
        assertTrue(result.isActive)
        assertFalse(result.reminderSent)
    }

    @Test
    fun predictionResponseDeserialization() {
        val json = """
            {
                "risk_level": "high",
                "risk_message": "High risk of enforcement",
                "last_sighting_lot_name": null,
                "last_sighting_lot_code": null,
                "last_sighting_at": null,
                "hours_since_last_sighting": null,
                "parking_lot_id": 1,
                "parking_lot_name": "Lot A",
                "parking_lot_code": "LOT_A",
                "probability": 0.85,
                "predicted_for": "2025-01-15T12:00:00Z",
                "factors": {
                    "time_of_day_factor": 0.9,
                    "day_of_week_factor": 0.8,
                    "historical_factor": 0.7,
                    "recent_sightings_factor": 0.6,
                    "academic_calendar_factor": 0.5,
                    "weather_factor": null
                },
                "confidence": 0.92
            }
        """.trimIndent()

        val result = gson.fromJson(json, PredictionResponse::class.java)

        assertEquals("high", result.riskLevel)
        assertEquals(0.85, result.probability, 0.001)
        assertNotNull(result.factors)
        assertEquals(0.9, result.factors!!.timeOfDayFactor, 0.001)
        assertEquals(0.8, result.factors!!.dayOfWeekFactor, 0.001)
        assertNull(result.factors!!.weatherFactor)
        assertEquals(0.92, result.confidence!!, 0.001)
    }

    @Test
    fun feedSightingDeserialization() {
        val json = """
            {
                "id": 10,
                "parking_lot_id": 2,
                "parking_lot_name": "Lot B",
                "parking_lot_code": "LOT_B",
                "reported_at": "2025-01-15T11:00:00Z",
                "notes": "Spotted near entrance",
                "upvotes": 5,
                "downvotes": 1,
                "net_score": 4,
                "user_vote": "upvote",
                "minutes_ago": 15
            }
        """.trimIndent()

        val result = gson.fromJson(json, FeedSighting::class.java)

        assertEquals(5, result.upvotes)
        assertEquals(1, result.downvotes)
        assertEquals(4, result.netScore)
        assertEquals("upvote", result.userVote)
        assertEquals(15, result.minutesAgo)
    }

    @Test
    fun notificationItemDeserialization() {
        val json = """
            {
                "id": 7,
                "notification_type": "sighting_alert",
                "title": "New Sighting",
                "message": "TAPS spotted at Lot A",
                "parking_lot_id": 1,
                "created_at": "2025-01-15T14:00:00Z",
                "read_at": null,
                "is_read": false
            }
        """.trimIndent()

        val result = gson.fromJson(json, NotificationItem::class.java)

        assertEquals("sighting_alert", result.notificationType)
        assertEquals("New Sighting", result.title)
        assertEquals("TAPS spotted at Lot A", result.message)
        assertFalse(result.isRead)
        assertNull(result.readAt)
    }

    @Test
    fun deviceResponseDeserialization() {
        val json = """
            {
                "id": 3,
                "device_id": "abc-123-def",
                "email_verified": true,
                "is_push_enabled": false,
                "created_at": "2025-01-10T08:00:00Z",
                "last_seen_at": "2025-01-15T16:00:00Z"
            }
        """.trimIndent()

        val result = gson.fromJson(json, DeviceResponse::class.java)

        assertEquals("abc-123-def", result.deviceId)
        assertTrue(result.emailVerified)
        assertFalse(result.isPushEnabled)
    }

    @Test
    fun nullFieldsHandled() {
        val lotJson = """{"id":1,"name":"X","code":"X","is_active":true}"""
        val lot = gson.fromJson(lotJson, ParkingLot::class.java)
        assertNull(lot.latitude)
        assertNull(lot.longitude)

        val predJson = """
            {
                "risk_level": "low",
                "risk_message": "Low risk",
                "probability": 0.1,
                "predicted_for": "2025-01-15T12:00:00Z"
            }
        """.trimIndent()
        val pred = gson.fromJson(predJson, PredictionResponse::class.java)
        assertNull(pred.factors)
        assertNull(pred.confidence)

        val feedJson = """
            {
                "id": 1,
                "parking_lot_id": 1,
                "reported_at": "2025-01-15T12:00:00Z",
                "upvotes": 0,
                "downvotes": 0,
                "net_score": 0,
                "minutes_ago": 5
            }
        """.trimIndent()
        val feed = gson.fromJson(feedJson, FeedSighting::class.java)
        assertNull(feed.userVote)

        val notifJson = """
            {
                "id": 1,
                "notification_type": "reminder",
                "title": "T",
                "message": "M",
                "created_at": "2025-01-15T12:00:00Z",
                "is_read": false
            }
        """.trimIndent()
        val notif = gson.fromJson(notifJson, NotificationItem::class.java)
        assertNull(notif.readAt)
    }
}
