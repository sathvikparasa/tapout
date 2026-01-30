package com.warnabrotha.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.warnabrotha.app.ui.components.BeveledBorder
import com.warnabrotha.app.ui.components.Win95BigButton
import com.warnabrotha.app.ui.components.Win95TitleBar
import com.warnabrotha.app.ui.theme.Win95Colors

@Composable
fun WelcomeScreen(
    isLoading: Boolean,
    onGetStarted: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Win95Colors.WindowBackground)
    ) {
        Win95TitleBar(title = "WarnABrotha")

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
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "WarnABrotha",
                    fontSize = 32.sp,
                    fontWeight = FontWeight.Bold,
                    color = Win95Colors.TitleBar
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "UC Davis Parking Companion",
                    fontSize = 16.sp,
                    color = Win95Colors.TextSecondary
                )

                Spacer(modifier = Modifier.height(32.dp))

                // Features list
                FeatureItem(icon = "🚗", text = "Check in when you park")
                Spacer(modifier = Modifier.height(12.dp))
                FeatureItem(icon = "⚠️", text = "Get warned about TAPS")
                Spacer(modifier = Modifier.height(12.dp))
                FeatureItem(icon = "📢", text = "Report TAPS sightings")
                Spacer(modifier = Modifier.height(12.dp))
                FeatureItem(icon = "📊", text = "View probability predictions")

                Spacer(modifier = Modifier.height(48.dp))

                if (isLoading) {
                    CircularProgressIndicator(
                        color = Win95Colors.TitleBar
                    )
                } else {
                    Win95BigButton(
                        title = "Get Started",
                        subtitle = "Tap to register your device",
                        onClick = onGetStarted,
                        backgroundColor = Win95Colors.SafeGreen,
                        textColor = Win95Colors.TitleBarText,
                        height = 80.dp,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
    }
}

@Composable
private fun FeatureItem(icon: String, text: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = icon,
            fontSize = 24.sp
        )
        Spacer(modifier = Modifier.width(16.dp))
        Text(
            text = text,
            fontSize = 16.sp,
            color = Win95Colors.TextPrimary
        )
    }
}
