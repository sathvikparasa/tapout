package com.warnabrotha.app.data.repository

import com.warnabrotha.app.data.api.ApiService
import com.warnabrotha.app.data.model.*
import io.mockk.*
import kotlinx.coroutines.test.runTest
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import retrofit2.Response
import java.io.IOException

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class AppRepositoryTest {

    private lateinit var apiService: ApiService
    private lateinit var tokenRepository: TokenRepository
    private lateinit var repository: AppRepository

    private val testTokenResponse = TokenResponse(
        accessToken = "test-access-token",
        tokenType = "bearer",
        expiresIn = 3600
    )

    private val testDeviceResponse = DeviceResponse(
        id = 1,
        deviceId = "test-device-id",
        emailVerified = true,
        isPushEnabled = false,
        createdAt = "2025-01-01T00:00:00Z",
        lastSeenAt = "2025-01-15T00:00:00Z"
    )

    private val testLot = ParkingLot(
        id = 1, name = "Lot A", code = "LOT_A",
        latitude = 38.54, longitude = -121.74, isActive = true
    )

    private val testLotWithStats = ParkingLotWithStats(
        id = 1, name = "Lot A", code = "LOT_A",
        latitude = 38.54, longitude = -121.74, isActive = true,
        activeParkers = 5, recentSightings = 2, tapsProbability = 0.7
    )

    private val testSession = ParkingSession(
        id = 1, parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", checkedInAt = "2025-01-15T10:00:00Z",
        checkedOutAt = null, isActive = true, reminderSent = false
    )

    private val testCheckoutResponse = CheckoutResponse(
        success = true, message = "Checked out",
        sessionId = 1, checkedOutAt = "2025-01-15T12:00:00Z"
    )

    private val testSightingResponse = SightingResponse(
        id = 1, parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
        notes = null, usersNotified = 3
    )

    private val testFeedSighting = FeedSighting(
        id = 1, parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
        notes = null, upvotes = 2, downvotes = 0, netScore = 2,
        userVote = null, minutesAgo = 15
    )

    private val testFeedResponse = FeedResponse(
        parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A",
        sightings = listOf(testFeedSighting, testFeedSighting.copy(id = 2)),
        totalSightings = 2
    )

    private val testAllFeedsResponse = AllFeedsResponse(
        feeds = listOf(testFeedResponse),
        totalSightings = 5
    )

    private val testPrediction = PredictionResponse(
        riskLevel = "high", riskMessage = "High risk",
        lastSightingLotName = null, lastSightingLotCode = null,
        lastSightingAt = null, hoursSinceLastSighting = null,
        parkingLotId = 1, parkingLotName = "Lot A", parkingLotCode = "LOT_A",
        probability = 0.85, predictedFor = "2025-01-15T12:00:00Z",
        factors = null, confidence = 0.9
    )

    private val testGlobalStats = GlobalStatsResponse(
        totalRegisteredDevices = 100,
        totalParked = 25,
        totalSightingsToday = 10
    )

    private val testNotificationList = NotificationList(
        notifications = emptyList(),
        unreadCount = 3,
        total = 10
    )

    @Before
    fun setUp() {
        apiService = mockk()
        tokenRepository = mockk(relaxed = true)
        every { tokenRepository.getOrCreateDeviceId() } returns "test-device-id"
        repository = AppRepository(apiService, tokenRepository)
    }

    private fun <T> errorResponse(code: Int, body: String = """{"detail":"error"}"""): Response<T> =
        Response.error(code, body.toResponseBody(null))

    // ── Auth ──

    @Test
    fun registerSuccess() = runTest {
        coEvery { apiService.register(any()) } returns Response.success(testTokenResponse)

        val result = repository.register()

        assertTrue(result is Result.Success)
        assertEquals("test-access-token", (result as Result.Success).data.accessToken)
        assertEquals("bearer", result.data.tokenType)
        assertEquals(3600, result.data.expiresIn)
    }

    @Test
    fun registerSavesToken() = runTest {
        coEvery { apiService.register(any()) } returns Response.success(testTokenResponse)

        repository.register()

        verify { tokenRepository.saveToken("test-access-token") }
    }

    @Test
    fun registerFailure() = runTest {
        coEvery { apiService.register(any()) } throws IOException("timeout")

        val result = repository.register()

        assertTrue(result is Result.Error)
        assertEquals("timeout", (result as Result.Error).message)
    }

    @Test
    fun sendOTPSuccess() = runTest {
        val response = SendOTPResponse(success = true, message = "OTP sent")
        coEvery { apiService.sendOTP(any()) } returns Response.success(response)

        val result = repository.sendOTP("user@ucdavis.edu")

        assertTrue(result is Result.Success)
        assertTrue((result as Result.Success).data.success)
    }

    @Test
    fun sendOTPFailure() = runTest {
        coEvery { apiService.sendOTP(any()) } returns errorResponse(400, "Invalid email")

        val result = repository.sendOTP("user@gmail.com")

        assertTrue(result is Result.Error)
    }

    @Test
    fun verifyOTPSuccess() = runTest {
        val response = VerifyOTPResponse(
            success = true, message = "Verified", emailVerified = true,
            accessToken = "new-token", tokenType = "bearer", expiresIn = 3600
        )
        coEvery { apiService.verifyOTP(any()) } returns Response.success(response)

        val result = repository.verifyOTP("user@ucdavis.edu", "123456")

        assertTrue(result is Result.Success)
        assertTrue((result as Result.Success).data.emailVerified)
        verify { tokenRepository.saveToken("new-token") }
    }

    @Test
    fun verifyOTPFailure() = runTest {
        coEvery { apiService.verifyOTP(any()) } returns errorResponse(400, "Invalid OTP")

        val result = repository.verifyOTP("user@ucdavis.edu", "000000")

        assertTrue(result is Result.Error)
    }

    // ── Device ──

    @Test
    fun getDeviceInfoSuccess() = runTest {
        coEvery { apiService.getDeviceInfo() } returns Response.success(testDeviceResponse)

        val result = repository.getDeviceInfo()

        assertTrue(result is Result.Success)
        assertEquals("test-device-id", (result as Result.Success).data.deviceId)
        assertTrue(result.data.emailVerified)
    }

    // ── Parking ──

    @Test
    fun getParkingLotsSuccess() = runTest {
        coEvery { apiService.getParkingLots() } returns Response.success(listOf(testLot, testLot.copy(id = 2)))

        val result = repository.getParkingLots()

        assertTrue(result is Result.Success)
        assertEquals(2, (result as Result.Success).data.size)
    }

    @Test
    fun getParkingLotSuccess() = runTest {
        coEvery { apiService.getParkingLot(1) } returns Response.success(testLotWithStats)

        val result = repository.getParkingLot(1)

        assertTrue(result is Result.Success)
        assertEquals(5, (result as Result.Success).data.activeParkers)
        assertEquals(2, result.data.recentSightings)
    }

    @Test
    fun checkInSuccess() = runTest {
        coEvery { apiService.checkIn(any()) } returns Response.success(testSession)

        val result = repository.checkIn(1)

        assertTrue(result is Result.Success)
        assertTrue((result as Result.Success).data.isActive)
        assertEquals(1, result.data.parkingLotId)
    }

    @Test
    fun checkInHttpError() = runTest {
        coEvery { apiService.checkIn(any()) } returns errorResponse(409, "Already checked in")

        val result = repository.checkIn(1)

        assertTrue(result is Result.Error)
    }

    @Test
    fun checkOutSuccess() = runTest {
        coEvery { apiService.checkOut() } returns Response.success(testCheckoutResponse)

        val result = repository.checkOut()

        assertTrue(result is Result.Success)
        assertTrue((result as Result.Success).data.success)
        assertEquals(1, result.data.sessionId)
    }

    @Test
    fun getCurrentSessionActive() = runTest {
        coEvery { apiService.getCurrentSession() } returns Response.success(testSession)

        val result = repository.getCurrentSession()

        assertTrue(result is Result.Success)
        assertNotNull((result as Result.Success).data)
        assertEquals(1, result.data!!.id)
    }

    @Test
    fun getCurrentSessionNullOn404() = runTest {
        coEvery { apiService.getCurrentSession() } returns errorResponse(404)

        val result = repository.getCurrentSession()

        assertTrue(result is Result.Success)
        assertNull((result as Result.Success).data)
    }

    // ── Sighting / Feed ──

    @Test
    fun reportSightingSuccess() = runTest {
        coEvery { apiService.reportSighting(any()) } returns Response.success(testSightingResponse)

        val result = repository.reportSighting(1)

        assertTrue(result is Result.Success)
        assertEquals(3, (result as Result.Success).data.usersNotified)
    }

    @Test
    fun reportSightingServerError() = runTest {
        coEvery { apiService.reportSighting(any()) } returns errorResponse(500, "Internal Server Error")

        val result = repository.reportSighting(1)

        assertTrue(result is Result.Error)
        assertTrue((result as Result.Error).message.contains("Server error (500)"))
    }

    @Test
    fun getFeedSuccess() = runTest {
        coEvery { apiService.getFeed(1) } returns Response.success(testFeedResponse)

        val result = repository.getFeed(1)

        assertTrue(result is Result.Success)
        assertEquals(2, (result as Result.Success).data.sightings.size)
    }

    @Test
    fun getAllFeedsSuccess() = runTest {
        coEvery { apiService.getAllFeeds() } returns Response.success(testAllFeedsResponse)

        val result = repository.getAllFeeds()

        assertTrue(result is Result.Success)
        assertEquals(5, (result as Result.Success).data.totalSightings)
    }

    // ── Voting ──

    @Test
    fun voteSuccess() = runTest {
        val voteResult = VoteResult(success = true, action = "created", voteType = "upvote")
        coEvery { apiService.vote(10, any()) } returns Response.success(voteResult)

        val result = repository.vote(10, "upvote")

        assertTrue(result is Result.Success)
        assertEquals("created", (result as Result.Success).data.action)
        assertEquals("upvote", result.data.voteType)
    }

    @Test
    fun removeVoteSuccess() = runTest {
        val voteResult = VoteResult(success = true, action = "removed", voteType = null)
        coEvery { apiService.removeVote(10) } returns Response.success(voteResult)

        val result = repository.removeVote(10)

        assertTrue(result is Result.Success)
        assertEquals("removed", (result as Result.Success).data.action)
        assertNull(result.data.voteType)
    }

    // ── Other ──

    @Test
    fun getPredictionSuccess() = runTest {
        coEvery { apiService.getPrediction(1) } returns Response.success(testPrediction)

        val result = repository.getPrediction(1)

        assertTrue(result is Result.Success)
        assertEquals("high", (result as Result.Success).data.riskLevel)
        assertEquals(0.85, result.data.probability, 0.001)
    }

    @Test
    fun getGlobalStatsSuccess() = runTest {
        coEvery { apiService.getGlobalStats() } returns Response.success(testGlobalStats)

        val result = repository.getGlobalStats()

        assertTrue(result is Result.Success)
        assertEquals(100, (result as Result.Success).data.totalRegisteredDevices)
    }

    @Test
    fun updateDeviceSuccess() = runTest {
        coEvery { apiService.updateDevice(any()) } returns Response.success(testDeviceResponse)

        val result = repository.updateDevice(pushToken = "push-tok", isPushEnabled = true)

        assertTrue(result is Result.Success)
        coVerify { apiService.updateDevice(DeviceUpdate("push-tok", true)) }
    }

    @Test
    fun getUnreadNotificationsSuccess() = runTest {
        coEvery { apiService.getUnreadNotifications() } returns Response.success(testNotificationList)

        val result = repository.getUnreadNotifications()

        assertTrue(result is Result.Success)
        assertEquals(3, (result as Result.Success).data.unreadCount)
    }

    // ── Token Delegation ──

    @Test
    fun hasTokenDelegates() {
        every { tokenRepository.hasToken() } returns true

        assertTrue(repository.hasToken())

        verify { tokenRepository.hasToken() }
    }

    @Test
    fun getSavedPushTokenDelegates() {
        every { tokenRepository.getPushToken() } returns "saved-push-token"

        assertEquals("saved-push-token", repository.getSavedPushToken())

        verify { tokenRepository.getPushToken() }
    }

    @Test
    fun savePushTokenDelegates() {
        repository.savePushToken("new-push-token")

        verify { tokenRepository.savePushToken("new-push-token") }
    }
}
