package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.data.model.FeedSighting
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.screens.FeedTab
import org.junit.Rule
import org.junit.Test

class FeedTabTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true)
    )

    @Test
    fun emptyStateShown() {
        composeTestRule.setContent {
            MaterialTheme {
                FeedTab(
                    parkingLots = testLots,
                    feedFilterLotId = null,
                    feed = null,
                    allFeedSightings = emptyList(),
                    allFeedsTotalCount = 0,
                    isLoading = false,
                    onFeedFilterSelected = { },
                    onUpvote = { },
                    onDownvote = { }
                )
            }
        }

        composeTestRule.onNodeWithText("ALL CLEAR").assertIsDisplayed()
        composeTestRule.onNodeWithText("No TAPS sightings in the last 3 hours").assertIsDisplayed()
    }

    @Test
    fun sightingCardsDisplayed() {
        val sightings = listOf(
            FeedSighting(
                id = 1, parkingLotId = 1, parkingLotName = "Lot A",
                parkingLotCode = "LOT_A", reportedAt = "2025-01-15T11:00:00Z",
                notes = null, upvotes = 3, downvotes = 1, netScore = 2,
                userVote = null, minutesAgo = 10
            )
        )

        composeTestRule.setContent {
            MaterialTheme {
                FeedTab(
                    parkingLots = testLots,
                    feedFilterLotId = null,
                    feed = null,
                    allFeedSightings = sightings,
                    allFeedsTotalCount = 1,
                    isLoading = false,
                    onFeedFilterSelected = { },
                    onUpvote = { },
                    onDownvote = { }
                )
            }
        }

        // Sighting card shows lot name and time
        composeTestRule.onNodeWithText("LOT A").assertIsDisplayed()
        composeTestRule.onNodeWithText("10 MINS AGO").assertIsDisplayed()
        // Vote counts displayed
        composeTestRule.onNodeWithText("3").assertIsDisplayed()
        composeTestRule.onNodeWithText("1").assertIsDisplayed()
    }
}
