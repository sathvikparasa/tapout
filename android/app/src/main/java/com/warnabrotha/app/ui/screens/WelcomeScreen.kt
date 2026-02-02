package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.components.TacticalButton
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
            .background(Black900)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.weight(0.15f))

            // Logo area
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .background(
                        Brush.linearGradient(listOf(Amber500, Amber600)),
                        RoundedCornerShape(16.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Shield,
                    contentDescription = null,
                    tint = Black900,
                    modifier = Modifier.size(40.dp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "WARNABROTHA",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Black,
                color = Amber500,
                letterSpacing = 2.sp
            )

            Text(
                text = "UC DAVIS PARKING INTEL",
                style = MaterialTheme.typography.labelMedium,
                color = TextMuted,
                letterSpacing = 2.sp
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Features panel
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Black800, RoundedCornerShape(12.dp))
                    .border(1.dp, Border, RoundedCornerShape(12.dp))
                    .padding(16.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    FeatureRow(
                        icon = Icons.Outlined.Sensors,
                        title = "REAL-TIME ALERTS",
                        description = "Get notified when TAPS is spotted"
                    )
                    HorizontalDivider(color = Border)
                    FeatureRow(
                        icon = Icons.Outlined.Campaign,
                        title = "REPORT SIGHTINGS",
                        description = "Help warn other parkers"
                    )
                    HorizontalDivider(color = Border)
                    FeatureRow(
                        icon = Icons.Outlined.Analytics,
                        title = "RISK ANALYSIS",
                        description = "AI-powered probability predictions"
                    )
                    HorizontalDivider(color = Border)
                    FeatureRow(
                        icon = Icons.Outlined.Groups,
                        title = "COMMUNITY INTEL",
                        description = "Crowdsourced parking data"
                    )
                }
            }

            Spacer(modifier = Modifier.weight(0.3f))

            // CTA
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(32.dp),
                    color = Amber500,
                    strokeWidth = 3.dp
                )
            } else {
                TacticalButton(
                    text = "Get Started",
                    icon = Icons.Default.ArrowForward,
                    onClick = onGetStarted,
                    color = Amber500,
                    modifier = Modifier.fillMaxWidth()
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = "By continuing, you agree to our Terms of Service",
                style = MaterialTheme.typography.labelSmall,
                color = TextMuted,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
private fun FeatureRow(
    icon: ImageVector,
    title: String,
    description: String
) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .background(AmberGlow, RoundedCornerShape(8.dp))
                .border(1.dp, Amber500.copy(alpha = 0.3f), RoundedCornerShape(8.dp)),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = Amber500,
                modifier = Modifier.size(18.dp)
            )
        }

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = TextWhite,
                letterSpacing = 0.5.sp
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = TextMuted
            )
        }
    }
}
