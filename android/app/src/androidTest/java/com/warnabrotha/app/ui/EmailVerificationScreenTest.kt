package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.ui.screens.EmailVerificationScreen
import com.warnabrotha.app.ui.viewmodel.OTPStep
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
                    otpStep = OTPStep.EMAIL_INPUT,
                    otpEmail = "",
                    canResendOTP = false,
                    resendCooldownSeconds = 0,
                    onSendOTP = { },
                    onVerifyOTP = { },
                    onResendOTP = { },
                    onChangeEmail = { }
                )
            }
        }

        composeTestRule.onNodeWithText("Verify Your Student Email").assertIsDisplayed()
        composeTestRule.onNodeWithText("yourname@ucdavis.edu").assertIsDisplayed()
        composeTestRule.onNodeWithText("UNIVERSITY EMAIL").assertIsDisplayed()
    }

    @Test
    fun submitWithValidEmail() {
        var sentEmail = ""
        composeTestRule.setContent {
            MaterialTheme {
                EmailVerificationScreen(
                    isLoading = false,
                    error = null,
                    otpStep = OTPStep.EMAIL_INPUT,
                    otpEmail = "",
                    canResendOTP = false,
                    resendCooldownSeconds = 0,
                    onSendOTP = { sentEmail = it },
                    onVerifyOTP = { },
                    onResendOTP = { },
                    onChangeEmail = { }
                )
            }
        }

        // Type a valid UCD email
        composeTestRule.onNodeWithText("yourname@ucdavis.edu").performTextInput("testuser@ucdavis.edu")

        // SEND CODE should now be clickable
        composeTestRule.onNodeWithText("SEND CODE").performClick()

        assertEquals("testuser@ucdavis.edu", sentEmail)
    }

    @Test
    fun submitDisabledForInvalidEmail() {
        var called = false
        composeTestRule.setContent {
            MaterialTheme {
                EmailVerificationScreen(
                    isLoading = false,
                    error = null,
                    otpStep = OTPStep.EMAIL_INPUT,
                    otpEmail = "",
                    canResendOTP = false,
                    resendCooldownSeconds = 0,
                    onSendOTP = { called = true },
                    onVerifyOTP = { },
                    onResendOTP = { },
                    onChangeEmail = { }
                )
            }
        }

        // Type an invalid email
        composeTestRule.onNodeWithText("yourname@ucdavis.edu").performTextInput("user@gmail.com")

        // SEND CODE button should be disabled -- click should not trigger callback
        composeTestRule.onNodeWithText("SEND CODE").assertIsDisplayed()
        composeTestRule.onNodeWithText("SEND CODE").performClick()

        assertTrue(!called)
    }
}
