package com.warnabrotha.app.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ThumbUp
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material.icons.outlined.ThumbDown
import androidx.compose.material.icons.outlined.ThumbUp
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.FeedResponse
import com.warnabrotha.app.data.model.FeedSighting
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.theme.*

@Composable
fun FeedTab(
    parkingLots: List<ParkingLot>,
    feedFilterLotId: Int?,
    feed: FeedResponse?,
    allFeedSightings: List<FeedSighting>,
    allFeedsTotalCount: Int,
    isLoading: Boolean,
    onFeedFilterSelected: (Int?) -> Unit,
    onUpvote: (Int) -> Unit,
    onDownvote: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    val displayedSightings = if (feedFilterLotId == null) {
        allFeedSightings
    } else {
        feed?.sightings ?: emptyList()
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Background)
    ) {
        // === Sticky header area ===
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Background)
                .padding(horizontal = 20.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // TapOut mini logo
            Text(
                text = buildAnnotatedString {
                    withStyle(SpanStyle(color = TextPrimaryAlt)) {
                        append("Tap")
                    }
                    withStyle(SpanStyle(color = Green500)) {
                        append("Out")
                    }
                },
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontFamily = DmSansFamily,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = (-0.5).sp
                )
            )

            Spacer(modifier = Modifier.height(4.dp))

            // "Recent Taps" heading
            Text(
                text = "Recent Taps",
                style = MaterialTheme.typography.displayMedium,
                color = TextPrimary
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Filter chips
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterChip(
                    label = "ALL LOTS",
                    isSelected = feedFilterLotId == null,
                    onClick = { onFeedFilterSelected(null) }
                )
                parkingLots.forEach { lot ->
                    FilterChip(
                        label = lot.code,
                        isSelected = lot.id == feedFilterLotId,
                        onClick = { onFeedFilterSelected(lot.id) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Subheader: "SHOWING REPORTS FROM LAST 3 HOURS" + LIVE
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "SHOWING REPORTS FROM LAST 3 HOURS",
                    style = MaterialTheme.typography.labelMedium.copy(
                        letterSpacing = 0.5.sp
                    ),
                    color = TextMuted
                )
                FeedLiveBadge()
            }

            Spacer(modifier = Modifier.height(12.dp))
        }

        // === Feed list ===
        if (isLoading && displayedSightings.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(32.dp),
                        color = Green500,
                        strokeWidth = 3.dp
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "Loading reports...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextMuted
                    )
                }
            }
        } else if (displayedSightings.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Outlined.Notifications,
                        contentDescription = null,
                        tint = TextMuted,
                        modifier = Modifier.size(32.dp)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "ALL CLEAR",
                        style = MaterialTheme.typography.labelLarge,
                        color = TextSecondary,
                        letterSpacing = 1.sp
                    )
                    Text(
                        text = "No TAPS sightings in the last 3 hours",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextMuted,
                        textAlign = TextAlign.Center
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(horizontal = 20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(
                    items = displayedSightings,
                    key = { it.id }
                ) { sighting ->
                    // Fade older items
                    val itemAlpha = when {
                        sighting.minutesAgo < 30 -> 1f
                        sighting.minutesAgo < 90 -> 0.8f
                        else -> 0.6f
                    }

                    FeedCard(
                        sighting = sighting,
                        onUpvote = { onUpvote(sighting.id) },
                        onDownvote = { onDownvote(sighting.id) },
                        modifier = Modifier.alpha(itemAlpha)
                    )
                }

                // End-of-list indicator
                item {
                    EndOfWindowIndicator()
                }
            }
        }
    }
}

// ─── Filter Chip (pill-shaped) ───

@Composable
private fun FilterChip(
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(50))
            .then(
                if (isSelected) {
                    Modifier.background(Green500)
                } else {
                    Modifier
                        .background(Surface)
                        .border(1.dp, Border, RoundedCornerShape(50))
                }
            )
            .clickable(onClick = onClick)
            .padding(horizontal = 20.dp, vertical = 10.dp)
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.titleSmall.copy(
                fontFamily = DmSansFamily,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp
            ),
            color = if (isSelected) TextOnPrimary else TextSecondary
        )
    }
}

// ─── Feed Card (white card with green left accent) ───

@Composable
private fun FeedCard(
    sighting: FeedSighting,
    onUpvote: () -> Unit,
    onDownvote: () -> Unit,
    modifier: Modifier = Modifier
) {
    val timeText = when {
        sighting.minutesAgo < 1 -> "JUST NOW"
        sighting.minutesAgo < 60 -> "${sighting.minutesAgo} MINS AGO"
        sighting.minutesAgo < 120 -> "1 HOUR AGO"
        else -> "${sighting.minutesAgo / 60} HOUR AGO"
    }

    val lotName = sighting.parkingLotName?.uppercase() ?: sighting.parkingLotCode?.uppercase() ?: "UNKNOWN"

    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(IntrinsicSize.Min)
            .shadow(1.dp, RoundedCornerShape(16.dp), ambientColor = ShadowLight, spotColor = ShadowLight)
            .clip(RoundedCornerShape(16.dp))
            .background(Surface),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Green left accent bar
        Box(
            modifier = Modifier
                .width(5.dp)
                .fillMaxHeight()
                .background(Green500)
        )

        // Content
        Row(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 16.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = timeText,
                    style = MaterialTheme.typography.labelMedium.copy(
                        letterSpacing = 0.5.sp
                    ),
                    color = Green500
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = lotName,
                    style = MaterialTheme.typography.headlineMedium,
                    color = TextPrimary
                )
            }

            // Vote buttons
            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                FeedVoteButton(
                    count = sighting.upvotes,
                    isUp = true,
                    isSelected = sighting.userVote == "upvote",
                    onClick = onUpvote
                )
                FeedVoteButton(
                    count = sighting.downvotes,
                    isUp = false,
                    isSelected = sighting.userVote == "downvote",
                    onClick = onDownvote
                )
            }
        }
    }
}

// ─── Vote Button (thumb icon + count) ───

@Composable
private fun FeedVoteButton(
    count: Int,
    isUp: Boolean,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val color = when {
        isSelected && isUp -> Green500
        isSelected && !isUp -> Red500
        isUp -> Green600
        else -> TextMuted
    }

    Row(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .clickable(onClick = onClick)
            .padding(4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Icon(
            imageVector = if (isUp) {
                if (isSelected) Icons.Filled.ThumbUp else Icons.Outlined.ThumbUp
            } else {
                Icons.Outlined.ThumbDown
            },
            contentDescription = if (isUp) "Upvote" else "Downvote",
            tint = color,
            modifier = Modifier.size(18.dp)
        )
        Text(
            text = count.toString(),
            style = MaterialTheme.typography.titleMedium,
            color = color
        )
    }
}

// ─── LIVE badge (reused from ReportTab pattern) ───

@Composable
private fun FeedLiveBadge() {
    val infiniteTransition = rememberInfiniteTransition(label = "feedLive")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800),
            repeatMode = RepeatMode.Reverse
        ),
        label = "feedLiveAlpha"
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

// ─── End of 3-hour window indicator ───

@Composable
private fun EndOfWindowIndicator() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Three dots
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            repeat(3) {
                Box(
                    modifier = Modifier
                        .size(6.dp)
                        .background(TextMuted.copy(alpha = 0.4f), CircleShape)
                )
            }
        }
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "END OF 3-HOUR WINDOW",
            style = MaterialTheme.typography.labelMedium.copy(
                letterSpacing = 1.sp
            ),
            color = TextMuted.copy(alpha = 0.6f)
        )
    }
}
