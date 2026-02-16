package com.warnabrotha.app

import android.Manifest
import android.net.Uri
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.FileProvider
import androidx.hilt.navigation.compose.hiltViewModel
import com.warnabrotha.app.ui.screens.EmailVerificationScreen
import com.warnabrotha.app.ui.screens.MainScreen
import com.warnabrotha.app.ui.screens.WelcomeScreen
import com.warnabrotha.app.ui.theme.WarnABrothaTheme
import com.warnabrotha.app.ui.viewmodel.AppViewModel
import dagger.hilt.android.AndroidEntryPoint
import java.io.File

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            WarnABrothaTheme {
                val viewModel: AppViewModel = hiltViewModel()
                val uiState by viewModel.uiState.collectAsState()
                val context = LocalContext.current

                val modifier = Modifier
                    .fillMaxSize()
                    .systemBarsPadding()

                // Camera temp file URI for TakePicture contract
                var cameraImageUri by remember { mutableStateOf<Uri?>(null) }

                // Gallery picker launcher
                val galleryLauncher = rememberLauncherForActivityResult(
                    ActivityResultContracts.PickVisualMedia()
                ) { uri ->
                    uri?.let { viewModel.selectScanImage(it) }
                }

                // Camera launcher
                val cameraLauncher = rememberLauncherForActivityResult(
                    ActivityResultContracts.TakePicture()
                ) { success ->
                    if (success) {
                        cameraImageUri?.let { viewModel.selectScanImage(it) }
                    }
                }

                // Camera permission launcher
                val cameraPermissionLauncher = rememberLauncherForActivityResult(
                    ActivityResultContracts.RequestPermission()
                ) { granted ->
                    if (granted) {
                        val imagesDir = File(context.cacheDir, "images").also { it.mkdirs() }
                        val tempFile = File(imagesDir, "ticket_${System.currentTimeMillis()}.jpg")
                        val uri = FileProvider.getUriForFile(
                            context,
                            "${context.packageName}.fileprovider",
                            tempFile
                        )
                        cameraImageUri = uri
                        cameraLauncher.launch(uri)
                    }
                }

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
                            onTakePhoto = {
                                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                            },
                            onPickFromLibrary = {
                                galleryLauncher.launch(
                                    ActivityResultContracts.PickVisualMedia.ImageOnly.let {
                                        androidx.activity.result.PickVisualMediaRequest(it)
                                    }
                                )
                            },
                            onSubmitScan = { viewModel.submitTicketScan(context) },
                            onResetScan = viewModel::resetScan,
                            modifier = modifier
                        )
                    }
                }
            }
        }
    }
}
