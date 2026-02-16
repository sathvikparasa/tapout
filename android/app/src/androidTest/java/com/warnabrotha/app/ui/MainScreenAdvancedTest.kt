package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.ui.screens.MainScreen
import com.warnabrotha.app.ui.viewmodel.AppUiState
import org.junit.Rule
import org.junit.Test

class MainScreenAdvancedTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true),
        ParkingLot(2, "Lot B", "LOT_B", 38.55, -121.75, true)
    )

    private val noopInt: (Int) -> Unit = {}
    private val noopIntNullable: (Int?) -> Unit = {}
    private val noop: () -> Unit = {}

    private fun renderMainScreen(uiState: AppUiState) {
        composeTestRule.setContent {
            MaterialTheme {
                MainScreen(
                    uiState = uiState,
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
    }

    @Test
    fun errorSnackbar_displayed() {
        val stateWithError = AppUiState(
            isAuthenticated = true,
            isEmailVerified = true,
            parkingLots = testLots,
            error = "Check-in failed"
        )
        renderMainScreen(stateWithError)

        composeTestRule.onNodeWithText("Check-in failed").assertIsDisplayed()
    }

    @Test
    fun successSnackbar_displayed() {
        val stateWithSuccess = AppUiState(
            isAuthenticated = true,
            isEmailVerified = true,
            parkingLots = testLots,
            successMessage = "Checked in!"
        )
        renderMainScreen(stateWithSuccess)

        composeTestRule.onNodeWithText("Checked in!").assertIsDisplayed()
    }

    @Test
    fun tabNavigation_homeToFeedAndBack() {
        val defaultState = AppUiState(
            isAuthenticated = true,
            isEmailVerified = true,
            parkingLots = testLots
        )
        renderMainScreen(defaultState)

        // Home tab is active by default
        composeTestRule.onNodeWithText("SELECT PARKING ZONE").assertIsDisplayed()

        // Navigate to Feed
        composeTestRule.onNodeWithText("Feed").performClick()
        composeTestRule.onNodeWithText("Recent Taps").assertIsDisplayed()

        // Navigate back to Home
        composeTestRule.onNodeWithText("Home").performClick()
        composeTestRule.onNodeWithText("SELECT PARKING ZONE").assertIsDisplayed()
    }
}
