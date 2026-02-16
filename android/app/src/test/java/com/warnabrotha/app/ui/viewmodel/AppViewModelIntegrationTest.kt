package com.warnabrotha.app.ui.viewmodel

import com.warnabrotha.app.data.model.*
import com.warnabrotha.app.data.repository.AppRepository
import com.warnabrotha.app.data.repository.Result
import io.mockk.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class AppViewModelIntegrationTest {

    private lateinit var repository: AppRepository
    private val testDispatcher = UnconfinedTestDispatcher()

    private val testDeviceResponse = DeviceResponse(
        id = 1, deviceId = "test-id", emailVerified = true,
        isPushEnabled = false, createdAt = "2025-01-01T00:00:00Z",
        lastSeenAt = "2025-01-15T00:00:00Z"
    )

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true),
        ParkingLot(2, "Lot B", "LOT_B", 38.55, -121.75, true)
    )

    private val testLotWithStats = ParkingLotWithStats(
        id = 1, name = "Lot A", code = "LOT_A",
        latitude = 38.54, longitude = -121.74, isActive = true,
        activeParkers = 5, recentSightings = 2, tapsProbability = 0.7
    )

    private val testFeedResponse = FeedResponse(
        parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", sightings = emptyList(), totalSightings = 0
    )

    private val testAllFeeds = AllFeedsResponse(feeds = emptyList(), totalSightings = 0)

    private val testPrediction = PredictionResponse(
        riskLevel = "low", riskMessage = "Low risk",
        lastSightingLotName = null, lastSightingLotCode = null,
        lastSightingAt = null, hoursSinceLastSighting = null,
        parkingLotId = 1, parkingLotName = "Lot A", parkingLotCode = "LOT_A",
        probability = 0.2, predictedFor = "2025-01-15T12:00:00Z",
        factors = null, confidence = null
    )

    private val testGlobalStats = GlobalStatsResponse(
        totalRegisteredDevices = 100, totalParked = 25, totalSightingsToday = 10
    )

    private val testNotificationList = NotificationList(
        notifications = emptyList(), unreadCount = 0, total = 0
    )

    private val testSession = ParkingSession(
        id = 1, parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", checkedInAt = "2025-01-15T10:00:00Z",
        checkedOutAt = null, isActive = true, reminderSent = false
    )

    private val testSightingResponse = SightingResponse(
        id = 1, parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
        notes = null, usersNotified = 3
    )

    private val testTokenResponse = TokenResponse("tok", "bearer", 3600)

    private val testCheckoutResponse = CheckoutResponse(
        true, "ok", 1, "2025-01-15T12:00:00Z"
    )

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        repository = mockk(relaxed = true)
        every { repository.hasToken() } returns false
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun createViewModel() = AppViewModel(repository)

    private fun mockLoadInitialData() {
        coEvery { repository.getParkingLots() } returns Result.Success(testLots)
        coEvery { repository.getParkingLot(any()) } returns Result.Success(testLotWithStats)
        coEvery { repository.getAllFeeds() } returns Result.Success(testAllFeeds)
        coEvery { repository.getCurrentSession() } returns Result.Success(null)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)
        coEvery { repository.getPrediction(any()) } returns Result.Success(testPrediction)
        coEvery { repository.getGlobalStats() } returns Result.Success(testGlobalStats)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(testNotificationList)
    }

    private fun createAuthenticatedViewModel(): AppViewModel {
        every { repository.hasToken() } returns true
        coEvery { repository.getDeviceInfo() } returns Result.Success(testDeviceResponse)
        mockLoadInitialData()
        return AppViewModel(repository)
    }

    // ══════════════════════════════════════════════════════════
    // B1: Full Auth Flow (5 tests)
    // ══════════════════════════════════════════════════════════

    @Test
    fun fullAuthFlow_register_verify_loadData() {
        val viewModel = createViewModel()
        coEvery { repository.register() } returns Result.Success(testTokenResponse)
        val verifyResponse = EmailVerificationResponse(true, "Verified", true)
        coEvery { repository.verifyEmail("x@ucdavis.edu") } returns Result.Success(verifyResponse)
        mockLoadInitialData()

        // Step 1: Register
        viewModel.register()
        assertTrue(viewModel.uiState.value.isAuthenticated)

        // Step 2: Verify email
        viewModel.verifyEmail("x@ucdavis.edu")
        val state = viewModel.uiState.value

        assertTrue(state.isAuthenticated)
        assertTrue(state.isEmailVerified)
        assertFalse(state.showEmailVerification)

        // Verify data loading was triggered
        coVerify { repository.getParkingLots() }
        coVerify { repository.getAllFeeds() }
        coVerify { repository.getGlobalStats() }
    }

    @Test
    fun authFlow_registerFails_staysOnWelcome() {
        val viewModel = createViewModel()
        coEvery { repository.register() } returns Result.Error("Registration failed")

        viewModel.register()
        val state = viewModel.uiState.value

        assertFalse(state.isAuthenticated)
        assertEquals("Registration failed", state.error)
    }

    @Test
    fun authFlow_verifyFails_staysOnVerification() {
        val viewModel = createViewModel()
        coEvery { repository.register() } returns Result.Success(testTokenResponse)
        coEvery { repository.verifyEmail(any()) } returns Result.Error("Server error")

        viewModel.register()
        assertTrue(viewModel.uiState.value.isAuthenticated)

        viewModel.verifyEmail("x@ucdavis.edu")
        val state = viewModel.uiState.value

        assertTrue(state.isAuthenticated)
        assertTrue(state.showEmailVerification)
        assertEquals("Server error", state.error)
    }

    @Test
    fun authFlow_verifyRejects_showsMessage() {
        val viewModel = createViewModel()
        coEvery { repository.register() } returns Result.Success(testTokenResponse)
        val rejectResponse = EmailVerificationResponse(false, "Invalid domain", false)
        coEvery { repository.verifyEmail(any()) } returns Result.Success(rejectResponse)

        viewModel.register()
        viewModel.verifyEmail("x@gmail.com")
        val state = viewModel.uiState.value

        assertFalse(state.isEmailVerified)
        assertEquals("Invalid domain", state.error)
    }

    @Test
    fun authFlow_alreadyAuthenticated_loadDataCascade() {
        val viewModel = createAuthenticatedViewModel()
        val state = viewModel.uiState.value

        assertTrue(state.isAuthenticated)
        assertTrue(state.isEmailVerified)
        assertTrue(state.parkingLots.isNotEmpty())
        assertNotNull(state.selectedLot)
        assertEquals(100, state.totalRegisteredDevices)
    }

    // ══════════════════════════════════════════════════════════
    // B2: Multi-Step Action Flows (5 tests)
    // ══════════════════════════════════════════════════════════

    @Test
    fun checkIn_thenReportSighting_updatesAll() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkIn(1) } returns Result.Success(testSession)
        coEvery { repository.reportSighting(1, null) } returns Result.Success(testSightingResponse)

        // Check in
        viewModel.checkInAtLot(1)
        assertNotNull(viewModel.uiState.value.currentSession)

        // Report sighting
        viewModel.reportSightingAtLot(1)
        val state = viewModel.uiState.value

        assertNotNull(state.successMessage)
        assertTrue(state.successMessage!!.contains("users notified"))

        // Verify refresh calls after report
        coVerify(atLeast = 1) { repository.getParkingLot(1) }
        coVerify(atLeast = 2) { repository.getAllFeeds() }
    }

    @Test
    fun checkIn_thenCheckOut_clearsSession() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkIn(1) } returns Result.Success(testSession)
        coEvery { repository.checkOut() } returns Result.Success(testCheckoutResponse)

        // Check in
        viewModel.checkInAtLot(1)
        assertNotNull(viewModel.uiState.value.currentSession)

        // Check out
        viewModel.checkOut()
        val state = viewModel.uiState.value

        assertNull(state.currentSession)
        assertTrue(state.successMessage!!.contains("Checked out"))
    }

    @Test
    fun reportSighting_refreshesFeedAndStats() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.reportSighting(1, null) } returns Result.Success(testSightingResponse)

        // Clear recorded calls from init
        clearMocks(repository, answers = false, recordedCalls = true)
        coEvery { repository.getAllFeeds() } returns Result.Success(testAllFeeds)
        coEvery { repository.getParkingLot(any()) } returns Result.Success(testLotWithStats)
        coEvery { repository.getPrediction(any()) } returns Result.Success(testPrediction)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)
        coEvery { repository.getGlobalStats() } returns Result.Success(testGlobalStats)
        coEvery { repository.reportSighting(1, null) } returns Result.Success(testSightingResponse)

        viewModel.reportSightingAtLot(1)

        // getAllFeeds called at least once post-report (loadAllFeeds in reportSightingAtLot)
        coVerify(atLeast = 1) { repository.getAllFeeds() }
    }

    @Test
    fun checkIn_usesSelectedLot() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkIn(2) } returns Result.Success(
            testSession.copy(parkingLotId = 2)
        )

        // Select lot 2, then checkIn (which uses selectedLotId)
        viewModel.selectLot(2)
        viewModel.checkIn()

        coVerify { repository.checkIn(2) }
    }

    @Test
    fun checkIn_noSelectedLot_doesNothing() {
        // Fresh unauthenticated ViewModel has no selectedLotId
        val viewModel = createViewModel()

        viewModel.checkIn()

        coVerify(exactly = 0) { repository.checkIn(any()) }
    }

    // ══════════════════════════════════════════════════════════
    // B3: Error Recovery (4 tests)
    // ══════════════════════════════════════════════════════════

    @Test
    fun checkIn_fails_retry_succeeds() {
        val viewModel = createAuthenticatedViewModel()

        // First attempt fails
        coEvery { repository.checkIn(1) } returns Result.Error("Server error")
        viewModel.checkInAtLot(1)
        assertNotNull(viewModel.uiState.value.error)
        assertNull(viewModel.uiState.value.currentSession)

        // Clear error, retry
        viewModel.clearError()
        coEvery { repository.checkIn(1) } returns Result.Success(testSession)
        viewModel.checkInAtLot(1)

        assertNotNull(viewModel.uiState.value.currentSession)
        assertNotNull(viewModel.uiState.value.successMessage)
    }

    @Test
    fun reportSighting_networkError_retrySucceeds() {
        val viewModel = createAuthenticatedViewModel()

        // First attempt fails
        coEvery { repository.reportSighting(1, null) } returns Result.Error("Network error")
        viewModel.reportSightingAtLot(1)
        assertEquals("Network error", viewModel.uiState.value.error)

        // Retry succeeds
        coEvery { repository.reportSighting(1, null) } returns Result.Success(testSightingResponse)
        viewModel.reportSightingAtLot(1)

        assertNull(viewModel.uiState.value.error)
        assertNotNull(viewModel.uiState.value.successMessage)
    }

    @Test
    fun loadInitialData_lotsFails_showsError() {
        every { repository.hasToken() } returns true
        coEvery { repository.getDeviceInfo() } returns Result.Success(testDeviceResponse)
        coEvery { repository.getParkingLots() } returns Result.Error("Failed to load lots")
        coEvery { repository.getCurrentSession() } returns Result.Success(null)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(testNotificationList)

        val viewModel = AppViewModel(repository)
        val state = viewModel.uiState.value

        assertEquals("Failed to load lots", state.error)
        assertTrue(state.parkingLots.isEmpty())
    }

    @Test
    fun loadInitialData_sessionFails_lotsStillLoad() {
        every { repository.hasToken() } returns true
        coEvery { repository.getDeviceInfo() } returns Result.Success(testDeviceResponse)
        mockLoadInitialData()
        coEvery { repository.getCurrentSession() } returns Result.Error("Session error")

        val viewModel = AppViewModel(repository)
        val state = viewModel.uiState.value

        // Lots should still be loaded despite session failure
        assertTrue(state.parkingLots.isNotEmpty())
        assertEquals(2, state.parkingLots.size)
    }

    // ══════════════════════════════════════════════════════════
    // B4: Feed & Notification (4 tests)
    // ══════════════════════════════════════════════════════════

    @Test
    fun feedFilter_allToLot_reloads() {
        val viewModel = createAuthenticatedViewModel()
        clearMocks(repository, answers = false, recordedCalls = true)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)
        coEvery { repository.getAllFeeds() } returns Result.Success(testAllFeeds)

        // Switch from ALL to lot 1
        viewModel.selectFeedFilter(1)
        coVerify { repository.getFeed(1) }

        // Switch back to ALL
        viewModel.selectFeedFilter(null)
        coVerify { repository.getAllFeeds() }
    }

    @Test
    fun feedFilter_lotToLot_loadsBoth() {
        val viewModel = createAuthenticatedViewModel()
        clearMocks(repository, answers = false, recordedCalls = true)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)

        viewModel.selectFeedFilter(1)
        viewModel.selectFeedFilter(2)

        coVerify { repository.getFeed(1) }
        coVerify { repository.getFeed(2) }
    }

    @Test
    fun vote_onFilteredFeed_callsCorrectMethod() {
        // Set up with feedFilterLotId=1 and a sighting with null userVote
        val sighting = FeedSighting(
            id = 10, parkingLotId = 1, parkingLotName = "Lot A",
            parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
            notes = null, upvotes = 0, downvotes = 0, netScore = 0,
            userVote = null, minutesAgo = 15
        )
        val lotFeed = FeedResponse(1, "Lot A", "LOT_A", listOf(sighting), 1)

        every { repository.hasToken() } returns true
        coEvery { repository.getDeviceInfo() } returns Result.Success(testDeviceResponse)
        mockLoadInitialData()
        coEvery { repository.getFeed(1) } returns Result.Success(lotFeed)
        coEvery { repository.vote(10, "upvote") } returns Result.Success(
            VoteResult(true, "created", "upvote")
        )

        val viewModel = AppViewModel(repository)
        viewModel.selectFeedFilter(1)
        viewModel.vote(10, "upvote")

        coVerify { repository.vote(10, "upvote") }
        coVerify(exactly = 0) { repository.removeVote(10) }
    }

    @Test
    fun notificationCount_updatesOnRefresh() {
        val viewModel = createViewModel()

        // First fetch: count=3
        val notifs3 = NotificationList(emptyList(), unreadCount = 3, total = 3)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(notifs3)
        viewModel.fetchUnreadNotificationCount()
        assertEquals(3, viewModel.uiState.value.unreadNotificationCount)

        // Second fetch: count=7
        val notifs7 = NotificationList(emptyList(), unreadCount = 7, total = 7)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(notifs7)
        viewModel.fetchUnreadNotificationCount()
        assertEquals(7, viewModel.uiState.value.unreadNotificationCount)
    }
}
