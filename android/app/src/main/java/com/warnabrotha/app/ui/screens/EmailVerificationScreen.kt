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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.components.TacticalButton
import com.warnabrotha.app.ui.theme.*

@Composable
fun EmailVerificationScreen(
    isLoading: Boolean,
    error: String?,
    onVerify: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var email by remember { mutableStateOf("") }
    val isValidEmail = email.endsWith("@ucdavis.edu") && email.length > 12

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Black900)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(48.dp))

            // Header icon
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .background(
                        Brush.linearGradient(listOf(Blue500, Blue500.copy(alpha = 0.7f))),
                        RoundedCornerShape(12.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Email,
                    contentDescription = null,
                    tint = TextWhite,
                    modifier = Modifier.size(28.dp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "VERIFY EMAIL",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Black,
                color = TextWhite,
                letterSpacing = 1.sp
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "UC Davis email required",
                style = MaterialTheme.typography.labelMedium,
                color = TextMuted
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Input panel
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Black800, RoundedCornerShape(12.dp))
                    .border(1.dp, Border, RoundedCornerShape(12.dp))
                    .padding(16.dp)
            ) {
                Column {
                    Text(
                        text = "EMAIL ADDRESS",
                        style = MaterialTheme.typography.labelSmall,
                        color = TextMuted,
                        letterSpacing = 1.sp
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    OutlinedTextField(
                        value = email,
                        onValueChange = { email = it },
                        placeholder = {
                            Text(
                                "username@ucdavis.edu",
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
                                    onVerify(email)
                                }
                            }
                        ),
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Outlined.AlternateEmail,
                                contentDescription = null,
                                tint = if (isValidEmail) Green500 else TextMuted,
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
                            focusedBorderColor = Amber500,
                            unfocusedBorderColor = Border,
                            errorBorderColor = Red500,
                            focusedTextColor = TextWhite,
                            unfocusedTextColor = TextWhite,
                            cursorColor = Amber500,
                            focusedContainerColor = Black700,
                            unfocusedContainerColor = Black700
                        ),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    )

                    // Validation message
                    if (email.isNotEmpty() && !isValidEmail) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Default.Warning,
                                contentDescription = null,
                                tint = Red500,
                                modifier = Modifier.size(14.dp)
                            )
                            Text(
                                text = "Must be a @ucdavis.edu email",
                                style = MaterialTheme.typography.labelSmall,
                                color = Red500
                            )
                        }
                    }
                }
            }

            // Server error
            if (error != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(RedGlow, RoundedCornerShape(8.dp))
                        .border(1.dp, Red500.copy(alpha = 0.5f), RoundedCornerShape(8.dp))
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

            Spacer(modifier = Modifier.height(20.dp))

            // Verify button
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(32.dp),
                    color = Amber500,
                    strokeWidth = 3.dp
                )
            } else {
                TacticalButton(
                    text = "Verify",
                    icon = Icons.Default.Send,
                    onClick = { onVerify(email) },
                    enabled = isValidEmail,
                    color = if (isValidEmail) Amber500 else Black600,
                    modifier = Modifier.fillMaxWidth()
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Privacy notice
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Black800, RoundedCornerShape(8.dp))
                    .border(1.dp, Border, RoundedCornerShape(8.dp))
                    .padding(12.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Lock,
                        contentDescription = null,
                        tint = Green500,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = "We don't store your email. Used for verification only.",
                        style = MaterialTheme.typography.labelSmall,
                        color = TextMuted
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
