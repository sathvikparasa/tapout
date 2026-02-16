package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.data.model.*
import com.warnabrotha.app.ui.screens.MainScreen
import com.warnabrotha.app.ui.viewmodel.AppUiState
import org.junit.Rule
import org.junit.Test

class MainScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true),
        ParkingLot(2, "Lot B", "LOT_B", 38.55, -121.75, true)
    )

    private val defaultState = AppUiState(
        isAuthenticated = true,
        isEmailVerified = true,
        parkingLots = testLots
    )

    private val noopInt: (Int) -> Unit = {}
    private val noopIntNullable: (Int?) -> Unit = {}
    private val noop: () -> Unit = {}

    @Test
    fun bottomNavTabsDisplayed() {
        composeTestRule.setContent {
            MaterialTheme {
                MainScreen(
                    uiState = defaultState,
                    onReportTaps = noop,
                    onReportTapsAtLot = noopInt,
                    onCheckIn = noop,
                    onCheckInAtLot = noopInt,
                    onCheckOut = noop,
                    onRefresh = noop,
                    onLotSelected = noopInt,
                    onFeedFilterSelected = noopIntNullable,
                    onUpvote = noopInt,
                    onDownvote = noopInt,
                    onClearError = noop,
                    onClearSuccess = noop
                )
            }
        }

        composeTestRule.onNodeWithText("Home").assertIsDisplayed()
        composeTestRule.onNodeWithText("Feed").assertIsDisplayed()
        composeTestRule.onNodeWithText("Map").assertIsDisplayed()
    }

    @Test
    fun tabNavigationSwitchesContent() {
        composeTestRule.setContent {
            MaterialTheme {
                MainScreen(
                    uiState = defaultState,
                    onReportTaps = noop,
                    onReportTapsAtLot = noopInt,
                    onCheckIn = noop,
                    onCheckInAtLot = noopInt,
                    onCheckOut = noop,
                    onRefresh = noop,
                    onLotSelected = noopInt,
                    onFeedFilterSelected = noopIntNullable,
                    onUpvote = noopInt,
                    onDownvote = noopInt,
                    onClearError = noop,
                    onClearSuccess = noop
                )
            }
        }

        // Default is Home tab — should show ReportTab content
        composeTestRule.onNodeWithText("SELECT PARKING ZONE").assertIsDisplayed()

        // Switch to Feed tab
        composeTestRule.onNodeWithText("Feed").performClick()

        // Feed tab shows "Recent Taps" heading and "ALL LOTS" filter chip
        composeTestRule.onNodeWithText("Recent Taps").assertIsDisplayed()
        composeTestRule.onNodeWithText("ALL LOTS").assertIsDisplayed()
    }
}
