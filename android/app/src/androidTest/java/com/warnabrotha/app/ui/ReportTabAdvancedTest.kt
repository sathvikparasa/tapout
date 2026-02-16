package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.ui.screens.ReportTab
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class ReportTabAdvancedTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true),
        ParkingLot(2, "Lot B", "LOT_B", 38.55, -121.75, true)
    )

    private val testLotWithStats = ParkingLotWithStats(
        id = 1, name = "Lot A", code = "LOT_A",
        latitude = 38.54, longitude = -121.74, isActive = true,
        activeParkers = 5, recentSightings = 2, tapsProbability = 0.7
    )

    private val testSession = ParkingSession(
        id = 1, parkingLotId = 1, parkingLotName = "Lot A",
        parkingLotCode = "LOT_A", checkedInAt = "2025-01-15T10:00:00Z",
        checkedOutAt = null, isActive = true, reminderSent = false
    )

    @Test
    fun checkInOutFlow_buttonChanges() {
        var session by mutableStateOf<ParkingSession?>(null)

        composeTestRule.setContent {
            MaterialTheme {
                ReportTab(
                    selectedLot = testLotWithStats,
                    parkingLots = testLots,
                    currentSession = session,
                    prediction = null,
                    totalParkedGlobal = 25,
                    totalRegisteredDevices = 100,
                    isLoading = false,
                    onReportTaps = { },
                    onCheckIn = { session = testSession },
                    onCheckOut = { session = null },
                    onRefresh = { },
                    onLotSelected = { }
                )
            }
        }

        // Initially CHECK IN
        composeTestRule.onNodeWithText("CHECK IN").assertIsDisplayed()

        // Click CHECK IN → triggers onCheckIn → session set → button becomes CHECK OUT
        composeTestRule.onNodeWithText("CHECK IN").performClick()
        composeTestRule.waitForIdle()
        composeTestRule.onNodeWithText("CHECK OUT").assertIsDisplayed()

        // Click CHECK OUT → triggers onCheckOut → session null → button becomes CHECK IN
        composeTestRule.onNodeWithText("CHECK OUT").performClick()
        composeTestRule.waitForIdle()
        composeTestRule.onNodeWithText("CHECK IN").assertIsDisplayed()
    }

    @Test
    fun reportTaps_callbackFired() {
        var reportCalled = false

        composeTestRule.setContent {
            MaterialTheme {
                ReportTab(
                    selectedLot = testLotWithStats,
                    parkingLots = testLots,
                    currentSession = null,
                    prediction = null,
                    totalParkedGlobal = 25,
                    totalRegisteredDevices = 100,
                    isLoading = false,
                    onReportTaps = { reportCalled = true },
                    onCheckIn = { },
                    onCheckOut = { },
                    onRefresh = { },
                    onLotSelected = { }
                )
            }
        }

        composeTestRule.onNodeWithText("REPORT TAPS").performClick()
        assertTrue(reportCalled)
    }

    @Test
    fun lotSelector_showsCurrentLot() {
        composeTestRule.setContent {
            MaterialTheme {
                ReportTab(
                    selectedLot = testLotWithStats,
                    parkingLots = testLots,
                    currentSession = null,
                    prediction = null,
                    totalParkedGlobal = 25,
                    totalRegisteredDevices = 100,
                    isLoading = false,
                    onReportTaps = { },
                    onCheckIn = { },
                    onCheckOut = { },
                    onRefresh = { },
                    onLotSelected = { }
                )
            }
        }

        // The selector row shows the lot name with code
        composeTestRule.onNodeWithText("Lot A (LOT_A)").assertIsDisplayed()
    }

    @Test
    fun loadingState_disablesButtons() {
        var checkInCalled = false

        composeTestRule.setContent {
            MaterialTheme {
                ReportTab(
                    selectedLot = testLotWithStats,
                    parkingLots = testLots,
                    currentSession = null,
                    prediction = null,
                    totalParkedGlobal = 25,
                    totalRegisteredDevices = 100,
                    isLoading = true,
                    onReportTaps = { },
                    onCheckIn = { checkInCalled = true },
                    onCheckOut = { },
                    onRefresh = { },
                    onLotSelected = { }
                )
            }
        }

        // Buttons should still exist with their text
        composeTestRule.onNodeWithText("CHECK IN").assertExists()
        composeTestRule.onNodeWithText("REPORT TAPS").assertExists()

        // When loading, the DashboardActionButton removes clickable modifier
        // so the click should not fire the callback
        composeTestRule.onNodeWithText("CHECK IN").performClick()
        assertTrue(!checkInCalled)
    }
}
