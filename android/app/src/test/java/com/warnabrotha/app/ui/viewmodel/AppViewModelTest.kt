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
class AppViewModelTest {

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

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        repository = mockk(relaxed = true)
        // Default: not authenticated → init block skips loadInitialData
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

    // ── Auth ──

    @Test
    fun initialStateIsDefault() {
        val viewModel = createViewModel()
        val state = viewModel.uiState.value

        assertFalse(state.isAuthenticated)
        assertFalse(state.isEmailVerified)
        assertFalse(state.showEmailVerification)
        assertTrue(state.parkingLots.isEmpty())
        assertNull(state.currentSession)
        assertNull(state.error)
        assertNull(state.successMessage)
        assertFalse(state.isLoading)
    }

    @Test
    fun checkAuthStatusWithTokenVerified() {
        val viewModel = createAuthenticatedViewModel()
        val state = viewModel.uiState.value

        assertTrue(state.isAuthenticated)
        assertTrue(state.isEmailVerified)
        assertFalse(state.showEmailVerification)
        coVerify { repository.getParkingLots() }
    }

    @Test
    fun checkAuthStatusWithTokenUnverified() {
        every { repository.hasToken() } returns true
        val unverifiedDevice = testDeviceResponse.copy(emailVerified = false)
        coEvery { repository.getDeviceInfo() } returns Result.Success(unverifiedDevice)

        val viewModel = createViewModel()
        val state = viewModel.uiState.value

        assertTrue(state.isAuthenticated)
        assertFalse(state.isEmailVerified)
        assertTrue(state.showEmailVerification)
        coVerify(exactly = 0) { repository.getParkingLots() }
    }

    @Test
    fun checkAuthStatusNoToken() {
        val viewModel = createViewModel()
        val state = viewModel.uiState.value

        assertFalse(state.isAuthenticated)
        coVerify(exactly = 0) { repository.getDeviceInfo() }
    }

    @Test
    fun registerSuccess() {
        val viewModel = createViewModel()
        val tokenResponse = TokenResponse("tok", "bearer", 3600)
        coEvery { repository.register() } returns Result.Success(tokenResponse)

        viewModel.register()
        val state = viewModel.uiState.value

        assertTrue(state.isAuthenticated)
        assertTrue(state.showEmailVerification)
        assertFalse(state.isLoading)
        assertNull(state.error)
    }

    @Test
    fun registerFailure() {
        val viewModel = createViewModel()
        coEvery { repository.register() } returns Result.Error("Network error")

        viewModel.register()
        val state = viewModel.uiState.value

        assertFalse(state.isAuthenticated)
        assertEquals("Network error", state.error)
        assertFalse(state.isLoading)
    }

    @Test
    fun verifyEmailSuccess() {
        val viewModel = createViewModel()
        val response = EmailVerificationResponse(true, "Verified", true)
        coEvery { repository.verifyEmail("user@ucdavis.edu") } returns Result.Success(response)
        mockLoadInitialData()

        viewModel.verifyEmail("user@ucdavis.edu")
        val state = viewModel.uiState.value

        assertTrue(state.isEmailVerified)
        assertFalse(state.showEmailVerification)
        assertFalse(state.isLoading)
        coVerify { repository.getParkingLots() }
    }

    @Test
    fun verifyEmailNotVerified() {
        val viewModel = createViewModel()
        val response = EmailVerificationResponse(false, "Invalid email domain", false)
        coEvery { repository.verifyEmail("user@gmail.com") } returns Result.Success(response)

        viewModel.verifyEmail("user@gmail.com")
        val state = viewModel.uiState.value

        assertFalse(state.isEmailVerified)
        assertEquals("Invalid email domain", state.error)
        assertFalse(state.isLoading)
    }

    @Test
    fun verifyEmailError() {
        val viewModel = createViewModel()
        coEvery { repository.verifyEmail(any()) } returns Result.Error("Server error")

        viewModel.verifyEmail("user@ucdavis.edu")
        val state = viewModel.uiState.value

        assertFalse(state.isEmailVerified)
        assertEquals("Server error", state.error)
        assertFalse(state.isLoading)
    }

    // ── Data Loading ──

    @Test
    fun selectLotUpdatesState() {
        val viewModel = createAuthenticatedViewModel()

        viewModel.selectLot(2)
        val state = viewModel.uiState.value

        assertEquals(2, state.selectedLotId)
        coVerify { repository.getParkingLot(2) }
        coVerify { repository.getPrediction(2) }
        coVerify { repository.getFeed(2) }
    }

    @Test
    fun selectFeedFilterUpdatesState() {
        val viewModel = createAuthenticatedViewModel()

        viewModel.selectFeedFilter(1)
        assertEquals(1, viewModel.uiState.value.feedFilterLotId)

        viewModel.selectFeedFilter(null)
        assertNull(viewModel.uiState.value.feedFilterLotId)
        // getAllFeeds is called during loadInitialData and again on selectFeedFilter(null)
        coVerify(atLeast = 2) { repository.getAllFeeds() }
    }

    // ── Check-in / Check-out ──

    @Test
    fun checkInSuccess() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkIn(1) } returns Result.Success(testSession)

        viewModel.checkInAtLot(1)
        val state = viewModel.uiState.value

        assertEquals(testSession, state.currentSession)
        assertEquals("Checked in successfully!", state.successMessage)
        assertFalse(state.isLoading)
    }

    @Test
    fun checkInFailure() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkIn(1) } returns Result.Error("Already checked in")

        viewModel.checkInAtLot(1)
        val state = viewModel.uiState.value

        assertNull(state.currentSession)
        assertEquals("Already checked in", state.error)
        assertFalse(state.isLoading)
    }

    @Test
    fun checkOutSuccess() {
        val viewModel = createAuthenticatedViewModel()
        // First check in
        coEvery { repository.checkIn(1) } returns Result.Success(testSession)
        viewModel.checkInAtLot(1)
        assertEquals(testSession, viewModel.uiState.value.currentSession)

        // Then check out
        val checkoutResponse = CheckoutResponse(true, "ok", 1, "2025-01-15T12:00:00Z")
        coEvery { repository.checkOut() } returns Result.Success(checkoutResponse)

        viewModel.checkOut()
        val state = viewModel.uiState.value

        assertNull(state.currentSession)
        assertEquals("Checked out successfully!", state.successMessage)
        assertFalse(state.isLoading)
    }

    @Test
    fun checkOutFailure() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkOut() } returns Result.Error("No active session")

        viewModel.checkOut()
        val state = viewModel.uiState.value

        assertEquals("No active session", state.error)
        assertFalse(state.isLoading)
    }

    // ── Sighting ──

    @Test
    fun reportSightingSuccess() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.reportSighting(1, null) } returns Result.Success(testSightingResponse)

        viewModel.reportSightingAtLot(1)
        val state = viewModel.uiState.value

        assertNotNull(state.successMessage)
        assertTrue(state.successMessage!!.contains("3 users notified"))
        assertFalse(state.isLoading)
    }

    @Test
    fun reportSightingFailure() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.reportSighting(1, any()) } returns Result.Error("Failed to report")

        viewModel.reportSightingAtLot(1)
        val state = viewModel.uiState.value

        assertEquals("Failed to report", state.error)
        assertFalse(state.isLoading)
    }

    @Test
    fun reportSightingNoSelectedLot() {
        val viewModel = createViewModel()
        // No selectedLotId set → reportSighting() should return early

        viewModel.reportSighting()

        coVerify(exactly = 0) { repository.reportSighting(any(), any()) }
    }

    // ── Voting ──

    @Test
    fun voteNewVote() {
        // Set up with sightings in allFeedSightings (feedFilterLotId=null)
        val sighting = FeedSighting(
            id = 10, parkingLotId = 1, parkingLotName = "Lot A",
            parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
            notes = null, upvotes = 0, downvotes = 0, netScore = 0,
            userVote = null, minutesAgo = 15
        )
        val feedsWithSighting = AllFeedsResponse(
            feeds = listOf(
                FeedResponse(1, "Lot A", "LOT_A", listOf(sighting), 1)
            ),
            totalSightings = 1
        )
        every { repository.hasToken() } returns true
        coEvery { repository.getDeviceInfo() } returns Result.Success(testDeviceResponse)
        coEvery { repository.getParkingLots() } returns Result.Success(testLots)
        coEvery { repository.getParkingLot(any()) } returns Result.Success(testLotWithStats)
        coEvery { repository.getAllFeeds() } returns Result.Success(feedsWithSighting)
        coEvery { repository.getCurrentSession() } returns Result.Success(null)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)
        coEvery { repository.getPrediction(any()) } returns Result.Success(testPrediction)
        coEvery { repository.getGlobalStats() } returns Result.Success(testGlobalStats)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(testNotificationList)
        coEvery { repository.vote(10, "upvote") } returns Result.Success(
            VoteResult(true, "created", "upvote")
        )

        val viewModel = AppViewModel(repository)
        // feedFilterLotId is null by default → looks in allFeedSightings
        viewModel.vote(10, "upvote")

        coVerify { repository.vote(10, "upvote") }
        coVerify(exactly = 0) { repository.removeVote(10) }
    }

    @Test
    fun voteToggleRemoves() {
        // Set up with sighting that has userVote="upvote"
        val sighting = FeedSighting(
            id = 10, parkingLotId = 1, parkingLotName = "Lot A",
            parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
            notes = null, upvotes = 1, downvotes = 0, netScore = 1,
            userVote = "upvote", minutesAgo = 15
        )
        val feedsWithSighting = AllFeedsResponse(
            feeds = listOf(
                FeedResponse(1, "Lot A", "LOT_A", listOf(sighting), 1)
            ),
            totalSightings = 1
        )
        every { repository.hasToken() } returns true
        coEvery { repository.getDeviceInfo() } returns Result.Success(testDeviceResponse)
        coEvery { repository.getParkingLots() } returns Result.Success(testLots)
        coEvery { repository.getParkingLot(any()) } returns Result.Success(testLotWithStats)
        coEvery { repository.getAllFeeds() } returns Result.Success(feedsWithSighting)
        coEvery { repository.getCurrentSession() } returns Result.Success(null)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)
        coEvery { repository.getPrediction(any()) } returns Result.Success(testPrediction)
        coEvery { repository.getGlobalStats() } returns Result.Success(testGlobalStats)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(testNotificationList)
        coEvery { repository.removeVote(10) } returns Result.Success(
            VoteResult(true, "removed", null)
        )

        val viewModel = AppViewModel(repository)
        // Voting "upvote" when userVote is already "upvote" → toggle → removeVote
        viewModel.vote(10, "upvote")

        coVerify { repository.removeVote(10) }
        coVerify(exactly = 0) { repository.vote(10, any()) }
    }

    // ── Notifications ──

    @Test
    fun fetchUnreadCount() {
        val viewModel = createViewModel()
        val notifList = NotificationList(emptyList(), unreadCount = 5, total = 5)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(notifList)

        viewModel.fetchUnreadNotificationCount()

        assertEquals(5, viewModel.uiState.value.unreadNotificationCount)
    }

    @Test
    fun updatePushToken() {
        val viewModel = createViewModel()
        coEvery { repository.updateDevice(pushToken = "fcm-token", isPushEnabled = true) } returns
            Result.Success(testDeviceResponse)

        viewModel.updatePushToken("fcm-token")
        val state = viewModel.uiState.value

        assertEquals("fcm-token", state.pushToken)
        verify { repository.savePushToken("fcm-token") }
        coVerify { repository.updateDevice(pushToken = "fcm-token", isPushEnabled = true) }
    }

    // ── UI State ──

    @Test
    fun clearError() {
        val viewModel = createViewModel()
        coEvery { repository.register() } returns Result.Error("Some error")
        viewModel.register()
        assertNotNull(viewModel.uiState.value.error)

        viewModel.clearError()

        assertNull(viewModel.uiState.value.error)
    }

    @Test
    fun clearSuccessMessage() {
        val viewModel = createAuthenticatedViewModel()
        coEvery { repository.checkIn(1) } returns Result.Success(testSession)
        viewModel.checkInAtLot(1)
        assertNotNull(viewModel.uiState.value.successMessage)

        viewModel.clearSuccessMessage()

        assertNull(viewModel.uiState.value.successMessage)
    }

    @Test
    fun refreshReloadsData() {
        val viewModel = createAuthenticatedViewModel()
        clearMocks(repository, answers = false, recordedCalls = true)

        coEvery { repository.getCurrentSession() } returns Result.Success(testSession)
        coEvery { repository.getParkingLot(any()) } returns Result.Success(testLotWithStats)
        coEvery { repository.getPrediction(any()) } returns Result.Success(testPrediction)
        coEvery { repository.getFeed(any()) } returns Result.Success(testFeedResponse)
        coEvery { repository.getUnreadNotifications() } returns Result.Success(testNotificationList)

        viewModel.refresh()

        coVerify { repository.getCurrentSession() }
        coVerify { repository.getUnreadNotifications() }
        assertEquals(testSession, viewModel.uiState.value.currentSession)
    }
}
