package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.ui.components.*
import com.warnabrotha.app.ui.theme.Win95Colors

@Composable
fun ReportTab(
    selectedLot: ParkingLotWithStats?,
    currentSession: ParkingSession?,
    displayedProbability: Double,
    isLoading: Boolean,
    onReportTaps: () -> Unit,
    onCheckIn: () -> Unit,
    onCheckOut: () -> Unit,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isParked = currentSession != null

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Win95Colors.WindowBackground)
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Lot name
        if (selectedLot != null) {
            Text(
                text = selectedLot.name,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = Win95Colors.TitleBar,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )

            Spacer(modifier = Modifier.height(16.dp))
        }

        // Probability meter
        Win95ProbabilityMeter(
            probability = displayedProbability,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Report TAPS button
        Win95BigButton(
            title = "I SAW TAPS",
            subtitle = "Tap to report a sighting",
            onClick = onReportTaps,
            enabled = !isLoading,
            backgroundColor = Win95Colors.DangerRed,
            textColor = Win95Colors.TitleBarText,
            height = 120.dp
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Check in/out button
        if (isParked) {
            Win95BigButton(
                title = "I'M LEAVING",
                subtitle = "Tap to check out",
                onClick = onCheckOut,
                enabled = !isLoading,
                backgroundColor = Win95Colors.WarningYellow,
                textColor = Win95Colors.TitleBarText,
                height = 72.dp
            )
        } else {
            Win95BigButton(
                title = "I PARKED HERE",
                subtitle = "Tap to check in",
                onClick = onCheckIn,
                enabled = !isLoading,
                backgroundColor = Win95Colors.SafeGreen,
                textColor = Win95Colors.TitleBarText,
                height = 72.dp
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Refresh button
        Win95Button(
            text = "↻ Refresh",
            onClick = onRefresh,
            enabled = !isLoading,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        )

        if (isLoading) {
            Spacer(modifier = Modifier.height(8.dp))
            CircularProgressIndicator(
                color = Win95Colors.TitleBar,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )
        }

        Spacer(modifier = Modifier.weight(1f))

        // Status bar
        Win95StatusBar(
            activeParkers = selectedLot?.activeParkers ?: 0,
            recentReports = selectedLot?.recentSightings ?: 0,
            isParked = isParked
        )
    }
}
