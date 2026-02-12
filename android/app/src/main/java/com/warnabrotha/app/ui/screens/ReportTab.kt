package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.data.model.PredictionResponse
import com.warnabrotha.app.ui.components.*
import com.warnabrotha.app.ui.theme.*

@Composable
fun ReportTab(
    selectedLot: ParkingLotWithStats?,
    parkingLots: List<ParkingLot>,
    currentSession: ParkingSession?,
    prediction: PredictionResponse?,
    totalParkedGlobal: Int,
    totalRegisteredDevices: Int,
    isLoading: Boolean,
    onReportTaps: () -> Unit,
    onCheckIn: () -> Unit,
    onCheckOut: () -> Unit,
    onRefresh: () -> Unit,
    onLotSelected: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    val isParked = currentSession != null
    var dropdownExpanded by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Black900)
            .padding(16.dp)
    ) {
        // === HEADER - Location Dropdown ===
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Location dropdown
            Box {
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Black700)
                        .clickable { dropdownExpanded = true }
                        .padding(horizontal = 12.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Column {
                        Text(
                            text = selectedLot?.name ?: "Select Location",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = TextWhite
                        )
                        Text(
                            text = selectedLot?.code ?: "---",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Black,
                            color = Amber500
                        )
                    }
                    Icon(
                        imageVector = if (dropdownExpanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                        contentDescription = "Select location",
                        tint = TextGray,
                        modifier = Modifier.size(24.dp)
                    )
                }

                DropdownMenu(
                    expanded = dropdownExpanded,
                    onDismissRequest = { dropdownExpanded = false },
                    modifier = Modifier
                        .background(Black700)
                ) {
                    parkingLots.forEach { lot ->
                        DropdownMenuItem(
                            text = {
                                Row(
                                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = lot.code,
                                        style = MaterialTheme.typography.labelLarge,
                                        fontWeight = FontWeight.Black,
                                        color = Amber500
                                    )
                                    Text(
                                        text = lot.name,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = if (lot.id == selectedLot?.id) TextWhite else TextGray
                                    )
                                }
                            },
                            onClick = {
                                onLotSelected(lot.id)
                                dropdownExpanded = false
                            },
                            modifier = Modifier.background(
                                if (lot.id == selectedLot?.id) Black600 else Color.Transparent
                            )
                        )
                    }
                }
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                StatusBadge(
                    isActive = isParked,
                    activeText = "Parked",
                    inactiveText = "Not parked"
                )
                IconButton(
                    onClick = onRefresh,
                    enabled = !isLoading,
                    modifier = Modifier.size(36.dp)
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            color = Amber500,
                            strokeWidth = 2.dp
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh",
                            tint = TextGray,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.weight(0.1f))

        // === PRIMARY ACTIONS ===
        // Report Button
        BigSquareButton(
            text = "REPORT TAPS",
            subtitle = "Warn others nearby",
            icon = Icons.Default.Warning,
            onClick = onReportTaps,
            enabled = !isLoading,
            gradient = listOf(Red500, Red600),
            modifier = Modifier
                .fillMaxWidth()
                .weight(0.5f)
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Park / Checkout Button
        if (isParked) {
            BigSquareButton(
                text = "CHECK OUT",
                subtitle = "Stop receiving alerts",
                icon = Icons.Default.Logout,
                onClick = onCheckOut,
                enabled = !isLoading,
                gradient = listOf(Black600, Black700),
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(0.5f)
            )
        } else {
            BigSquareButton(
                text = "I'M PARKED",
                subtitle = "Get notified if TAPS is spotted",
                icon = Icons.Default.LocalParking,
                onClick = onCheckIn,
                enabled = !isLoading,
                gradient = listOf(Blue500, Blue600),
                textColor = TextWhite,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(0.5f)
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // === Risk Card ===
        RiskCard(
            riskLevel = prediction?.riskLevel ?: "MEDIUM",
            riskMessage = prediction?.riskMessage ?: "Loading...",
            modifier = Modifier.weight(0.4f)
        )
    }
}

@Composable
private fun RiskCard(
    riskLevel: String,
    riskMessage: String,
    modifier: Modifier = Modifier
) {
    val riskColor = when (riskLevel) {
        "HIGH" -> Red500
        "MEDIUM" -> Amber500
        "LOW" -> Green500
        else -> TextMuted
    }
    val riskBars = when (riskLevel) {
        "HIGH" -> 3
        "MEDIUM" -> 2
        "LOW" -> 1
        else -> 2
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Black800, RoundedCornerShape(12.dp))
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Risk bars (3 bars of increasing height)
        Row(
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            verticalAlignment = Alignment.Bottom,
            modifier = Modifier.height(48.dp)
        ) {
            for (i in 1..3) {
                Box(
                    modifier = Modifier
                        .width(12.dp)
                        .fillMaxHeight(fraction = i / 3f)
                        .background(
                            if (i <= riskBars) riskColor else Black600,
                            RoundedCornerShape(2.dp)
                        )
                )
            }
        }

        // Risk level + message stacked vertically
        Column(
            verticalArrangement = Arrangement.spacedBy(4.dp),
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = "$riskLevel RISK",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Black,
                color = riskColor
            )
            Text(
                text = riskMessage,
                style = MaterialTheme.typography.bodyMedium,
                color = TextGray,
                maxLines = 2
            )
        }
    }
}

@Composable
private fun BigSquareButton(
    text: String,
    subtitle: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    gradient: List<Color>,
    textColor: Color = TextWhite
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(24.dp))
            .background(
                Brush.verticalGradient(
                    colors = if (enabled) gradient else gradient.map { it.copy(alpha = 0.5f) }
                )
            )
            .then(
                if (enabled) Modifier.clickable(onClick = onClick) else Modifier
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = textColor,
                modifier = Modifier.size(64.dp)
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = text,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Black,
                color = textColor
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodyLarge,
                color = textColor.copy(alpha = 0.8f)
            )
        }
    }
}

