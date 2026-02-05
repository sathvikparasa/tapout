package com.warnabrotha.app.data.api

import com.warnabrotha.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // Authentication
    @POST("auth/register")
    suspend fun register(@Body registration: DeviceRegistration): Response<TokenResponse>

    @POST("auth/verify-email")
    suspend fun verifyEmail(@Body request: EmailVerificationRequest): Response<EmailVerificationResponse>

    @GET("auth/me")
    suspend fun getDeviceInfo(): Response<DeviceResponse>

    // Parking Lots
    @GET("lots")
    suspend fun getParkingLots(): Response<List<ParkingLot>>

    @GET("lots/{id}")
    suspend fun getParkingLot(@Path("id") id: Int): Response<ParkingLotWithStats>

    // Parking Sessions
    @POST("sessions/checkin")
    suspend fun checkIn(@Body session: ParkingSessionCreate): Response<ParkingSession>

    @POST("sessions/checkout")
    suspend fun checkOut(): Response<CheckoutResponse>

    @GET("sessions/current")
    suspend fun getCurrentSession(): Response<ParkingSession?>

    @GET("sessions/history")
    suspend fun getSessionHistory(@Query("limit") limit: Int = 20): Response<List<ParkingSession>>

    // Sightings
    @POST("sightings")
    suspend fun reportSighting(@Body sighting: SightingCreate): Response<SightingResponse>

    @GET("sightings")
    suspend fun getSightings(
        @Query("hours") hours: Int = 24,
        @Query("lot_id") lotId: Int? = null,
        @Query("limit") limit: Int = 50
    ): Response<List<SightingResponse>>

    // Feed
    @GET("feed")
    suspend fun getAllFeeds(): Response<AllFeedsResponse>

    @GET("feed/{lot_id}")
    suspend fun getFeed(@Path("lot_id") lotId: Int): Response<FeedResponse>

    @POST("feed/sightings/{id}/vote")
    suspend fun vote(
        @Path("id") sightingId: Int,
        @Body vote: VoteCreate
    ): Response<VoteResult>

    @DELETE("feed/sightings/{id}/vote")
    suspend fun removeVote(@Path("id") sightingId: Int): Response<VoteResult>

    // Predictions
    @GET("predictions/{lot_id}")
    suspend fun getPrediction(@Path("lot_id") lotId: Int): Response<PredictionResponse>

    // Notifications
    @GET("notifications/unread")
    suspend fun getUnreadNotifications(): Response<NotificationList>

    @POST("notifications/read")
    suspend fun markNotificationsRead(@Body request: MarkReadRequest): Response<Unit>

    // Global Stats
    @GET("stats")
    suspend fun getGlobalStats(): Response<GlobalStatsResponse>
}
