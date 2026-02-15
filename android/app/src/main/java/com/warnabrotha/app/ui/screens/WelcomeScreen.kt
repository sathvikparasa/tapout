package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.theme.*

@Composable
fun WelcomeScreen(
    isLoading: Boolean,
    onGetStarted: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Background)
    ) {
        // Subtle green blur circles
        Box(
            modifier = Modifier
                .size(192.dp)
                .offset(x = (-48).dp, y = (-48).dp)
                .blur(32.dp)
                .background(GreenOverlay10, RoundedCornerShape(percent = 50))
        )
        Box(
            modifier = Modifier
                .size(192.dp)
                .align(Alignment.BottomEnd)
                .offset(x = 48.dp, y = 48.dp)
                .blur(32.dp)
                .background(GreenOverlay10, RoundedCornerShape(percent = 50))
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 32.dp)
                .padding(top = 48.dp, bottom = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Top: Logo + Branding
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Shield icon in green container
                Box(
                    modifier = Modifier
                        .size(80.dp)
                        .background(GreenOverlay10, RoundedCornerShape(16.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Outlined.VerifiedUser,
                        contentDescription = null,
                        tint = Green500,
                        modifier = Modifier.size(48.dp)
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // "TapOut" branded title
                Text(
                    text = buildAnnotatedString {
                        withStyle(SpanStyle(color = TextPrimary)) {
                            append("Tap")
                        }
                        withStyle(SpanStyle(color = Green500)) {
                            append("Out")
                        }
                    },
                    style = MaterialTheme.typography.displayLarge,
                    textAlign = TextAlign.Center
                )

                Text(
                    text = "Tap out of parking",
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary,
                    textAlign = TextAlign.Center
                )
            }

            // Middle: Feature cards
            Column(
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                FeatureCard(
                    icon = Icons.Outlined.NotificationsActive,
                    title = "Real-time alerts",
                    description = "Get notified when TAPS\nenforcement is spotted nearby."
                )
                FeatureCard(
                    icon = Icons.Outlined.Group,
                    title = "Community-powered",
                    description = "Join fellow Aggies in reporting active\nenforcement areas."
                )
                FeatureCard(
                    icon = Icons.Outlined.Timer,
                    title = "Check in/out tracking",
                    description = "Smart reminders to pay or move\nbefore your time expires."
                )
                FeatureCard(
                    icon = Icons.Outlined.Map,
                    title = "Campus-wide coverage",
                    description = "Detailed coverage across all UC\nDavis parking zones."
                )
            }

            // Bottom: CTA
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(32.dp),
                        color = Green500,
                        strokeWidth = 3.dp
                    )
                } else {
                    Button(
                        onClick = onGetStarted,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                            .shadow(
                                elevation = 10.dp,
                                shape = RoundedCornerShape(12.dp),
                                ambientColor = GreenShadow,
                                spotColor = GreenShadow
                            ),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Green500,
                            contentColor = TextOnPrimary
                        )
                    ) {
                        Text(
                            text = "GET STARTED",
                            style = MaterialTheme.typography.labelLarge.copy(
                                fontFamily = DmSansFamily,
                                fontWeight = FontWeight.ExtraBold,
                                letterSpacing = 1.4.sp
                            )
                        )
                    }
                }

                // "Already have an account? Log In"
                Text(
                    text = buildAnnotatedString {
                        withStyle(SpanStyle(color = TextSecondary)) {
                            append("Already have an account? ")
                        }
                        withStyle(
                            SpanStyle(
                                color = Green500,
                                fontWeight = FontWeight.Bold
                            )
                        ) {
                            append("Log In")
                        }
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}

@Composable
private fun FeatureCard(
    icon: ImageVector,
    title: String,
    description: String
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(GreenOverlay5, RoundedCornerShape(12.dp))
            .border(1.dp, GreenOverlay10, RoundedCornerShape(12.dp))
            .padding(17.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalAlignment = Alignment.Top
    ) {
        // Green icon container
        Box(
            modifier = Modifier
                .size(36.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(Green500),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = TextOnPrimary,
                modifier = Modifier.size(20.dp)
            )
        }

        Column {
            Text(
                text = title,
                style = MaterialTheme.typography.headlineSmall,
                color = TextPrimary
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary,
                lineHeight = 20.sp
            )
        }
    }
}
