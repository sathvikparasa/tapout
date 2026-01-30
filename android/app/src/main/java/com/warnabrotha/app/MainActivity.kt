package com.warnabrotha.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.systemBarsPadding
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
                            onVerify = viewModel::verifyEmail,
                            modifier = modifier
                        )
                    }
                    else -> {
                        MainScreen(
                            uiState = uiState,
                            onReportTaps = { viewModel.reportSighting() },
                            onCheckIn = viewModel::checkIn,
                            onCheckOut = viewModel::checkOut,
                            onRefresh = viewModel::refresh,
                            onLotSelected = viewModel::selectLot,
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
