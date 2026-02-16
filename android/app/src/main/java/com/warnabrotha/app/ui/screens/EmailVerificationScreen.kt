package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.theme.*
import com.warnabrotha.app.ui.viewmodel.OTPStep

@Composable
fun EmailVerificationScreen(
    isLoading: Boolean,
    error: String?,
    otpStep: OTPStep,
    otpEmail: String,
    canResendOTP: Boolean,
    resendCooldownSeconds: Int,
    onSendOTP: (String) -> Unit,
    onVerifyOTP: (String) -> Unit,
    onResendOTP: () -> Unit,
    onChangeEmail: () -> Unit,
    modifier: Modifier = Modifier
) {
    when (otpStep) {
        OTPStep.EMAIL_INPUT -> EmailInputStep(
            isLoading = isLoading,
            error = error,
            onSendOTP = onSendOTP,
            modifier = modifier
        )
        OTPStep.CODE_INPUT -> OTPCodeInputStep(
            isLoading = isLoading,
            error = error,
            otpEmail = otpEmail,
            canResendOTP = canResendOTP,
            resendCooldownSeconds = resendCooldownSeconds,
            onVerifyOTP = onVerifyOTP,
            onResendOTP = onResendOTP,
            onChangeEmail = onChangeEmail,
            modifier = modifier
        )
    }
}

@Composable
private fun EmailInputStep(
    isLoading: Boolean,
    error: String?,
    onSendOTP: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var email by remember { mutableStateOf("") }
    val isValidEmail = email.endsWith("@ucdavis.edu") && email.length > 12

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Background)
    ) {
        // Back button
        IconButton(
            onClick = { /* navigation back if needed */ },
            modifier = Modifier.padding(start = 16.dp, top = 8.dp)
        ) {
            Icon(
                imageVector = Icons.Default.ArrowBackIosNew,
                contentDescription = "Back",
                tint = Green500,
                modifier = Modifier.size(24.dp)
            )
        }

        // Main content
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(8.dp))

            // Parking icon in green container
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .shadow(
                        elevation = 10.dp,
                        shape = RoundedCornerShape(16.dp),
                        ambientColor = GreenShadow,
                        spotColor = GreenShadow
                    )
                    .background(Green500, RoundedCornerShape(16.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.LocalParking,
                    contentDescription = null,
                    tint = TextOnPrimary,
                    modifier = Modifier.size(30.dp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Heading
            Text(
                text = "Verify Your Student Email",
                style = MaterialTheme.typography.headlineLarge,
                color = TextPrimary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Description
            Text(
                text = "Enter your UC Davis email to receive\na verification code.",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
                textAlign = TextAlign.Center,
                lineHeight = 16.sp
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Email input section
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                // Label
                Text(
                    text = "UNIVERSITY EMAIL",
                    style = MaterialTheme.typography.labelMedium,
                    color = Green500
                )

                // Input field
                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    placeholder = {
                        Text(
                            "yourname@ucdavis.edu",
                            color = TextMuted
                        )
                    },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Email,
                        imeAction = ImeAction.Done
                    ),
                    keyboardActions = KeyboardActions(
                        onDone = {
                            if (isValidEmail && !isLoading) {
                                onSendOTP(email)
                            }
                        }
                    ),
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Outlined.Email,
                            contentDescription = null,
                            tint = if (email.isNotEmpty() && isValidEmail) Green500 else TextMuted,
                            modifier = Modifier.size(20.dp)
                        )
                    },
                    trailingIcon = {
                        if (email.isNotEmpty()) {
                            Icon(
                                imageVector = if (isValidEmail) Icons.Default.CheckCircle else Icons.Default.Error,
                                contentDescription = null,
                                tint = if (isValidEmail) Green500 else Red500,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    },
                    isError = email.isNotEmpty() && !isValidEmail,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Green500,
                        unfocusedBorderColor = BorderLight,
                        errorBorderColor = Red500,
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        cursorColor = Green500,
                        focusedContainerColor = Surface,
                        unfocusedContainerColor = Surface
                    ),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                )

                // Hint text
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Info,
                        contentDescription = null,
                        tint = TextMuted,
                        modifier = Modifier.size(12.dp)
                    )
                    Text(
                        text = "Must use UC Davis email address",
                        style = MaterialTheme.typography.bodySmall.copy(
                            fontSize = 11.sp
                        ),
                        color = TextMuted
                    )
                }
            }

            // Server error
            if (error != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(RedOverlay10, RoundedCornerShape(12.dp))
                        .border(1.dp, Red500.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                        .padding(12.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.ErrorOutline,
                            contentDescription = null,
                            tint = Red500,
                            modifier = Modifier.size(18.dp)
                        )
                        Text(
                            text = error,
                            style = MaterialTheme.typography.bodySmall,
                            color = Red500
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Submit button
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(32.dp),
                    color = Green500,
                    strokeWidth = 3.dp
                )
            } else {
                Button(
                    onClick = { onSendOTP(email) },
                    enabled = isValidEmail,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .then(
                            if (isValidEmail) Modifier.shadow(
                                elevation = 10.dp,
                                shape = RoundedCornerShape(12.dp),
                                ambientColor = GreenShadow,
                                spotColor = GreenShadow
                            ) else Modifier
                        ),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Green500,
                        contentColor = TextOnPrimary,
                        disabledContainerColor = Green500.copy(alpha = 0.4f),
                        disabledContentColor = TextOnPrimary.copy(alpha = 0.6f)
                    )
                ) {
                    Text(
                        text = "SEND CODE",
                        style = MaterialTheme.typography.titleSmall.copy(
                            letterSpacing = 0.35.sp
                        ),
                        color = TextOnPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Icon(
                        imageVector = Icons.Default.ArrowForward,
                        contentDescription = null,
                        tint = TextOnPrimary,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Footer
            Text(
                text = buildAnnotatedString {
                    withStyle(SpanStyle(color = TextSecondary)) {
                        append("Having trouble? ")
                    }
                    withStyle(
                        SpanStyle(
                            color = Green500,
                            fontWeight = FontWeight.Bold
                        )
                    ) {
                        append("Contact Support")
                    }
                },
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
private fun OTPCodeInputStep(
    isLoading: Boolean,
    error: String?,
    otpEmail: String,
    canResendOTP: Boolean,
    resendCooldownSeconds: Int,
    onVerifyOTP: (String) -> Unit,
    onResendOTP: () -> Unit,
    onChangeEmail: () -> Unit,
    modifier: Modifier = Modifier
) {
    var otpCode by remember { mutableStateOf("") }
    val isValidCode = otpCode.length == 6

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Background)
    ) {
        // Back button → change email
        IconButton(
            onClick = onChangeEmail,
            modifier = Modifier.padding(start = 16.dp, top = 8.dp)
        ) {
            Icon(
                imageVector = Icons.Default.ArrowBackIosNew,
                contentDescription = "Back",
                tint = Green500,
                modifier = Modifier.size(24.dp)
            )
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(8.dp))

            // Lock icon
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .shadow(
                        elevation = 10.dp,
                        shape = RoundedCornerShape(16.dp),
                        ambientColor = GreenShadow,
                        spotColor = GreenShadow
                    )
                    .background(Green500, RoundedCornerShape(16.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Lock,
                    contentDescription = null,
                    tint = TextOnPrimary,
                    modifier = Modifier.size(30.dp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "Enter Verification Code",
                style = MaterialTheme.typography.headlineLarge,
                color = TextPrimary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Code sent to $otpEmail",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(24.dp))

            // OTP input
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(
                    text = "6-DIGIT CODE",
                    style = MaterialTheme.typography.labelMedium,
                    color = Green500
                )

                OutlinedTextField(
                    value = otpCode,
                    onValueChange = { newValue ->
                        val filtered = newValue.filter { it.isDigit() }.take(6)
                        otpCode = filtered
                    },
                    placeholder = {
                        Text("000000", color = TextMuted)
                    },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Number,
                        imeAction = ImeAction.Done
                    ),
                    keyboardActions = KeyboardActions(
                        onDone = {
                            if (isValidCode && !isLoading) {
                                onVerifyOTP(otpCode)
                            }
                        }
                    ),
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Outlined.Pin,
                            contentDescription = null,
                            tint = if (isValidCode) Green500 else TextMuted,
                            modifier = Modifier.size(20.dp)
                        )
                    },
                    trailingIcon = {
                        if (otpCode.isNotEmpty()) {
                            Icon(
                                imageVector = if (isValidCode) Icons.Default.CheckCircle else Icons.Default.Error,
                                contentDescription = null,
                                tint = if (isValidCode) Green500 else Red500,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Green500,
                        unfocusedBorderColor = BorderLight,
                        errorBorderColor = Red500,
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        cursorColor = Green500,
                        focusedContainerColor = Surface,
                        unfocusedContainerColor = Surface
                    ),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                )
            }

            // Error
            if (error != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(RedOverlay10, RoundedCornerShape(12.dp))
                        .border(1.dp, Red500.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                        .padding(12.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.ErrorOutline,
                            contentDescription = null,
                            tint = Red500,
                            modifier = Modifier.size(18.dp)
                        )
                        Text(
                            text = error,
                            style = MaterialTheme.typography.bodySmall,
                            color = Red500
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Verify button
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(32.dp),
                    color = Green500,
                    strokeWidth = 3.dp
                )
            } else {
                Button(
                    onClick = { onVerifyOTP(otpCode) },
                    enabled = isValidCode,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .then(
                            if (isValidCode) Modifier.shadow(
                                elevation = 10.dp,
                                shape = RoundedCornerShape(12.dp),
                                ambientColor = GreenShadow,
                                spotColor = GreenShadow
                            ) else Modifier
                        ),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Green500,
                        contentColor = TextOnPrimary,
                        disabledContainerColor = Green500.copy(alpha = 0.4f),
                        disabledContentColor = TextOnPrimary.copy(alpha = 0.6f)
                    )
                ) {
                    Text(
                        text = "VERIFY",
                        style = MaterialTheme.typography.titleSmall.copy(
                            letterSpacing = 0.35.sp
                        ),
                        color = TextOnPrimary
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Resend / Change email
            if (canResendOTP) {
                TextButton(onClick = onResendOTP) {
                    Text(
                        text = "Resend Code",
                        color = Green500,
                        style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold)
                    )
                }
            } else if (resendCooldownSeconds > 0) {
                Text(
                    text = "Resend in ${resendCooldownSeconds}s",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextMuted
                )
            }

            TextButton(onClick = onChangeEmail) {
                Text(
                    text = "Change Email",
                    color = TextSecondary,
                    style = MaterialTheme.typography.bodySmall
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}
