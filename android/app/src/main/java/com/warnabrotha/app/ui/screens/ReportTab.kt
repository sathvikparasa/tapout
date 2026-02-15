package com.warnabrotha.app.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.data.model.PredictionResponse
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
            .background(Background)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
    ) {
        Spacer(modifier = Modifier.height(16.dp))

        // === HEADER — TapOut logo + notification bell ===
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = buildAnnotatedString {
                    withStyle(SpanStyle(color = TextPrimaryAlt)) {
                        append("Tap")
                    }
                    withStyle(SpanStyle(color = Green500)) {
                        append("Out")
                    }
                },
                style = MaterialTheme.typography.displayMedium
            )

            Box(
                modifier = Modifier
                    .size(44.dp)
                    .shadow(2.dp, CircleShape, ambientColor = ShadowLight, spotColor = ShadowLight)
                    .background(Surface, CircleShape)
                    .border(1.dp, BorderLight, CircleShape)
                    .clip(CircleShape)
                    .clickable(onClick = onRefresh),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Outlined.Notifications,
                    contentDescription = "Refresh",
                    tint = TextPrimary,
                    modifier = Modifier.size(22.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // === LOT SELECTOR ===
        Text(
            text = "SELECT PARKING ZONE",
            style = MaterialTheme.typography.labelMedium,
            color = Green500
        )

        Spacer(modifier = Modifier.height(8.dp))

        Box {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .shadow(2.dp, RoundedCornerShape(24.dp), ambientColor = ShadowLight, spotColor = ShadowLight)
                    .background(Surface, RoundedCornerShape(24.dp))
                    .clip(RoundedCornerShape(24.dp))
                    .clickable { dropdownExpanded = true }
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = selectedLot?.let { "${it.name} (${it.code})" } ?: "Select Location",
                    style = MaterialTheme.typography.headlineMedium,
                    color = TextPrimary
                )
                Icon(
                    imageVector = if (dropdownExpanded) Icons.Default.KeyboardArrowUp
                        else Icons.Default.KeyboardArrowDown,
                    contentDescription = "Select location",
                    tint = TextSecondary,
                    modifier = Modifier.size(24.dp)
                )
            }

            DropdownMenu(
                expanded = dropdownExpanded,
                onDismissRequest = { dropdownExpanded = false },
                modifier = Modifier.background(Surface)
            ) {
                parkingLots.forEach { lot ->
                    DropdownMenuItem(
                        text = {
                            Text(
                                text = "${lot.name} (${lot.code})",
                                style = MaterialTheme.typography.bodyLarge,
                                color = if (lot.id == selectedLot?.id) Green500 else TextPrimary
                            )
                        },
                        onClick = {
                            onLotSelected(lot.id)
                            dropdownExpanded = false
                        },
                        modifier = Modifier.background(
                            if (lot.id == selectedLot?.id) GreenOverlay5 else Color.Transparent
                        )
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // === ACTION BUTTONS — side by side ===
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(IntrinsicSize.Min),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (isParked) {
                DashboardActionButton(
                    text = "CHECK OUT",
                    icon = Icons.Default.Logout,
                    containerColor = TextSecondary,
                    shadowColor = ShadowLight,
                    onClick = onCheckOut,
                    enabled = !isLoading,
                    modifier = Modifier.weight(1f)
                )
            } else {
                DashboardActionButton(
                    text = "CHECK IN",
                    icon = Icons.Default.LocalParking,
                    containerColor = Green500,
                    shadowColor = GreenShadow,
                    onClick = onCheckIn,
                    enabled = !isLoading,
                    modifier = Modifier.weight(1f)
                )
            }

            DashboardActionButton(
                text = "REPORT TAPS",
                icon = Icons.Outlined.Report,
                containerColor = Red500,
                shadowColor = RedShadow,
                onClick = onReportTaps,
                enabled = !isLoading,
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // === RISK METER CARD ===
        RiskMeterCard(prediction = prediction)

        Spacer(modifier = Modifier.height(20.dp))

        // === RECENT ACTIVITY ===
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Recent Activity",
                style = MaterialTheme.typography.headlineSmall,
                color = TextPrimary
            )
            Text(
                text = "View Map >",
                style = MaterialTheme.typography.titleSmall,
                color = Green500
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        prediction?.lastSightingLotName?.let { lotName ->
            val timeText = prediction.hoursSinceLastSighting?.let { hours ->
                when {
                    hours < 1.0 / 60 -> "JUST NOW"
                    hours < 1 -> "${(hours * 60).toInt()} MINS AGO"
                    hours < 24 -> "${hours.toInt()} HOURS AGO"
                    else -> "${(hours / 24).toInt()} DAYS AGO"
                }
            } ?: ""

            RecentActivityCard(
                title = "Taps spotted: $lotName",
                timeText = timeText
            )
        }

        if (isLoading) {
            Spacer(modifier = Modifier.height(16.dp))
            Box(
                modifier = Modifier.fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = Green500,
                    strokeWidth = 2.dp
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))
    }
}

// ─── Large rounded action button (CHECK IN / REPORT TAPS) ───

@Composable
private fun DashboardActionButton(
    text: String,
    icon: ImageVector,
    containerColor: Color,
    shadowColor: Color,
    onClick: () -> Unit,
    enabled: Boolean,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .aspectRatio(0.88f)
            .shadow(15.dp, RoundedCornerShape(40.dp), ambientColor = shadowColor, spotColor = shadowColor)
            .clip(RoundedCornerShape(40.dp))
            .background(if (enabled) containerColor else containerColor.copy(alpha = 0.5f))
            .then(if (enabled) Modifier.clickable(onClick = onClick) else Modifier),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = TextOnPrimary,
                modifier = Modifier.size(56.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = text,
                style = MaterialTheme.typography.titleSmall.copy(
                    fontFamily = DmSansFamily,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.sp
                ),
                color = TextOnPrimary
            )
        }
    }
}

// ─── Risk Meter Card ───

@Composable
private fun RiskMeterCard(prediction: PredictionResponse?) {
    val riskLevel = prediction?.riskLevel ?: "MEDIUM"
    val riskMessage = prediction?.riskMessage ?: "Loading..."

    val riskColor = when (riskLevel) {
        "HIGH" -> RiskHigh
        "MEDIUM" -> RiskMedium
        "LOW" -> RiskLow
        else -> TextMuted
    }
    val riskBars = when (riskLevel) {
        "HIGH" -> 3
        "MEDIUM" -> 2
        "LOW" -> 1
        else -> 2
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(2.dp, RoundedCornerShape(32.dp), ambientColor = ShadowLight, spotColor = ShadowLight)
            .background(Surface, RoundedCornerShape(32.dp))
            .border(1.dp, BorderLight, RoundedCornerShape(32.dp))
            .padding(20.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "CURRENT RISK METER",
                style = MaterialTheme.typography.labelMedium,
                color = TextSecondary
            )
            LiveBadge()
        }

        Spacer(modifier = Modifier.height(16.dp))

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 3 bars of increasing height
            Row(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.Bottom,
                modifier = Modifier.height(48.dp)
            ) {
                for (i in 1..3) {
                    Box(
                        modifier = Modifier
                            .width(14.dp)
                            .fillMaxHeight(fraction = i / 3f)
                            .background(
                                if (i <= riskBars) riskColor else RiskBarEmpty,
                                RoundedCornerShape(4.dp)
                            )
                    )
                }
            }

            Column {
                Text(
                    text = riskLevel,
                    style = MaterialTheme.typography.displayMedium,
                    color = riskColor
                )
                Text(
                    text = riskMessage,
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                    maxLines = 2
                )
            }
        }
    }
}

// ─── LIVE badge ───

@Composable
private fun LiveBadge() {
    val infiniteTransition = rememberInfiniteTransition(label = "livePulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800),
            repeatMode = RepeatMode.Reverse
        ),
        label = "livePulseAlpha"
    )

    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(LiveGreen.copy(alpha = alpha), CircleShape)
        )
        Text(
            text = "LIVE",
            style = MaterialTheme.typography.labelMedium.copy(letterSpacing = 0.5.sp),
            color = LiveGreen,
            fontWeight = FontWeight.Bold
        )
    }
}

// ─── Recent Activity Card ───

@Composable
private fun RecentActivityCard(
    title: String,
    timeText: String
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .shadow(2.dp, RoundedCornerShape(24.dp), ambientColor = ShadowLight, spotColor = ShadowLight)
            .background(Surface.copy(alpha = 0.9f), RoundedCornerShape(24.dp))
            .border(1.dp, BorderLight, RoundedCornerShape(24.dp))
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .background(RedOverlay10, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Outlined.Report,
                contentDescription = null,
                tint = Red500,
                modifier = Modifier.size(20.dp)
            )
        }

        Column {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = TextPrimary
            )
            Text(
                text = timeText,
                style = MaterialTheme.typography.labelMedium,
                color = TextMuted
            )
        }
    }
}
