package com.warnabrotha.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.messaging.FirebaseMessaging
import com.warnabrotha.app.data.model.*
import com.warnabrotha.app.data.repository.AppRepository
import com.warnabrotha.app.data.repository.Result
import kotlinx.coroutines.async
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import javax.inject.Inject

enum class OTPStep {
    EMAIL_INPUT,
    CODE_INPUT
}

data class AppUiState(
    val isAuthenticated: Boolean = false,
    val isEmailVerified: Boolean = false,
    val showEmailVerification: Boolean = false,
    val otpStep: OTPStep = OTPStep.EMAIL_INPUT,
    val otpEmail: String = "",
    val canResendOTP: Boolean = false,
    val resendCooldownSeconds: Int = 0,
    val parkingLots: List<ParkingLot> = emptyList(),
    val lotStats: Map<Int, ParkingLotWithStats> = emptyMap(),
    val selectedLot: ParkingLotWithStats? = null,
    val selectedLotId: Int? = null,
    val currentSession: ParkingSession? = null,
    val feed: FeedResponse? = null,
    val allFeedSightings: List<FeedSighting> = emptyList(),
    val allFeedsTotalCount: Int = 0,
    val feedFilterLotId: Int? = null, // null means "ALL" is selected
    val totalRegisteredDevices: Int = 0,
    val prediction: PredictionResponse? = null,
    val displayedProbability: Double = 0.0,
    val isLoading: Boolean = false,
    val error: String? = null,
    val successMessage: String? = null,
    // Notification fields
    val pushToken: String? = null,
    val notificationPermissionGranted: Boolean = false,
    val unreadNotificationCount: Int = 0
)

@HiltViewModel
class AppViewModel @Inject constructor(
    private val repository: AppRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AppUiState())
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()

    init {
        if (repository.hasToken() && repository.hasCompletedOnboarding()) {
            _uiState.value = _uiState.value.copy(
                isAuthenticated = true,
                isEmailVerified = true
            )
            silentRefresh()
        } else if (repository.hasToken()) {
            _uiState.value = _uiState.value.copy(isAuthenticated = true)
            silentRefresh()
        }
    }

    private fun silentRefresh() {
        viewModelScope.launch {
            when (val result = repository.register()) {
                is Result.Success -> {
                    if (result.data.emailVerified) {
                        repository.setCompletedOnboarding(true)
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = true,
                            isEmailVerified = true,
                            showEmailVerification = false
                        )
                        loadInitialData()
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = true,
                            showEmailVerification = true
                        )
                    }
                }
                is Result.Error -> {
                    // Network error — use existing token optimistically
                    if (repository.hasCompletedOnboarding()) {
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = true,
                            isEmailVerified = true,
                            showEmailVerification = false
                        )
                        loadInitialData()
                    }
                }
            }
        }
    }

    fun register() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = repository.register()) {
                is Result.Success -> {
                    if (result.data.emailVerified) {
                        repository.setCompletedOnboarding(true)
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = true,
                            isEmailVerified = true,
                            showEmailVerification = false,
                            isLoading = false
                        )
                        loadInitialData()
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = true,
                            isLoading = false,
                            showEmailVerification = true
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message
                    )
                }
            }
        }
    }

    fun sendOTP(email: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null, otpEmail = email)

            when (val result = repository.sendOTP(email)) {
                is Result.Success -> {
                    if (result.data.success) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            otpStep = OTPStep.CODE_INPUT
                        )
                        startResendCooldown()
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = result.data.message
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message
                    )
                }
            }
        }
    }

    fun verifyOTP(otpCode: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val email = _uiState.value.otpEmail

            when (val result = repository.verifyOTP(email, otpCode)) {
                is Result.Success -> {
                    if (result.data.success && result.data.emailVerified) {
                        repository.setCompletedOnboarding(true)
                        _uiState.value = _uiState.value.copy(
                            isEmailVerified = true,
                            showEmailVerification = false,
                            otpStep = OTPStep.EMAIL_INPUT,
                            isLoading = false
                        )
                        loadInitialData()
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = result.data.message
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message
                    )
                }
            }
        }
    }

    fun resendOTP() {
        sendOTP(_uiState.value.otpEmail)
    }

    fun changeEmail() {
        _uiState.value = _uiState.value.copy(
            otpStep = OTPStep.EMAIL_INPUT,
            error = null
        )
    }

    private fun startResendCooldown() {
        _uiState.value = _uiState.value.copy(canResendOTP = false, resendCooldownSeconds = 30)
        viewModelScope.launch {
            for (i in 29 downTo 0) {
                delay(1000)
                _uiState.value = _uiState.value.copy(resendCooldownSeconds = i)
            }
            _uiState.value = _uiState.value.copy(canResendOTP = true, resendCooldownSeconds = 0)
        }
    }

    private fun loadInitialData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            android.util.Log.d("AppViewModel", "Loading initial data...")

            // Load parking lots
            when (val lotsResult = repository.getParkingLots()) {
                is Result.Success -> {
                    val lots = lotsResult.data
                    android.util.Log.d("AppViewModel", "Loaded ${lots.size} parking lots")
                    val selectedLotId = lots.firstOrNull()?.id
                    _uiState.value = _uiState.value.copy(
                        parkingLots = lots,
                        selectedLotId = selectedLotId,
                        feedFilterLotId = null // Default to ALL for feed
                    )
                    selectedLotId?.let { loadLotData(it) }
                    // Load all feeds by default for the feed tab
                    loadAllFeeds()
                    // Load stats for all lots (for map view)
                    loadAllLotStats(lots)
                    // Load global stats (for homepage)
                    loadGlobalStats()
                    // Load unread notification count
                    fetchUnreadNotificationCount()
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load lots: ${lotsResult.message}")
                    _uiState.value = _uiState.value.copy(error = lotsResult.message)
                }
            }

            // Load current session
            when (val sessionResult = repository.getCurrentSession()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        currentSession = sessionResult.data
                    )
                }
                is Result.Error -> { /* Session might not exist */ }
            }

            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    private fun loadAllLotStats(lots: List<ParkingLot>) {
        viewModelScope.launch {
            val statsMap = mutableMapOf<Int, ParkingLotWithStats>()
            lots.forEach { lot ->
                when (val result = repository.getParkingLot(lot.id)) {
                    is Result.Success -> {
                        statsMap[lot.id] = result.data
                    }
                    is Result.Error -> {
                        android.util.Log.e("AppViewModel", "Failed to load stats for lot ${lot.id}: ${result.message}")
                    }
                }
            }
            _uiState.value = _uiState.value.copy(lotStats = statsMap)
        }
    }

    fun refreshAllLotStats() {
        viewModelScope.launch {
            loadAllLotStats(_uiState.value.parkingLots)
            loadGlobalStats()
        }
    }

    private fun loadGlobalStats() {
        viewModelScope.launch {
            when (val result = repository.getGlobalStats()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        totalRegisteredDevices = result.data.totalRegisteredDevices
                    )
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load global stats: ${result.message}")
                    // Don't show error to user, just use default value
                }
            }
        }
    }

    fun loadLotData(lotId: Int) {
        viewModelScope.launch {
            // Load lot details
            when (val result = repository.getParkingLot(lotId)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(selectedLot = result.data)
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load lot: ${result.message}")
                }
            }

            // Load prediction
            when (val result = repository.getPrediction(lotId)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        prediction = result.data,
                        displayedProbability = result.data.probability
                    )
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load prediction: ${result.message}")
                }
            }

            // Load feed
            when (val result = repository.getFeed(lotId)) {
                is Result.Success -> {
                    android.util.Log.d("AppViewModel", "Feed loaded: ${result.data.sightings.size} sightings")
                    _uiState.value = _uiState.value.copy(feed = result.data)
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load feed: ${result.message}")
                }
            }
        }
    }

    fun selectLot(lotId: Int) {
        _uiState.value = _uiState.value.copy(selectedLotId = lotId)
        loadLotData(lotId)
    }

    fun selectFeedFilter(lotId: Int?) {
        _uiState.value = _uiState.value.copy(feedFilterLotId = lotId)
        if (lotId == null) {
            loadAllFeeds()
        } else {
            loadFeedForLot(lotId)
        }
    }

    private fun loadAllFeeds() {
        viewModelScope.launch {
            when (val result = repository.getAllFeeds()) {
                is Result.Success -> {
                    val allSightings = result.data.feeds
                        .flatMap { it.sightings }
                        .sortedBy { it.minutesAgo }
                    _uiState.value = _uiState.value.copy(
                        allFeedSightings = allSightings,
                        allFeedsTotalCount = result.data.totalSightings
                    )
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load all feeds: ${result.message}")
                }
            }
        }
    }

    private fun loadFeedForLot(lotId: Int) {
        viewModelScope.launch {
            when (val result = repository.getFeed(lotId)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(feed = result.data)
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to load feed: ${result.message}")
                }
            }
        }
    }

    fun checkIn() {
        val lotId = _uiState.value.selectedLotId ?: return
        checkInAtLot(lotId)
    }

    fun checkInAtLot(lotId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = repository.checkIn(lotId)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        currentSession = result.data,
                        isLoading = false,
                        successMessage = "Checked in successfully!"
                    )
                    loadLotData(lotId)
                    refreshAllLotStats()
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message
                    )
                }
            }
        }
    }

    fun checkOut() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = repository.checkOut()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        currentSession = null,
                        isLoading = false,
                        successMessage = "Checked out successfully!"
                    )
                    _uiState.value.selectedLotId?.let { loadLotData(it) }
                    refreshAllLotStats()
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message
                    )
                }
            }
        }
    }

    fun reportSighting(notes: String? = null) {
        val lotId = _uiState.value.selectedLotId ?: return
        reportSightingAtLot(lotId, notes)
    }

    fun reportSightingAtLot(lotId: Int, notes: String? = null) {
        android.util.Log.d("AppViewModel", "reportSightingAtLot called with lotId: $lotId")
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = repository.reportSighting(lotId, notes)) {
                is Result.Success -> {
                    android.util.Log.d("AppViewModel", "Report success: ${result.data.usersNotified} users notified")
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "TAPS reported! ${result.data.usersNotified} users notified."
                    )
                    loadLotData(lotId)
                    loadAllFeeds() // Refresh the feed
                    refreshAllLotStats() // Refresh lot stats
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Report error for lotId $lotId: ${result.message}")
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.message
                    )
                }
            }
        }
    }

    fun vote(sightingId: Int, voteType: String) {
        viewModelScope.launch {
            // Check the correct data source based on current feed filter
            val filterLotId = _uiState.value.feedFilterLotId
            val currentVote = if (filterLotId == null) {
                _uiState.value.allFeedSightings
                    .find { it.id == sightingId }?.userVote
            } else {
                _uiState.value.feed?.sightings
                    ?.find { it.id == sightingId }?.userVote
            }

            val result = if (currentVote == voteType) {
                // Remove vote (toggle)
                repository.removeVote(sightingId)
            } else {
                // Add or change vote
                repository.vote(sightingId, voteType)
            }

            if (result is Result.Success) {
                // Refresh the correct feed view
                if (filterLotId == null) {
                    loadAllFeeds()
                } else {
                    loadFeedForLot(filterLotId)
                }
            }
        }
    }

    fun refresh() {
        _uiState.value.selectedLotId?.let { loadLotData(it) }
        fetchUnreadNotificationCount()
        viewModelScope.launch {
            when (val sessionResult = repository.getCurrentSession()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(currentSession = sessionResult.data)
                }
                is Result.Error -> { }
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun clearSuccessMessage() {
        _uiState.value = _uiState.value.copy(successMessage = null)
    }

    fun onNotificationPermissionResult(granted: Boolean) {
        _uiState.value = _uiState.value.copy(notificationPermissionGranted = granted)
        if (granted) {
            fetchAndSyncPushToken()
        }
    }

    private fun fetchAndSyncPushToken() {
        viewModelScope.launch {
            try {
                val token = FirebaseMessaging.getInstance().token.await()
                updatePushToken(token)
            } catch (e: Exception) {
                android.util.Log.e("AppViewModel", "Failed to get FCM token", e)
            }
        }
    }

    fun updatePushToken(token: String) {
        viewModelScope.launch {
            repository.savePushToken(token)
            _uiState.value = _uiState.value.copy(pushToken = token)
            try {
                repository.updateDevice(pushToken = token, isPushEnabled = true)
            } catch (e: Exception) {
                android.util.Log.e("AppViewModel", "Failed to sync push token with backend", e)
            }
        }
    }

    fun fetchUnreadNotificationCount() {
        viewModelScope.launch {
            when (val result = repository.getUnreadNotifications()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        unreadNotificationCount = result.data.unreadCount
                    )
                }
                is Result.Error -> {
                    android.util.Log.e("AppViewModel", "Failed to fetch unread count: ${result.message}")
                }
            }
        }
    }
}
