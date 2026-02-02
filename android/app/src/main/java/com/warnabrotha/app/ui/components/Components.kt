package com.warnabrotha.app.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.FeedSighting
import com.warnabrotha.app.ui.theme.*

// ============================================
// TACTICAL ACTION BUTTONS
// ============================================

@Composable
fun TacticalButton(
    text: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    color: Color = Amber500,
    enabled: Boolean = true
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.height(52.dp),
        shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = color,
            contentColor = Black900,
            disabledContainerColor = color.copy(alpha = 0.4f),
            disabledContentColor = Black900.copy(alpha = 0.6f)
        ),
        contentPadding = PaddingValues(horizontal = 16.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(18.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = text.uppercase(),
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Black
        )
    }
}

@Composable
fun AlertButton(
    text: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    val infiniteTransition = rememberInfiniteTransition(label = "glow")
    val glowAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.6f,
        animationSpec = infiniteRepeatable(
            animation = tween(800),
            repeatMode = RepeatMode.Reverse
        ),
        label = "glowAlpha"
    )

    Box(
        modifier = modifier
            .height(52.dp)
            .clip(RoundedCornerShape(8.dp))
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Red500,
                        Red600
                    )
                )
            )
            .then(
                if (enabled) Modifier.clickable(onClick = onClick)
                else Modifier
            ),
        contentAlignment = Alignment.Center
    ) {
        // Glow effect
        Box(
            modifier = Modifier
                .matchParentSize()
                .background(Red500.copy(alpha = glowAlpha))
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = TextWhite,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = text.uppercase(),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Black,
                color = TextWhite
            )
        }
    }
}

// ============================================
// RISK INDICATOR - COMPACT
// ============================================

@Composable
fun RiskMeter(
    probability: Double,
    modifier: Modifier = Modifier
) {
    val animatedProb by animateFloatAsState(
        targetValue = probability.toFloat(),
        animationSpec = tween(600, easing = FastOutSlowInEasing),
        label = "prob"
    )

    val color = when {
        probability < 0.33 -> Green500
        probability < 0.66 -> Amber500
        else -> Red500
    }

    val label = when {
        probability < 0.33 -> "LOW"
        probability < 0.66 -> "MED"
        else -> "HIGH"
    }

    Row(
        modifier = modifier
            .background(Black700, RoundedCornerShape(6.dp))
            .border(1.dp, Border, RoundedCornerShape(6.dp))
            .padding(horizontal = 10.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // Mini arc gauge
        Box(
            modifier = Modifier.size(36.dp),
            contentAlignment = Alignment.Center
        ) {
            androidx.compose.foundation.Canvas(modifier = Modifier.fillMaxSize()) {
                val stroke = 4.dp.toPx()
                val radius = (size.minDimension - stroke) / 2
                val topLeft = Offset(stroke / 2, stroke / 2)

                drawArc(
                    color = Black500,
                    startAngle = 135f,
                    sweepAngle = 270f,
                    useCenter = false,
                    topLeft = topLeft,
                    size = Size(radius * 2, radius * 2),
                    style = Stroke(width = stroke, cap = StrokeCap.Round)
                )
                drawArc(
                    color = color,
                    startAngle = 135f,
                    sweepAngle = 270f * animatedProb,
                    useCenter = false,
                    topLeft = topLeft,
                    size = Size(radius * 2, radius * 2),
                    style = Stroke(width = stroke, cap = StrokeCap.Round)
                )
            }
            Text(
                text = "${(animatedProb * 100).toInt()}",
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = color,
                fontFamily = FontFamily.Monospace
            )
        }

        Column {
            Text(
                text = "RISK",
                style = MaterialTheme.typography.labelSmall,
                color = TextMuted,
                letterSpacing = 1.sp
            )
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Black,
                color = color
            )
        }
    }
}

// ============================================
// STAT CHIP - INLINE STATS
// ============================================

@Composable
fun StatChip(
    label: String,
    value: String,
    icon: ImageVector,
    color: Color = TextGray,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .background(Black700, RoundedCornerShape(6.dp))
            .border(1.dp, Border, RoundedCornerShape(6.dp))
            .padding(horizontal = 10.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(14.dp)
        )
        Text(
            text = value,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold,
            color = TextWhite,
            fontFamily = FontFamily.Monospace
        )
        Text(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = TextMuted
        )
    }
}

// ============================================
// STATUS INDICATOR - PARKING STATE
// ============================================

@Composable
fun StatusBadge(
    isActive: Boolean,
    activeText: String,
    inactiveText: String,
    modifier: Modifier = Modifier
) {
    val color = if (isActive) Green500 else TextMuted

    Row(
        modifier = modifier
            .background(
                if (isActive) GreenGlow else Color.Transparent,
                RoundedCornerShape(4.dp)
            )
            .border(1.dp, if (isActive) Green500.copy(alpha = 0.5f) else Border, RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        if (isActive) {
            PulsingDot(color = Green500, size = 6.dp)
        } else {
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .background(TextMuted, CircleShape)
            )
        }
        Text(
            text = if (isActive) activeText.uppercase() else inactiveText.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = color,
            letterSpacing = 0.5.sp
        )
    }
}

@Composable
fun PulsingDot(
    color: Color = Green500,
    size: Dp = 8.dp
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    Box(
        modifier = Modifier
            .size(size)
            .clip(CircleShape)
            .background(color.copy(alpha = alpha))
    )
}

// ============================================
// FEED CARD - SIGHTING REPORT
// ============================================

@Composable
fun SightingCard(
    sighting: FeedSighting,
    onUpvote: () -> Unit,
    onDownvote: () -> Unit,
    modifier: Modifier = Modifier
) {
    val timeColor = when {
        sighting.minutesAgo < 30 -> Red500
        sighting.minutesAgo < 90 -> Amber500
        else -> TextMuted
    }

    val timeText = when {
        sighting.minutesAgo < 1 -> "NOW"
        sighting.minutesAgo < 60 -> "${sighting.minutesAgo}m"
        else -> "${sighting.minutesAgo / 60}h${sighting.minutesAgo % 60}m"
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Black700, RoundedCornerShape(8.dp))
            .border(1.dp, Border, RoundedCornerShape(8.dp))
            .padding(10.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // Time indicator
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.width(40.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .background(timeColor, CircleShape)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = timeText,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = timeColor,
                fontFamily = FontFamily.Monospace
            )
        }

        // Content
        Column(modifier = Modifier.weight(1f)) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(
                    text = sighting.parkingLotCode ?: "???",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = Amber500
                )
                if (!sighting.notes.isNullOrBlank()) {
                    Text(
                        text = "•",
                        color = TextMuted
                    )
                    Text(
                        text = sighting.notes,
                        style = MaterialTheme.typography.bodySmall,
                        color = TextGray,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        }

        // Votes
        Row(
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            VoteButton(
                count = sighting.upvotes,
                isUp = true,
                isSelected = sighting.userVote == "upvote",
                onClick = onUpvote
            )
            VoteButton(
                count = sighting.downvotes,
                isUp = false,
                isSelected = sighting.userVote == "downvote",
                onClick = onDownvote
            )
        }
    }
}

@Composable
private fun VoteButton(
    count: Int,
    isUp: Boolean,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val color = when {
        isSelected && isUp -> Green500
        isSelected && !isUp -> Red500
        else -> TextMuted
    }

    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(if (isSelected) color.copy(alpha = 0.15f) else Color.Transparent)
            .clickable(onClick = onClick)
            .padding(horizontal = 6.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        Icon(
            imageVector = if (isUp) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(14.dp)
        )
        Text(
            text = count.toString(),
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = color,
            fontFamily = FontFamily.Monospace
        )
    }
}

// ============================================
// LOT SELECTOR - CHIPS
// ============================================

@Composable
fun LotChip(
    code: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(4.dp))
            .background(if (isSelected) Amber500 else Black700)
            .border(1.dp, if (isSelected) Amber500 else Border, RoundedCornerShape(4.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(
            text = code,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
            color = if (isSelected) Black900 else TextGray
        )
    }
}

// ============================================
// EMPTY STATE
// ============================================

@Composable
fun EmptyState(
    icon: ImageVector,
    title: String,
    subtitle: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = TextMuted,
            modifier = Modifier.size(32.dp)
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = title.uppercase(),
            style = MaterialTheme.typography.labelLarge,
            color = TextGray,
            letterSpacing = 1.sp
        )
        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodySmall,
            color = TextMuted,
            textAlign = TextAlign.Center
        )
    }
}

// ============================================
// NOTIFICATION BADGE
// ============================================

@Composable
fun NotificationBadge(
    count: Int,
    modifier: Modifier = Modifier
) {
    if (count > 0) {
        Box(
            modifier = modifier
                .size(16.dp)
                .background(Red500, CircleShape),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = if (count > 9) "+" else count.toString(),
                style = MaterialTheme.typography.labelSmall,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = TextWhite
            )
        }
    }
}

// ============================================
// SECTION HEADER
// ============================================

@Composable
fun SectionHeader(
    title: String,
    modifier: Modifier = Modifier,
    action: @Composable (() -> Unit)? = null
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title.uppercase(),
            style = MaterialTheme.typography.labelMedium,
            color = TextMuted,
            letterSpacing = 1.sp
        )
        action?.invoke()
    }
}
