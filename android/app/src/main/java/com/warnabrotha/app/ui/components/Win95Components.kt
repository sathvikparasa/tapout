package com.warnabrotha.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.FeedSighting
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.theme.Win95Colors

@Composable
fun BeveledBorder(
    modifier: Modifier = Modifier,
    raised: Boolean = true,
    borderWidth: Dp = 2.dp,
    content: @Composable BoxScope.() -> Unit
) {
    val topLeftColor = if (raised) Win95Colors.ButtonHighlight else Win95Colors.ButtonDarkShadow
    val bottomRightColor = if (raised) Win95Colors.ButtonDarkShadow else Win95Colors.ButtonHighlight

    Box(
        modifier = modifier
            .drawBehind {
                val strokeWidth = borderWidth.toPx()
                // Top edge
                drawLine(
                    color = topLeftColor,
                    start = Offset(0f, 0f),
                    end = Offset(size.width, 0f),
                    strokeWidth = strokeWidth
                )
                // Left edge
                drawLine(
                    color = topLeftColor,
                    start = Offset(0f, 0f),
                    end = Offset(0f, size.height),
                    strokeWidth = strokeWidth
                )
                // Bottom edge
                drawLine(
                    color = bottomRightColor,
                    start = Offset(0f, size.height),
                    end = Offset(size.width, size.height),
                    strokeWidth = strokeWidth
                )
                // Right edge
                drawLine(
                    color = bottomRightColor,
                    start = Offset(size.width, 0f),
                    end = Offset(size.width, size.height),
                    strokeWidth = strokeWidth
                )
            }
            .background(Win95Colors.ButtonFace),
        content = content
    )
}

@Composable
fun Win95TitleBar(
    title: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(32.dp)
            .background(Win95Colors.TitleBar)
            .padding(horizontal = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            color = Win95Colors.TitleBarText,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.SansSerif,
            modifier = Modifier.weight(1f)
        )

        Row(horizontalArrangement = Arrangement.spacedBy(2.dp)) {
            TitleBarButton("_")
            TitleBarButton("□")
            TitleBarButton("×")
        }
    }
}

@Composable
private fun TitleBarButton(symbol: String) {
    BeveledBorder(
        modifier = Modifier.size(20.dp),
        raised = true
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = symbol,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = Win95Colors.TextPrimary
            )
        }
    }
}

@Composable
fun Win95TabBar(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 4.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        Win95Tab(
            title = "Report",
            isSelected = selectedTab == 0,
            onClick = { onTabSelected(0) },
            modifier = Modifier.weight(1f)
        )
        Win95Tab(
            title = "Feed",
            isSelected = selectedTab == 1,
            onClick = { onTabSelected(1) },
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
fun Win95Tab(
    title: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    BeveledBorder(
        modifier = modifier
            .height(28.dp)
            .clickable(onClick = onClick),
        raised = isSelected
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    if (isSelected) Win95Colors.WindowBackground
                    else Win95Colors.ButtonShadow
                ),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = title,
                fontSize = 12.sp,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                color = Win95Colors.TextPrimary
            )
        }
    }
}

@Composable
fun Win95Button(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    backgroundColor: Color = Win95Colors.ButtonFace,
    textColor: Color = Win95Colors.TextPrimary
) {
    BeveledBorder(
        modifier = modifier
            .height(32.dp)
            .clickable(enabled = enabled, onClick = onClick),
        raised = true
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(if (enabled) backgroundColor else Win95Colors.ButtonShadow)
                .padding(horizontal = 16.dp),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = text,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = if (enabled) textColor else Win95Colors.TextSecondary
            )
        }
    }
}

@Composable
fun Win95BigButton(
    title: String,
    subtitle: String? = null,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    backgroundColor: Color = Win95Colors.ButtonFace,
    textColor: Color = Win95Colors.TextPrimary,
    height: Dp = 120.dp
) {
    BeveledBorder(
        modifier = modifier
            .fillMaxWidth()
            .height(height)
            .clickable(enabled = enabled, onClick = onClick),
        raised = true
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(if (enabled) backgroundColor else Win95Colors.ButtonShadow),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = title,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (enabled) textColor else Win95Colors.TextSecondary,
                    textAlign = TextAlign.Center
                )
                if (subtitle != null) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = subtitle,
                        fontSize = 14.sp,
                        color = if (enabled) textColor.copy(alpha = 0.8f) else Win95Colors.TextSecondary,
                        textAlign = TextAlign.Center
                    )
                }
            }
        }
    }
}

@Composable
fun Win95ProbabilityMeter(
    probability: Double,
    modifier: Modifier = Modifier
) {
    val color = when {
        probability < 0.33 -> Win95Colors.SafeGreen
        probability < 0.66 -> Win95Colors.WarningYellow
        else -> Win95Colors.DangerRed
    }

    val riskLevel = when {
        probability < 0.33 -> "LOW RISK"
        probability < 0.66 -> "MEDIUM RISK"
        else -> "HIGH RISK"
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "TAPS Probability",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = Win95Colors.TextPrimary
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Progress bar container
        BeveledBorder(
            modifier = Modifier
                .fillMaxWidth()
                .height(32.dp),
            raised = false
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Color.White)
                    .padding(2.dp)
            ) {
                // Filled portion
                Box(
                    modifier = Modifier
                        .fillMaxHeight()
                        .fillMaxWidth(probability.toFloat().coerceIn(0f, 1f))
                        .background(color)
                )

                // Percentage text
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "${(probability * 100).toInt()}%",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Win95Colors.TextPrimary
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = riskLevel,
            fontSize = 18.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
    }
}

@Composable
fun Win95LotSelector(
    lots: List<ParkingLot>,
    selectedLotId: Int?,
    onLotSelected: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyRow(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        contentPadding = PaddingValues(horizontal = 8.dp)
    ) {
        items(lots) { lot ->
            val isSelected = lot.id == selectedLotId
            BeveledBorder(
                modifier = Modifier
                    .clickable { onLotSelected(lot.id) },
                raised = isSelected
            ) {
                Box(
                    modifier = Modifier
                        .background(
                            if (isSelected) Win95Colors.TitleBar else Win95Colors.ButtonFace
                        )
                        .padding(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Text(
                        text = lot.code,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = if (isSelected) Color.White else Win95Colors.TextPrimary
                    )
                }
            }
        }
    }
}

@Composable
fun Win95FeedItem(
    sighting: FeedSighting,
    onUpvote: () -> Unit,
    onDownvote: () -> Unit,
    modifier: Modifier = Modifier
) {
    val timeColor = when {
        sighting.minutesAgo < 30 -> Win95Colors.DangerRed
        sighting.minutesAgo < 90 -> Win95Colors.WarningYellow
        else -> Win95Colors.TextSecondary
    }

    val timeText = when {
        sighting.minutesAgo < 60 -> "${sighting.minutesAgo}m ago"
        else -> "${sighting.minutesAgo / 60}h ${sighting.minutesAgo % 60}m ago"
    }

    BeveledBorder(
        modifier = modifier.fillMaxWidth(),
        raised = true
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Win95Colors.WindowBackground)
                .padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = timeText,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = timeColor
                )

                Text(
                    text = sighting.parkingLotCode ?: "",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Win95Colors.TitleBar
                )
            }

            if (!sighting.notes.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = sighting.notes,
                    fontSize = 12.sp,
                    color = Win95Colors.TextPrimary
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Vote buttons
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    VoteButton(
                        text = "▲ ${sighting.upvotes}",
                        isSelected = sighting.userVote == "upvote",
                        onClick = onUpvote
                    )
                    VoteButton(
                        text = "▼ ${sighting.downvotes}",
                        isSelected = sighting.userVote == "downvote",
                        onClick = onDownvote
                    )
                }

                // Net score
                Text(
                    text = "Score: ${sighting.netScore}",
                    fontSize = 12.sp,
                    color = when {
                        sighting.netScore > 0 -> Win95Colors.SafeGreen
                        sighting.netScore < 0 -> Win95Colors.DangerRed
                        else -> Win95Colors.TextSecondary
                    }
                )
            }
        }
    }
}

@Composable
private fun VoteButton(
    text: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    BeveledBorder(
        modifier = Modifier
            .clickable(onClick = onClick),
        raised = !isSelected
    ) {
        Box(
            modifier = Modifier
                .background(
                    if (isSelected) Win95Colors.TitleBar else Win95Colors.ButtonFace
                )
                .padding(horizontal = 12.dp, vertical = 4.dp)
        ) {
            Text(
                text = text,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = if (isSelected) Color.White else Win95Colors.TextPrimary
            )
        }
    }
}

@Composable
fun Win95StatusBar(
    activeParkers: Int,
    recentReports: Int,
    isParked: Boolean,
    modifier: Modifier = Modifier
) {
    BeveledBorder(
        modifier = modifier.fillMaxWidth(),
        raised = false
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(Win95Colors.WindowBackground)
                .padding(horizontal = 8.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            StatusItem(label = "Active", value = activeParkers.toString())
            StatusItem(label = "Reports", value = recentReports.toString())
            StatusItem(
                label = "Status",
                value = if (isParked) "Parked" else "Not parked",
                valueColor = if (isParked) Win95Colors.SafeGreen else Win95Colors.TextSecondary
            )
        }
    }
}

@Composable
private fun StatusItem(
    label: String,
    value: String,
    valueColor: Color = Win95Colors.TextPrimary
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = label,
            fontSize = 10.sp,
            color = Win95Colors.TextSecondary
        )
        Text(
            text = value,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = valueColor
        )
    }
}

@Composable
fun Win95Popup(
    title: String,
    message: String,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.5f))
            .clickable(onClick = onDismiss),
        contentAlignment = Alignment.Center
    ) {
        BeveledBorder(
            modifier = modifier
                .width(300.dp)
                .clickable(enabled = false) {}
        ) {
            Column(
                modifier = Modifier.background(Win95Colors.WindowBackground)
            ) {
                Win95TitleBar(title = title)

                Column(
                    modifier = Modifier.padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = message,
                        fontSize = 14.sp,
                        color = Win95Colors.TextPrimary,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Win95Button(
                        text = "OK",
                        onClick = onDismiss,
                        modifier = Modifier.width(100.dp)
                    )
                }
            }
        }
    }
}
