package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.data.model.ParkingLot
import com.warnabrotha.app.data.model.ParkingLotWithStats
import com.warnabrotha.app.data.model.ParkingSession
import com.warnabrotha.app.ui.screens.ReportTab
import org.junit.Rule
import org.junit.Test

class ReportTabTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    private val testLots = listOf(
        ParkingLot(1, "Lot A", "LOT_A", 38.54, -121.74, true)
    )

    private val testLotWithStats = ParkingLotWithStats(
        id = 1, name = "Lot A", code = "LOT_A",
        latitude = 38.54, longitude = -121.74, isActive = true,
        activeParkers = 5, recentSightings = 2, tapsProbability = 0.7
    )

    @Test
    fun checkInButtonDisplayed() {
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

        // Not parked → CHECK IN button shown
        composeTestRule.onNodeWithText("CHECK IN").assertIsDisplayed()
        composeTestRule.onNodeWithText("REPORT TAPS").assertIsDisplayed()
    }

    @Test
    fun checkOutButtonWhenParked() {
        val session = ParkingSession(
            id = 1, parkingLotId = 1, parkingLotName = "Lot A",
            parkingLotCode = "LOT_A", checkedInAt = "2025-01-15T10:00:00Z",
            checkedOutAt = null, isActive = true, reminderSent = false
        )

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
                    onCheckIn = { },
                    onCheckOut = { },
                    onRefresh = { },
                    onLotSelected = { }
                )
            }
        }

        // Parked → CHECK OUT button shown instead of CHECK IN
        composeTestRule.onNodeWithText("CHECK OUT").assertIsDisplayed()
        composeTestRule.onNodeWithText("REPORT TAPS").assertIsDisplayed()
    }
}
