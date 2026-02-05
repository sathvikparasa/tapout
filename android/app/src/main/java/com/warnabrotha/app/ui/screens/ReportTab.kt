package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.Canvas
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.ui.components.*
import com.warnabrotha.app.ui.theme.*

@Composable
fun ReportTab(
    selectedLot: ParkingLotWithStats?,
    parkingLots: List<ParkingLot>,
    currentSession: ParkingSession?,
    displayedProbability: Double,
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

        // === PRIMARY ACTIONS - HUGE BUTTONS ===
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
                .weight(0.8f)
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
                    .weight(0.8f)
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
                    .weight(0.8f)
            )
        }

        Spacer(modifier = Modifier.weight(0.1f))

        // === FOOTER - Stats ===
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(Black800, RoundedCornerShape(12.dp))
                .padding(vertical = 16.dp, horizontal = 8.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            SmallStat(
                value = "$totalParkedGlobal",
                label = "parked",
                color = TextWhite
            )
            StatDivider()
            RiskGaugeStat(
                probability = displayedProbability
            )
            StatDivider()
            SmallStat(
                value = "$totalRegisteredDevices",
                label = "users",
                color = TextWhite
            )
        }
    }
}

@Composable
private fun StatDivider() {
    Box(
        modifier = Modifier
            .width(1.dp)
            .height(40.dp)
            .background(Border)
    )
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

@Composable
private fun SmallStat(
    value: String,
    label: String,
    color: Color
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Black,
            color = color
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Medium,
            color = TextMuted,
            letterSpacing = 1.sp
        )
    }
}

@Composable
private fun RiskGaugeStat(
    probability: Double
) {
    val riskLevel = when {
        probability < 0.33 -> "Low"
        probability < 0.66 -> "Med"
        else -> "High"
    }
    val riskColor = when {
        probability < 0.33 -> Green500
        probability < 0.66 -> Amber500
        else -> Red500
    }

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        // Speedometer gauge
        Box(
            modifier = Modifier.size(48.dp),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val strokeWidth = 5.dp.toPx()
                val radius = (size.minDimension - strokeWidth) / 2
                val center = Offset(size.width / 2, size.height / 2)

                // Background arc (gray)
                drawArc(
                    color = Black600,
                    startAngle = 135f,
                    sweepAngle = 270f,
                    useCenter = false,
                    topLeft = Offset(center.x - radius, center.y - radius),
                    size = Size(radius * 2, radius * 2),
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )

                // Filled arc based on probability
                val sweepAngle = (probability * 270f).toFloat()
                drawArc(
                    color = riskColor,
                    startAngle = 135f,
                    sweepAngle = sweepAngle,
                    useCenter = false,
                    topLeft = Offset(center.x - radius, center.y - radius),
                    size = Size(radius * 2, radius * 2),
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )
            }

            // Risk level text inside gauge
            Text(
                text = riskLevel,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Black,
                color = riskColor
            )
        }

        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = "RISK",
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Medium,
            color = TextMuted,
            letterSpacing = 1.sp
        )
    }
}
