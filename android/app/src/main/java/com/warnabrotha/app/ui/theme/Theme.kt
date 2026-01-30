package com.warnabrotha.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColorScheme = lightColorScheme(
    primary = Win95Colors.TitleBar,
    onPrimary = Win95Colors.TitleBarText,
    secondary = Win95Colors.SafeGreen,
    onSecondary = Color.White,
    background = Win95Colors.WindowBackground,
    onBackground = Win95Colors.TextPrimary,
    surface = Win95Colors.ButtonFace,
    onSurface = Win95Colors.TextPrimary,
    error = Win95Colors.DangerRed,
    onError = Color.White
)

@Composable
fun WarnABrothaTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        content = content
    )
}
