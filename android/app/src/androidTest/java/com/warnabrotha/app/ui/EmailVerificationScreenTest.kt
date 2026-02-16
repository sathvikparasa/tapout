package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.ui.screens.EmailVerificationScreen
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class EmailVerificationScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun emailInputDisplayed() {
        composeTestRule.setContent {
            MaterialTheme {
                EmailVerificationScreen(
                    isLoading = false,
                    error = null,
                    onVerify = { }
                )
            }
        }

        composeTestRule.onNodeWithText("Verify Your Student Email").assertIsDisplayed()
        composeTestRule.onNodeWithText("yourname@ucdavis.edu").assertIsDisplayed()
        composeTestRule.onNodeWithText("UNIVERSITY EMAIL").assertIsDisplayed()
    }

    @Test
    fun submitWithValidEmail() {
        var verifiedEmail = ""
        composeTestRule.setContent {
            MaterialTheme {
                EmailVerificationScreen(
                    isLoading = false,
                    error = null,
                    onVerify = { verifiedEmail = it }
                )
            }
        }

        // Type a valid UCD email
        composeTestRule.onNodeWithText("yourname@ucdavis.edu").performTextInput("testuser@ucdavis.edu")

        // SUBMIT should now be clickable
        composeTestRule.onNodeWithText("SUBMIT").performClick()

        assertEquals("testuser@ucdavis.edu", verifiedEmail)
    }

    @Test
    fun submitDisabledForInvalidEmail() {
        var called = false
        composeTestRule.setContent {
            MaterialTheme {
                EmailVerificationScreen(
                    isLoading = false,
                    error = null,
                    onVerify = { called = true }
                )
            }
        }

        // Type an invalid email
        composeTestRule.onNodeWithText("yourname@ucdavis.edu").performTextInput("user@gmail.com")

        // SUBMIT button should be disabled — click should not trigger callback
        composeTestRule.onNodeWithText("SUBMIT").assertIsDisplayed()
        composeTestRule.onNodeWithText("SUBMIT").performClick()

        assertTrue(!called)
    }
}
