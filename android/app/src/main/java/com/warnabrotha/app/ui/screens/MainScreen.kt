package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.warnabrotha.app.ui.components.BeveledBorder
import com.warnabrotha.app.ui.components.Win95Popup
import com.warnabrotha.app.ui.components.Win95TabBar
import com.warnabrotha.app.ui.components.Win95TitleBar
import com.warnabrotha.app.ui.theme.Win95Colors
import com.warnabrotha.app.ui.viewmodel.AppUiState

@Composable
fun MainScreen(
    uiState: AppUiState,
    onReportTaps: () -> Unit,
    onCheckIn: () -> Unit,
    onCheckOut: () -> Unit,
    onRefresh: () -> Unit,
    onLotSelected: (Int) -> Unit,
    onUpvote: (Int) -> Unit,
    onDownvote: (Int) -> Unit,
    onClearError: () -> Unit,
    onClearSuccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableIntStateOf(0) }

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Win95Colors.WindowBackground)
        ) {
            Win95TitleBar(title = "WarnABrotha - ${uiState.selectedLot?.code ?: "Loading..."}")

            BeveledBorder(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(4.dp)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Win95Colors.WindowBackground)
                ) {
                    Win95TabBar(
                        selectedTab = selectedTab,
                        onTabSelected = { selectedTab = it }
                    )

                    when (selectedTab) {
                        0 -> ReportTab(
                            selectedLot = uiState.selectedLot,
                            currentSession = uiState.currentSession,
                            displayedProbability = uiState.displayedProbability,
                            isLoading = uiState.isLoading,
                            onReportTaps = onReportTaps,
                            onCheckIn = onCheckIn,
                            onCheckOut = onCheckOut,
                            onRefresh = onRefresh,
                            modifier = Modifier.weight(1f)
                        )
                        1 -> FeedTab(
                            parkingLots = uiState.parkingLots,
                            selectedLotId = uiState.selectedLotId,
                            feed = uiState.feed,
                            onLotSelected = onLotSelected,
                            onUpvote = onUpvote,
                            onDownvote = onDownvote,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
        }

        // Error popup
        if (uiState.error != null) {
            Win95Popup(
                title = "Error",
                message = uiState.error,
                onDismiss = onClearError
            )
        }

        // Success popup
        if (uiState.successMessage != null) {
            Win95Popup(
                title = "Success",
                message = uiState.successMessage,
                onDismiss = onClearSuccess
            )
        }
    }
}
