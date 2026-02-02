package com.warnabrotha.app.ui.theme

import android.app.Activity
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val TacticalColorScheme = darkColorScheme(
    primary = Amber500,
    onPrimary = Black900,
    primaryContainer = Amber600,
    onPrimaryContainer = TextWhite,
    secondary = Blue500,
    onSecondary = Black900,
    secondaryContainer = Black600,
    onSecondaryContainer = TextWhite,
    tertiary = Green500,
    onTertiary = Black900,
    error = Red500,
    onError = TextWhite,
    errorContainer = Red600,
    onErrorContainer = TextWhite,
    background = Black900,
    onBackground = TextWhite,
    surface = Black800,
    onSurface = TextWhite,
    surfaceVariant = Black700,
    onSurfaceVariant = TextGray,
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
            window.statusBarColor = Black900.toArgb()
            window.navigationBarColor = Black900.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = false
        }
    }

    MaterialTheme(
        colorScheme = TacticalColorScheme,
        typography = AppTypography,
        content = content
    )
}
