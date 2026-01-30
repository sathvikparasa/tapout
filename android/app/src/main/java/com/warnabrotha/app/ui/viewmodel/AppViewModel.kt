package com.warnabrotha.app.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.warnabrotha.app.data.model.*
import com.warnabrotha.app.data.repository.AppRepository
import com.warnabrotha.app.data.repository.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AppUiState(
    val isAuthenticated: Boolean = false,
    val isEmailVerified: Boolean = false,
    val showEmailVerification: Boolean = false,
    val parkingLots: List<ParkingLot> = emptyList(),
    val selectedLot: ParkingLotWithStats? = null,
    val selectedLotId: Int? = null,
    val currentSession: ParkingSession? = null,
    val feed: FeedResponse? = null,
    val prediction: PredictionResponse? = null,
    val displayedProbability: Double = 0.0,
    val isLoading: Boolean = false,
    val error: String? = null,
    val successMessage: String? = null
)

@HiltViewModel
class AppViewModel @Inject constructor(
    private val repository: AppRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AppUiState())
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()

    init {
        checkAuthStatus()
    }

    fun checkAuthStatus() {
        viewModelScope.launch {
            if (repository.hasToken()) {
                when (val result = repository.getDeviceInfo()) {
                    is Result.Success -> {
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = true,
                            isEmailVerified = result.data.emailVerified,
                            showEmailVerification = !result.data.emailVerified
                        )
                        if (result.data.emailVerified) {
                            loadInitialData()
                        }
                    }
                    is Result.Error -> {
                        _uiState.value = _uiState.value.copy(
                            isAuthenticated = false,
                            isEmailVerified = false
                        )
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
                    _uiState.value = _uiState.value.copy(
                        isAuthenticated = true,
                        isLoading = false,
                        showEmailVerification = true
                    )
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

    fun verifyEmail(email: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = repository.verifyEmail(email)) {
                is Result.Success -> {
                    if (result.data.emailVerified) {
                        _uiState.value = _uiState.value.copy(
                            isEmailVerified = true,
                            showEmailVerification = false,
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
                        selectedLotId = selectedLotId
                    )
                    selectedLotId?.let { loadLotData(it) }
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

    fun checkIn() {
        val lotId = _uiState.value.selectedLotId ?: return
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
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = repository.reportSighting(lotId, notes)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "TAPS reported! ${result.data.usersNotified} users notified."
                    )
                    loadLotData(lotId)
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

    fun vote(sightingId: Int, voteType: String) {
        viewModelScope.launch {
            val currentVote = _uiState.value.feed?.sightings
                ?.find { it.id == sightingId }?.userVote

            if (currentVote == voteType) {
                // Remove vote
                when (repository.removeVote(sightingId)) {
                    is Result.Success -> {
                        _uiState.value.selectedLotId?.let { loadLotData(it) }
                    }
                    is Result.Error -> { /* Handle error */ }
                }
            } else {
                // Add or change vote
                when (repository.vote(sightingId, voteType)) {
                    is Result.Success -> {
                        _uiState.value.selectedLotId?.let { loadLotData(it) }
                    }
                    is Result.Error -> { /* Handle error */ }
                }
            }
        }
    }

    fun refresh() {
        _uiState.value.selectedLotId?.let { loadLotData(it) }
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
}
