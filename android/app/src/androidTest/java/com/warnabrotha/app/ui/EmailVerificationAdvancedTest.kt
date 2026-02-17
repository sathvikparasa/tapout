package com.warnabrotha.app.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import com.warnabrotha.app.ui.screens.EmailVerificationScreen
import com.warnabrotha.app.ui.viewmodel.OTPStep
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

        composeTestRule.onNodeWithText("Invalid email domain").assertIsDisplayed()
    }
}
