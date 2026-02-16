package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.data.model.FeedSighting
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.screens.FeedTab
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class FeedTabAdvancedTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true),
        ParkingLot(2, "Lot B", "LOT_B", 38.55, -121.75, true)
    )

    private fun makeSighting(
        id: Int, lotId: Int, lotName: String, lotCode: String, minutesAgo: Int,
        upvotes: Int = 0, downvotes: Int = 0, userVote: String? = null
    ) = FeedSighting(
        id = id, parkingLotId = lotId, parkingLotName = lotName,
        parkingLotCode = lotCode, reportedAt = "2025-01-15T11:00:00Z",
        notes = null, upvotes = upvotes, downvotes = downvotes,
        netScore = upvotes - downvotes, userVote = userVote, minutesAgo = minutesAgo
    )

    @Test
    fun votingFlow_callbackFired() {
        var upvotedId = -1

        val sighting = makeSighting(
            id = 10, lotId = 1, lotName = "Lot A", lotCode = "LOT_A",
            minutesAgo = 5, upvotes = 2, downvotes = 1
        )

        composeTestRule.setContent {
            MaterialTheme {
                FeedTab(
                    parkingLots = testLots,
                    feedFilterLotId = null,
                    feed = null,
                    allFeedSightings = listOf(sighting),
                    allFeedsTotalCount = 1,
                    isLoading = false,
                    onFeedFilterSelected = { },
                    onUpvote = { upvotedId = it },
                    onDownvote = { }
                )
            }
        }

        // Click the upvote button (shows "Upvote" content description)
        composeTestRule.onNodeWithContentDescription("Upvote").performClick()
        assertEquals(10, upvotedId)
    }

    @Test
    fun filterChips_callbackWithCorrectId() {
        var selectedFilterId: Int? = -1

        composeTestRule.setContent {
            MaterialTheme {
                FeedTab(
                    parkingLots = testLots,
                    feedFilterLotId = null,
                    feed = null,
                    allFeedSightings = emptyList(),
                    allFeedsTotalCount = 0,
                    isLoading = false,
                    onFeedFilterSelected = { selectedFilterId = it },
                    onUpvote = { },
                    onDownvote = { }
                )
            }
        }

        // Click the LOT_B chip (lot code is displayed as chip label)
        composeTestRule.onNodeWithText("LOT_B").performClick()
        assertEquals(2, selectedFilterId)
    }

    @Test
    fun multipleSightings_allDisplayed() {
        val sightings = listOf(
            makeSighting(1, 1, "Lot A", "LOT_A", 5),
            makeSighting(2, 2, "Lot B", "LOT_B", 15),
            makeSighting(3, 1, "Lot C", "LOT_C", 30)
        )

        composeTestRule.setContent {
            MaterialTheme {
                FeedTab(
                    parkingLots = testLots,
                    feedFilterLotId = null,
                    feed = null,
                    allFeedSightings = sightings,
                    allFeedsTotalCount = 3,
                    isLoading = false,
                    onFeedFilterSelected = { },
                    onUpvote = { },
                    onDownvote = { }
                )
            }
        }

        // All 3 lot names should be visible (displayed as uppercase)
        composeTestRule.onNodeWithText("LOT A").assertIsDisplayed()
        composeTestRule.onNodeWithText("LOT B").assertIsDisplayed()
        composeTestRule.onNodeWithText("LOT C").assertIsDisplayed()
    }
}
