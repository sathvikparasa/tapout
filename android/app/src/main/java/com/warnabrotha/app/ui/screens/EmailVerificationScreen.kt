package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.components.BeveledBorder
import com.warnabrotha.app.ui.components.Win95Button
import com.warnabrotha.app.ui.components.Win95TitleBar
import com.warnabrotha.app.ui.theme.Win95Colors

@Composable
fun EmailVerificationScreen(
    isLoading: Boolean,
    error: String?,
    onVerify: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var email by remember { mutableStateOf("") }
    val isValidEmail = email.endsWith("@ucdavis.edu") && email.length > 12

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Win95Colors.WindowBackground)
    ) {
        Win95TitleBar(title = "Email Verification")

        BeveledBorder(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Win95Colors.WindowBackground)
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Spacer(modifier = Modifier.height(32.dp))

                Text(
                    text = "Verify Your Email",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = Win95Colors.TitleBar
                )

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "Enter your UC Davis email address to continue",
                    fontSize = 14.sp,
                    color = Win95Colors.TextSecondary,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(32.dp))

                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    label = { Text("Email") },
                    placeholder = { Text("username@ucdavis.edu") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Email,
                        imeAction = ImeAction.Done
                    ),
                    keyboardActions = KeyboardActions(
                        onDone = {
                            if (isValidEmail && !isLoading) {
                                onVerify(email)
                            }
                        }
                    ),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Win95Colors.TitleBar,
                        focusedLabelColor = Win95Colors.TitleBar,
                        cursorColor = Win95Colors.TitleBar
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                if (!isValidEmail && email.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Email must end with @ucdavis.edu",
                        fontSize = 12.sp,
                        color = Win95Colors.DangerRed
                    )
                }

                if (error != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = error,
                        fontSize = 12.sp,
                        color = Win95Colors.DangerRed,
                        textAlign = TextAlign.Center
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                if (isLoading) {
                    CircularProgressIndicator(
                        color = Win95Colors.TitleBar
                    )
                } else {
                    Win95Button(
                        text = "Verify Email",
                        onClick = { onVerify(email) },
                        enabled = isValidEmail,
                        backgroundColor = if (isValidEmail) Win95Colors.SafeGreen else Win95Colors.ButtonFace,
                        textColor = if (isValidEmail) Win95Colors.TitleBarText else Win95Colors.TextSecondary,
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                Spacer(modifier = Modifier.weight(1f))

                BeveledBorder(
                    modifier = Modifier.fillMaxWidth(),
                    raised = false
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(Win95Colors.WindowBackground)
                            .padding(12.dp)
                    ) {
                        Text(
                            text = "🔒 We don't store your email address. It's only used for verification.",
                            fontSize = 12.sp,
                            color = Win95Colors.TextSecondary,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }
            }
        }
    }
}
