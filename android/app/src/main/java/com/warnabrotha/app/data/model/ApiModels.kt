package com.warnabrotha.app.data.model

import com.google.gson.annotations.SerializedName

// Authentication
data class DeviceRegistration(
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("push_token") val pushToken: String? = null
)

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("expires_in") val expiresIn: Int
)

data class EmailVerificationRequest(
    val email: String,
    @SerializedName("device_id") val deviceId: String
)

data class EmailVerificationResponse(
    val success: Boolean,
    val message: String,
    @SerializedName("email_verified") val emailVerified: Boolean
)

data class DeviceResponse(
    val id: Int,
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("email_verified") val emailVerified: Boolean,
    @SerializedName("is_push_enabled") val isPushEnabled: Boolean,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("last_seen_at") val lastSeenAt: String
)

// Parking Lots
data class ParkingLot(
    val id: Int,
    val name: String,
    val code: String,
    val latitude: Double?,
    val longitude: Double?,
    @SerializedName("is_active") val isActive: Boolean
)

data class ParkingLotWithStats(
    val id: Int,
    val name: String,
    val code: String,
    val latitude: Double?,
    val longitude: Double?,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("active_parkers") val activeParkers: Int,
    @SerializedName("recent_sightings") val recentSightings: Int,
    @SerializedName("taps_probability") val tapsProbability: Double
)

// Parking Sessions
data class ParkingSession(
    val id: Int,
    @SerializedName("parking_lot_id") val parkingLotId: Int,
    @SerializedName("parking_lot_name") val parkingLotName: String?,
    @SerializedName("parking_lot_code") val parkingLotCode: String?,
    @SerializedName("checked_in_at") val checkedInAt: String,
    @SerializedName("checked_out_at") val checkedOutAt: String?,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("reminder_sent") val reminderSent: Boolean
)

data class ParkingSessionCreate(
    @SerializedName("parking_lot_id") val parkingLotId: Int
)

data class CheckoutResponse(
    val success: Boolean,
    val message: String,
    @SerializedName("session_id") val sessionId: Int,
    @SerializedName("checked_out_at") val checkedOutAt: String
)

// Sightings
data class SightingCreate(
    @SerializedName("parking_lot_id") val parkingLotId: Int,
    val notes: String? = null
)

data class SightingResponse(
    val id: Int,
    @SerializedName("parking_lot_id") val parkingLotId: Int,
    @SerializedName("parking_lot_name") val parkingLotName: String?,
    @SerializedName("parking_lot_code") val parkingLotCode: String?,
    @SerializedName("reported_at") val reportedAt: String,
    val notes: String?,
    @SerializedName("users_notified") val usersNotified: Int
)

// Feed
data class FeedSighting(
    val id: Int,
    @SerializedName("parking_lot_id") val parkingLotId: Int,
    @SerializedName("parking_lot_name") val parkingLotName: String?,
    @SerializedName("parking_lot_code") val parkingLotCode: String?,
    @SerializedName("reported_at") val reportedAt: String,
    val notes: String?,
    val upvotes: Int,
    val downvotes: Int,
    @SerializedName("net_score") val netScore: Int,
    @SerializedName("user_vote") val userVote: String?,
    @SerializedName("minutes_ago") val minutesAgo: Int
)

data class FeedResponse(
    @SerializedName("parking_lot_id") val parkingLotId: Int,
    @SerializedName("parking_lot_name") val parkingLotName: String?,
    @SerializedName("parking_lot_code") val parkingLotCode: String?,
    val sightings: List<FeedSighting>,
    @SerializedName("total_sightings") val totalSightings: Int
)

data class AllFeedsResponse(
    val feeds: List<FeedResponse>,
    @SerializedName("total_sightings") val totalSightings: Int
)

// Voting
data class VoteCreate(
    @SerializedName("vote_type") val voteType: String
)

data class VoteResult(
    val success: Boolean,
    val action: String,
    @SerializedName("vote_type") val voteType: String?
)

// Predictions
data class PredictionFactors(
    @SerializedName("time_of_day_factor") val timeOfDayFactor: Double,
    @SerializedName("day_of_week_factor") val dayOfWeekFactor: Double,
    @SerializedName("historical_factor") val historicalFactor: Double,
    @SerializedName("recent_sightings_factor") val recentSightingsFactor: Double,
    @SerializedName("academic_calendar_factor") val academicCalendarFactor: Double,
    @SerializedName("weather_factor") val weatherFactor: Double?
)

data class PredictionResponse(
    @SerializedName("parking_lot_id") val parkingLotId: Int,
    @SerializedName("parking_lot_name") val parkingLotName: String?,
    @SerializedName("parking_lot_code") val parkingLotCode: String?,
    val probability: Double,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("predicted_for") val predictedFor: String,
    val factors: PredictionFactors?,
    val confidence: Double?
)

// Notifications
data class NotificationItem(
    val id: Int,
    @SerializedName("notification_type") val notificationType: String,
    val title: String,
    val message: String,
    @SerializedName("parking_lot_id") val parkingLotId: Int?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("read_at") val readAt: String?,
    @SerializedName("is_read") val isRead: Boolean
)

data class NotificationList(
    val notifications: List<NotificationItem>,
    @SerializedName("unread_count") val unreadCount: Int,
    val total: Int
)

data class MarkReadRequest(
    @SerializedName("notification_ids") val notificationIds: List<Int>
)

// Global Stats
data class GlobalStatsResponse(
    @SerializedName("total_registered_devices") val totalRegisteredDevices: Int,
    @SerializedName("total_parked") val totalParked: Int,
    @SerializedName("total_sightings_today") val totalSightingsToday: Int
)
