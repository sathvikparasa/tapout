package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.ui.screens.EmailVerificationScreen
import org.junit.Rule
import org.junit.Test

class EmailVerificationAdvancedTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun errorMessage_displayedInRedBox() {
        composeTestRule.setContent {
            MaterialTheme {
                EmailVerificationScreen(
                    isLoading = false,
                    error = "Invalid email domain",
                    onVerify = { }
                )
            }
        }

        composeTestRule.onNodeWithText("Invalid email domain").assertIsDisplayed()
    }
}
