package com.warnabrotha.app

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import com.warnabrotha.app.ui.screens.EmailVerificationScreen
import com.warnabrotha.app.ui.screens.MainScreen
import com.warnabrotha.app.ui.screens.WelcomeScreen
import com.warnabrotha.app.ui.theme.WarnABrothaTheme
import com.warnabrotha.app.ui.viewmodel.AppViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            WarnABrothaTheme {
                val viewModel: AppViewModel = hiltViewModel()
                val uiState by viewModel.uiState.collectAsState()

                val modifier = Modifier
                    .fillMaxSize()
                    .systemBarsPadding()

                when {
                    !uiState.isAuthenticated -> {
                        WelcomeScreen(
                            isLoading = uiState.isLoading,
                            onGetStarted = viewModel::register,
                            modifier = modifier
                        )
                    }
                    uiState.showEmailVerification -> {
                        EmailVerificationScreen(
                            isLoading = uiState.isLoading,
                            error = uiState.error,
                            otpStep = uiState.otpStep,
                            otpEmail = uiState.otpEmail,
                            canResendOTP = uiState.canResendOTP,
                            resendCooldownSeconds = uiState.resendCooldownSeconds,
                            onSendOTP = viewModel::sendOTP,
                            onVerifyOTP = viewModel::verifyOTP,
                            onResendOTP = viewModel::resendOTP,
                            onChangeEmail = viewModel::changeEmail,
                            modifier = modifier
                        )
                    }
                    else -> {
                        val notificationPermissionLauncher = rememberLauncherForActivityResult(
                            ActivityResultContracts.RequestPermission()
                        ) { granted ->
                            viewModel.onNotificationPermissionResult(granted)
                        }

                        LaunchedEffect(Unit) {
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                            } else {
                                viewModel.onNotificationPermissionResult(true)
                            }
                        }

                        MainScreen(
                            uiState = uiState,
                            onReportTaps = { viewModel.reportSighting() },
                            onReportTapsAtLot = { lotId -> viewModel.reportSightingAtLot(lotId) },
                            onCheckIn = viewModel::checkIn,
                            onCheckInAtLot = viewModel::checkInAtLot,
                            onCheckOut = viewModel::checkOut,
                            onRefresh = viewModel::refresh,
                            onLotSelected = viewModel::selectLot,
                            onFeedFilterSelected = viewModel::selectFeedFilter,
                            onUpvote = { id -> viewModel.vote(id, "upvote") },
                            onDownvote = { id -> viewModel.vote(id, "downvote") },
                            onClearError = viewModel::clearError,
                            onClearSuccess = viewModel::clearSuccessMessage,
                            modifier = modifier
                        )
                    }
                }
            }
        }
    }
}
