package com.warnabrotha.app.ui.theme

import androidx.compose.ui.graphics.Color

// === TAPOUT LIGHT THEME PALETTE ===

// Primary green
val Green500 = Color(0xFF9CAF88)
val Green400 = Color(0xFFB0BF9F)
val Green600 = Color(0xFF7D8E6D)
val GreenOverlay5 = Color(0x0D9CAF88)   // 5% opacity
val GreenOverlay10 = Color(0x1A9CAF88)  // 10% opacity
val GreenOverlay20 = Color(0x339CAF88)  // 20% opacity
val GreenShadow = Color(0x339CAF88)     // for button shadows

// Alert red
val Red500 = Color(0xFFE57373)
val Red400 = Color(0xFFEF5350)
val Red600 = Color(0xFFEF4444)
val RedOverlay10 = Color(0x1AE57373)
val RedShadow = Color(0x4DE57373)       // for button shadows

// Risk level colors
val RiskLow = Color(0xFF81C784)
val RiskMedium = Color(0xFFFFD54F)
val RiskHigh = Color(0xFFE57373)
val RiskBarEmpty = Color(0xFFF2F2EB)

// Live indicator
val LiveGreen = Color(0xFF22C55E)

// Backgrounds
val Background = Color(0xFFF7F7F7)
val Surface = Color(0xFFFFFFFF)

// Text hierarchy
val TextPrimary = Color(0xFF0F172A)
val TextPrimaryAlt = Color(0xFF2D2D27)  // used in dashboard
val TextSecondary = Color(0xFF64748B)
val TextMuted = Color(0xFF94A3B8)
val TextMutedDark = Color(0xFF6B7280)   // search placeholder
val TextOnPrimary = Color(0xFFFFFFFF)

// Borders and dividers
val Border = Color(0xFFE2E8F0)
val BorderLight = Color(0xFFF1F5F9)
val BorderSubtle = Color(0x0D000000)    // rgba(0,0,0,0.05)

// Shadows (used as tint colors in Compose shadow/elevation)
val ShadowLight = Color(0x1A000000)     // rgba(0,0,0,0.1)

// Nav inactive
val NavInactive = Color(0x4D2D2D27)     // #2D2D27 at 30% opacity

// Chip / badge
val ChipActiveBg = Green500
val ChipActiveText = Color(0xFFFFFFFF)
val ChipInactiveBg = Color(0xFFFFFFFF)
val ChipInactiveBorder = Border
val ChipInactiveText = TextSecondary
val BadgeRed = Color(0xFFEF4444)

// Home bar indicator
val HomeIndicator = Border

// === SEMANTIC ALIASES ===
val AccentPrimary = Green500
val AccentPrimaryLight = Green400
val AccentPrimaryDark = Green600
val AlertRed = Red500
val AlertRedLight = Red400
val SafeGreen = LiveGreen
val InfoBlue = Color(0xFF3B82F6)

// Card backgrounds
val CardBackground = Surface
val CardBackgroundMuted = Background

// Legacy compat - keep these so existing screen code compiles during migration
val DarkBackground = Background
val DarkSurface = Surface
val DarkCard = Surface
val DarkCardElevated = Surface
val Amber500 = Green500
val Amber400 = Green400
val Amber600 = Green600
val AmberGlow = GreenOverlay20
val Black900 = Background
val Black800 = Surface
val Black700 = Surface
val Black600 = Surface
val Black500 = Surface
val Blue500 = InfoBlue
val Blue400 = InfoBlue
val Blue600 = InfoBlue
val BlueGlow = Color(0x333B82F6)
val Green500Legacy = LiveGreen
val Green400Legacy = Color(0xFF4ADE80)
val GreenGlow = Color(0x3322C55E)
val Red400Legacy = Red400
val Red600Legacy = Red600
val RedGlow = RedOverlay10
val TextWhite = TextPrimary
val TextGray = TextSecondary
val BorderColor = Border
val DividerColor = Border
val AccentBlue = InfoBlue
val BrandBlue = InfoBlue
val WarningAmber = RiskMedium
