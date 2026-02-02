package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.FeedResponse
import com.warnabrotha.app.data.model.FeedSighting
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.components.EmptyState
import com.warnabrotha.app.ui.components.LotChip
import com.warnabrotha.app.ui.theme.*

@Composable
fun FeedTab(
    parkingLots: List<ParkingLot>,
    selectedLotId: Int?,
    feed: FeedResponse?,
    isLoading: Boolean,
    onLotSelected: (Int) -> Unit,
    onUpvote: (Int) -> Unit,
    onDownvote: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Black900)
            .padding(20.dp)
    ) {
        // Header
        Text(
            text = "LIVE FEED",
            style = MaterialTheme.typography.labelSmall,
            color = TextMuted,
            letterSpacing = 1.sp
        )
        Spacer(modifier = Modifier.height(4.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Recent Sightings",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = TextWhite
            )
            Text(
                text = "${feed?.totalSightings ?: 0} reports",
                style = MaterialTheme.typography.labelMedium,
                color = if ((feed?.totalSightings ?: 0) > 0) Amber500 else TextMuted
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Lot selector
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            parkingLots.forEach { lot ->
                LotChip(
                    code = lot.code,
                    isSelected = lot.id == selectedLotId,
                    onClick = { onLotSelected(lot.id) }
                )
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Feed list
        if (isLoading && feed == null) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(40.dp),
                        color = Amber500,
                        strokeWidth = 3.dp
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Loading reports...",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextMuted
                    )
                }
            }
        } else if (feed == null || feed.sightings.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                EmptyState(
                    icon = Icons.Outlined.Notifications,
                    title = "All Clear",
                    subtitle = "No TAPS sightings in the last 3 hours"
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                items(
                    items = feed.sightings,
                    key = { it.id }
                ) { sighting ->
                    FeedItem(
                        sighting = sighting,
                        onUpvote = { onUpvote(sighting.id) },
                        onDownvote = { onDownvote(sighting.id) }
                    )
                }
            }
        }
    }
}

@Composable
private fun FeedItem(
    sighting: FeedSighting,
    onUpvote: () -> Unit,
    onDownvote: () -> Unit
) {
    val timeColor = when {
        sighting.minutesAgo < 30 -> Red500
        sighting.minutesAgo < 90 -> Amber500
        else -> TextMuted
    }

    val timeText = when {
        sighting.minutesAgo < 1 -> "Just now"
        sighting.minutesAgo < 60 -> "${sighting.minutesAgo} min ago"
        else -> "${sighting.minutesAgo / 60}h ${sighting.minutesAgo % 60}m ago"
    }

    Column(
        modifier = Modifier.fillMaxWidth()
    ) {
        // Top row: time and lot
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Time indicator dot
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .clip(CircleShape)
                        .background(timeColor)
                )
                Text(
                    text = timeText,
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = timeColor
                )
            }

            // Lot code
            Text(
                text = sighting.parkingLotCode ?: "Unknown",
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold,
                color = Amber500
            )
        }

        // Notes (if any)
        if (!sighting.notes.isNullOrBlank()) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = sighting.notes,
                style = MaterialTheme.typography.bodyMedium,
                color = TextGray,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Bottom row: votes
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Vote buttons
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                VoteAction(
                    count = sighting.upvotes,
                    isUp = true,
                    isSelected = sighting.userVote == "upvote",
                    onClick = onUpvote
                )
                VoteAction(
                    count = sighting.downvotes,
                    isUp = false,
                    isSelected = sighting.userVote == "downvote",
                    onClick = onDownvote
                )
            }

            // Net score
            val scoreColor = when {
                sighting.netScore > 0 -> Green500
                sighting.netScore < 0 -> Red500
                else -> TextMuted
            }
            Text(
                text = if (sighting.netScore > 0) "+${sighting.netScore}" else "${sighting.netScore}",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = scoreColor,
                fontFamily = FontFamily.Monospace
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Divider
        HorizontalDivider(color = Border, thickness = 1.dp)
    }
}

@Composable
private fun VoteAction(
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

    TextButton(
        onClick = onClick,
        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Icon(
            imageVector = if (isUp) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
            contentDescription = if (isUp) "Upvote" else "Downvote",
            tint = color,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(4.dp))
        Text(
            text = count.toString(),
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.SemiBold,
            color = color
        )
    }
}
