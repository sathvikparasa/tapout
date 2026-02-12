package com.warnabrotha.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.components.NotificationBadge
import com.warnabrotha.app.ui.theme.*
import com.warnabrotha.app.ui.viewmodel.AppUiState

@Composable
fun MainScreen(
    uiState: AppUiState,
    onReportTaps: () -> Unit,
    onReportTapsAtLot: (Int) -> Unit,
    onCheckIn: () -> Unit,
    onCheckInAtLot: (Int) -> Unit,
    onCheckOut: () -> Unit,
    onRefresh: () -> Unit,
    onLotSelected: (Int) -> Unit,
    onFeedFilterSelected: (Int?) -> Unit,
    onUpvote: (Int) -> Unit,
    onDownvote: (Int) -> Unit,
    onClearError: () -> Unit,
    onClearSuccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableIntStateOf(0) }

    // Calculate new reports from all feed sightings
    val newReportsCount = if (uiState.feedFilterLotId == null) {
        uiState.allFeedSightings.count { it.minutesAgo < 30 }
    } else {
        uiState.feed?.sightings?.count { it.minutesAgo < 30 } ?: 0
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Black900)
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Content area
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
                // Calculate global stats
                val totalParkedGlobal = uiState.lotStats.values.sumOf { it.activeParkers }

                when (selectedTab) {
                    0 -> ReportTab(
                        selectedLot = uiState.selectedLot,
                        parkingLots = uiState.parkingLots,
                        currentSession = uiState.currentSession,
                        prediction = uiState.prediction,
                        totalParkedGlobal = totalParkedGlobal,
                        totalRegisteredDevices = uiState.totalRegisteredDevices,
                        isLoading = uiState.isLoading,
                        onReportTaps = onReportTaps,
                        onCheckIn = onCheckIn,
                        onCheckOut = onCheckOut,
                        onRefresh = onRefresh,
                        onLotSelected = onLotSelected,
                        modifier = Modifier.fillMaxSize()
                    )
                    1 -> FeedTab(
                        parkingLots = uiState.parkingLots,
                        feedFilterLotId = uiState.feedFilterLotId,
                        feed = uiState.feed,
                        allFeedSightings = uiState.allFeedSightings,
                        allFeedsTotalCount = uiState.allFeedsTotalCount,
                        isLoading = uiState.isLoading,
                        onFeedFilterSelected = onFeedFilterSelected,
                        onUpvote = onUpvote,
                        onDownvote = onDownvote,
                        modifier = Modifier.fillMaxSize()
                    )
                    2 -> MapTab(
                        parkingLots = uiState.parkingLots,
                        lotStats = uiState.lotStats,
                        currentSession = uiState.currentSession,
                        isLoading = uiState.isLoading,
                        onCheckIn = onCheckInAtLot,
                        onCheckOut = onCheckOut,
                        onReportTaps = onReportTapsAtLot,
                        modifier = Modifier.fillMaxSize()
                    )
                }
            }

            // Navigation bar
            TacticalNavBar(
                selectedTab = selectedTab,
                onTabSelected = { selectedTab = it },
                newReportsCount = newReportsCount
            )
        }

        // Snackbars
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 70.dp)
        ) {
            uiState.error?.let { error ->
                Snackbar(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                    containerColor = Red500,
                    contentColor = TextWhite,
                    shape = RoundedCornerShape(8.dp),
                    dismissAction = {
                        TextButton(onClick = onClearError) {
                            Text("OK", color = TextWhite, fontWeight = FontWeight.Bold)
                        }
                    }
                ) {
                    Text(error, style = MaterialTheme.typography.bodySmall)
                }
            }

            uiState.successMessage?.let { message ->
                Snackbar(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                    containerColor = Green500,
                    contentColor = Black900,
                    shape = RoundedCornerShape(8.dp),
                    dismissAction = {
                        TextButton(onClick = onClearSuccess) {
                            Text("OK", color = Black900, fontWeight = FontWeight.Bold)
                        }
                    }
                ) {
                    Text(message, style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun TacticalNavBar(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit,
    newReportsCount: Int
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Black800)
            .border(1.dp, Border, RoundedCornerShape(0.dp))
            .padding(8.dp)
            .navigationBarsPadding(),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        // Tab 0: COMMAND
        NavTab(
            icon = Icons.Outlined.Shield,
            selectedIcon = Icons.Filled.Shield,
            label = "COMMAND",
            isSelected = selectedTab == 0,
            onClick = { onTabSelected(0) }
        )

        // Tab 1: FEED with notification badge
        Box {
            NavTab(
                icon = Icons.Outlined.Sensors,
                selectedIcon = Icons.Filled.Sensors,
                label = "FEED",
                isSelected = selectedTab == 1,
                onClick = { onTabSelected(1) }
            )
            if (newReportsCount > 0) {
                NotificationBadge(
                    count = newReportsCount,
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .offset(x = 4.dp, y = (-2).dp)
                )
            }
        }

        // Tab 2: MAP (rightmost)
        NavTab(
            icon = Icons.Outlined.Map,
            selectedIcon = Icons.Filled.Map,
            label = "MAP",
            isSelected = selectedTab == 2,
            onClick = { onTabSelected(2) }
        )
    }
}

@Composable
private fun NavTab(
    icon: ImageVector,
    selectedIcon: ImageVector,
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val color = if (isSelected) Amber500 else TextMuted

    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(if (isSelected) AmberGlow else Color.Transparent)
            .border(
                1.dp,
                if (isSelected) Amber500.copy(alpha = 0.3f) else Color.Transparent,
                RoundedCornerShape(6.dp)
            )
            .clickable(onClick = onClick)
            .padding(horizontal = 24.dp, vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = if (isSelected) selectedIcon else icon,
            contentDescription = label,
            tint = color,
            modifier = Modifier.size(22.dp)
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
            color = color,
            letterSpacing = 1.sp
        )
    }
}
