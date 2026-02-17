package com.warnabrotha.app.ui.theme

import android.app.Activity
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val TapOutColorScheme = lightColorScheme(
    primary = Green500,
    onPrimary = TextOnPrimary,
    primaryContainer = GreenOverlay10,
    onPrimaryContainer = TextPrimary,
    secondary = Green400,
    onSecondary = TextOnPrimary,
    secondaryContainer = GreenOverlay5,
    onSecondaryContainer = TextPrimary,
    tertiary = LiveGreen,
    onTertiary = TextOnPrimary,
    error = Red500,
    onError = TextOnPrimary,
    errorContainer = RedOverlay10,
    onErrorContainer = TextPrimary,
    background = Background,
    onBackground = TextPrimary,
    surface = Surface,
    onSurface = TextPrimary,
    surfaceVariant = Background,
    onSurfaceVariant = TextSecondary,
    outline = Border,
    outlineVariant = BorderLight,
)

@Composable
fun WarnABrothaTheme(
    content: @Composable () -> Unit
) {
    val view = LocalView.current

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = Background.toArgb()
            window.navigationBarColor = Surface.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = true
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = true
        }
    }

    MaterialTheme(
        colorScheme = TapOutColorScheme,
        typography = AppTypography,
        content = content
    )
}
