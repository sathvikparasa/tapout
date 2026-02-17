package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.ui.screens.WelcomeScreen
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class WelcomeScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun welcomeScreenDisplays() {
        composeTestRule.setContent {
            MaterialTheme {
                WelcomeScreen(isLoading = false, onGetStarted = { })
            }
        }

        composeTestRule.onNodeWithText("GET STARTED").assertIsDisplayed()
        composeTestRule.onNodeWithText("Real-time alerts").assertIsDisplayed()
        composeTestRule.onNodeWithText("Community-powered").assertIsDisplayed()
        composeTestRule.onNodeWithText("Tap out of parking").assertIsDisplayed()
    }

    @Test
    fun getStartedCallsCallback() {
        var called = false
        composeTestRule.setContent {
            MaterialTheme {
                WelcomeScreen(isLoading = false, onGetStarted = { called = true })
            }
        }

        composeTestRule.onNodeWithText("GET STARTED").performClick()

        assertTrue(called)
    }
}
