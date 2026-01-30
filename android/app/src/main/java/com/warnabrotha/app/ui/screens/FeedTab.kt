package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.data.model.FeedResponse
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.components.BeveledBorder
import com.warnabrotha.app.ui.components.Win95FeedItem
import com.warnabrotha.app.ui.components.Win95LotSelector
import com.warnabrotha.app.ui.theme.Win95Colors

@Composable
fun FeedTab(
    parkingLots: List<ParkingLot>,
    selectedLotId: Int?,
    feed: FeedResponse?,
    onLotSelected: (Int) -> Unit,
    onUpvote: (Int) -> Unit,
    onDownvote: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Win95Colors.WindowBackground)
    ) {
        // Lot selector
        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Select Parking Lot",
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = Win95Colors.TextSecondary,
            modifier = Modifier.padding(horizontal = 16.dp)
        )

        Spacer(modifier = Modifier.height(4.dp))

        Win95LotSelector(
            lots = parkingLots,
            selectedLotId = selectedLotId,
            onLotSelected = onLotSelected
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Recent reports header
        Text(
            text = "Recent Reports (Last 3 Hours)",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = Win95Colors.TitleBar,
            modifier = Modifier.padding(horizontal = 16.dp)
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Feed items
        if (feed == null || feed.sightings.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                BeveledBorder(
                    modifier = Modifier
                        .padding(16.dp)
                        .fillMaxWidth(),
                    raised = false
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(Win95Colors.WindowBackground)
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                text = "📭",
                                fontSize = 48.sp
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "No recent reports",
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = Win95Colors.TextPrimary
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Be the first to report a TAPS sighting!",
                                fontSize = 12.sp,
                                color = Win95Colors.TextSecondary,
                                textAlign = TextAlign.Center
                            )
                        }
                    }
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.weight(1f),
                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(feed.sightings) { sighting ->
                    Win95FeedItem(
                        sighting = sighting,
                        onUpvote = { onUpvote(sighting.id) },
                        onDownvote = { onDownvote(sighting.id) }
                    )
                }
            }
        }
    }
}
