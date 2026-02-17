package com.warnabrotha.app.data.repository

import com.warnabrotha.app.data.api.ApiService
import com.warnabrotha.app.data.model.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
}

@Singleton
class AppRepository @Inject constructor(
    private val apiService: ApiService,
    private val tokenRepository: TokenRepository
) {

    suspend fun register(): Result<TokenResponse> {
        return try {
            val deviceId = tokenRepository.getOrCreateDeviceId()
            val response = apiService.register(DeviceRegistration(deviceId))
            if (response.isSuccessful && response.body() != null) {
                val tokenResponse = response.body()!!
                tokenRepository.saveToken(tokenResponse.accessToken)
                Result.Success(tokenResponse)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Registration failed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun sendOTP(email: String): Result<SendOTPResponse> {
        return try {
            val deviceId = tokenRepository.getOrCreateDeviceId()
            val response = apiService.sendOTP(SendOTPRequest(email, deviceId))
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to send OTP")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun verifyOTP(email: String, otpCode: String): Result<VerifyOTPResponse> {
        return try {
            val deviceId = tokenRepository.getOrCreateDeviceId()
            val response = apiService.verifyOTP(VerifyOTPRequest(email, deviceId, otpCode))
            if (response.isSuccessful && response.body() != null) {
                val verifyResponse = response.body()!!
                if (verifyResponse.success && verifyResponse.accessToken.isNotEmpty()) {
                    tokenRepository.saveToken(verifyResponse.accessToken)
                }
                Result.Success(verifyResponse)
            } else {
                Result.Error(response.errorBody()?.string() ?: "OTP verification failed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getDeviceInfo(): Result<DeviceResponse> {
        return try {
            val response = apiService.getDeviceInfo()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get device info")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getParkingLots(): Result<List<ParkingLot>> {
        return try {
            val response = apiService.getParkingLots()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get parking lots")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getParkingLot(id: Int): Result<ParkingLotWithStats> {
        return try {
            val response = apiService.getParkingLot(id)
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get parking lot")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun checkIn(lotId: Int): Result<ParkingSession> {
        return try {
            val response = apiService.checkIn(ParkingSessionCreate(lotId))
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Check-in failed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun checkOut(): Result<CheckoutResponse> {
        return try {
            val response = apiService.checkOut()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Check-out failed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getCurrentSession(): Result<ParkingSession?> {
        return try {
            val response = apiService.getCurrentSession()
            if (response.isSuccessful) {
                Result.Success(response.body())
            } else if (response.code() == 404) {
                Result.Success(null)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get session")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun reportSighting(lotId: Int, notes: String? = null): Result<SightingResponse> {
        return try {
            android.util.Log.d("AppRepository", "Reporting sighting for lotId: $lotId")
            val response = apiService.reportSighting(SightingCreate(lotId, notes))
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                val errorBody = response.errorBody()?.string()
                val errorMsg = when {
                    response.code() == 500 -> "Server error (500). Please try again."
                    errorBody?.contains("detail") == true -> errorBody
                    else -> errorBody ?: "Failed to report sighting (${response.code()})"
                }
                android.util.Log.e("AppRepository", "Report sighting failed: code=${response.code()}, body=$errorBody")
                Result.Error(errorMsg)
            }
        } catch (e: Exception) {
            android.util.Log.e("AppRepository", "Report sighting exception: ${e.message}", e)
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getFeed(lotId: Int): Result<FeedResponse> {
        return try {
            val response = apiService.getFeed(lotId)
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get feed")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun vote(sightingId: Int, voteType: String): Result<VoteResult> {
        return try {
            val response = apiService.vote(sightingId, VoteCreate(voteType))
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to vote")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun removeVote(sightingId: Int): Result<VoteResult> {
        return try {
            val response = apiService.removeVote(sightingId)
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to remove vote")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getPrediction(lotId: Int): Result<PredictionResponse> {
        return try {
            val response = apiService.getPrediction(lotId)
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get prediction")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getAllFeeds(): Result<AllFeedsResponse> {
        return try {
            val response = apiService.getAllFeeds()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get all feeds")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getGlobalStats(): Result<GlobalStatsResponse> {
        return try {
            val response = apiService.getGlobalStats()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get global stats")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun updateDevice(pushToken: String? = null, isPushEnabled: Boolean? = null): Result<DeviceResponse> {
        return try {
            val response = apiService.updateDevice(DeviceUpdate(pushToken, isPushEnabled))
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to update device")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getUnreadNotifications(): Result<NotificationList> {
        return try {
            val response = apiService.getUnreadNotifications()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to get notifications")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    fun hasCompletedOnboarding(): Boolean = tokenRepository.hasCompletedOnboarding()

    fun setCompletedOnboarding(completed: Boolean) = tokenRepository.setCompletedOnboarding(completed)

    fun hasToken(): Boolean = tokenRepository.hasToken()

    fun getSavedPushToken(): String? = tokenRepository.getPushToken()

    fun savePushToken(token: String) = tokenRepository.savePushToken(token)

    suspend fun scanTicket(imageFile: File): Result<TicketScanResponse> {
        return try {
            val mediaType = when (imageFile.extension.lowercase()) {
                "jpg", "jpeg" -> "image/jpeg"
                "png" -> "image/png"
                else -> "image/jpeg"
            }
            val requestBody = imageFile.asRequestBody(mediaType.toMediaTypeOrNull())
            val part = MultipartBody.Part.createFormData("image", imageFile.name, requestBody)
            val response = apiService.scanTicket(part)
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error(response.errorBody()?.string() ?: "Failed to scan ticket")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }
}
