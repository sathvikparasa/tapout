package com.warnabrotha.app.ui.screens

import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
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
import com.warnabrotha.app.ui.theme.*
import com.warnabrotha.app.ui.viewmodel.AppUiState
import com.warnabrotha.app.ui.viewmodel.ScanState

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
    onTakePhoto: () -> Unit,
    onPickFromLibrary: () -> Unit,
    onSubmitScan: () -> Unit,
    onResetScan: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableIntStateOf(0) }

    val newReportsCount = if (uiState.feedFilterLotId == null) {
        uiState.allFeedSightings.count { it.minutesAgo < 30 }
    } else {
        uiState.feed?.sightings?.count { it.minutesAgo < 30 } ?: 0
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Background)
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Content area
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) {
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
                    2 -> ScanTab(
                        scanState = uiState.scanState,
                        scanImageUri = uiState.scanImageUri,
                        scanResult = uiState.scanResult,
                        scanError = uiState.scanError,
                        isLoading = uiState.isLoading,
                        onTakePhoto = onTakePhoto,
                        onPickFromLibrary = onPickFromLibrary,
                        onSubmitScan = onSubmitScan,
                        onResetScan = onResetScan,
                        modifier = Modifier.fillMaxSize()
                    )
                    3 -> MapTab(
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

            // Bottom navigation bar
            AppBottomNav(
                selectedTab = selectedTab,
                onTabSelected = { selectedTab = it },
                newReportsCount = newReportsCount
            )
        }

        // Snackbars
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 96.dp)
        ) {
            uiState.error?.let { error ->
                Snackbar(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                    containerColor = Red500,
                    contentColor = TextOnPrimary,
                    shape = RoundedCornerShape(12.dp),
                    dismissAction = {
                        TextButton(onClick = onClearError) {
                            Text("OK", color = TextOnPrimary, fontWeight = FontWeight.Bold)
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
                    contentColor = TextOnPrimary,
                    shape = RoundedCornerShape(12.dp),
                    dismissAction = {
                        TextButton(onClick = onClearSuccess) {
                            Text("OK", color = TextOnPrimary, fontWeight = FontWeight.Bold)
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
private fun AppBottomNav(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit,
    newReportsCount: Int
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Surface.copy(alpha = 0.95f))
            .border(
                width = 1.dp,
                color = BorderSubtle,
                shape = RoundedCornerShape(0.dp)
            )
            .padding(top = 12.dp, bottom = 8.dp)
            .navigationBarsPadding(),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically
    ) {
        NavTab(
            icon = Icons.Outlined.GridView,
            label = "Home",
            isSelected = selectedTab == 0,
            onClick = { onTabSelected(0) }
        )

        // Feed tab with notification badge
        Box {
            NavTab(
                icon = Icons.Outlined.RssFeed,
                label = "Feed",
                isSelected = selectedTab == 1,
                onClick = { onTabSelected(1) }
            )
            if (newReportsCount > 0) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .offset(x = 8.dp, y = (-4).dp)
                        .size(16.dp)
                        .border(2.dp, Surface, CircleShape)
                        .background(BadgeRed, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = if (newReportsCount > 9) "+" else newReportsCount.toString(),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 8.sp,
                            lineHeight = 8.sp
                        ),
                        fontWeight = FontWeight.Bold,
                        color = TextOnPrimary
                    )
                }
            }
        }

        NavTab(
            icon = Icons.Outlined.DocumentScanner,
            label = "Scan",
            isSelected = selectedTab == 2,
            onClick = { onTabSelected(2) }
        )

        NavTab(
            icon = Icons.Outlined.Map,
            label = "Map",
            isSelected = selectedTab == 3,
            onClick = { onTabSelected(3) }
        )
    }
}

@Composable
private fun NavTab(
    icon: ImageVector,
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val color = if (isSelected) Green500 else NavInactive

    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 24.dp, vertical = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = color,
            modifier = Modifier.size(28.dp)
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.ExtraBold,
                letterSpacing = (-0.5).sp
            ),
            color = color
        )
    }
}
