package com.warnabrotha.app.ui.theme

import androidx.compose.ui.graphics.Color

// === TACTICAL COMMAND CENTER PALETTE ===

// Deep blacks - layered depth
val Black900 = Color(0xFF050507)
val Black800 = Color(0xFF0A0A0D)
val Black700 = Color(0xFF111115)
val Black600 = Color(0xFF18181D)
val Black500 = Color(0xFF1F1F26)

// Hot amber - primary action color
val Amber500 = Color(0xFFFF6B00)
val Amber400 = Color(0xFFFF8C33)
val Amber600 = Color(0xFFCC5500)
val AmberGlow = Color(0x33FF6B00)

// Alert red - danger/urgent
val Red500 = Color(0xFFFF3B3B)
val Red400 = Color(0xFFFF5C5C)
val Red600 = Color(0xFFCC2F2F)
val RedGlow = Color(0x33FF3B3B)

// Status green - safe/success
val Green500 = Color(0xFF00D26A)
val Green400 = Color(0xFF33DB88)
val GreenGlow = Color(0x3300D26A)

// Cool blue - info/secondary
val Blue500 = Color(0xFF00A3FF)
val Blue400 = Color(0xFF33B5FF)
val Blue600 = Color(0xFF0082CC)
val BlueGlow = Color(0x3300A3FF)

// Text hierarchy
val TextWhite = Color(0xFFF0F0F2)
val TextGray = Color(0xFF8A8A94)
val TextMuted = Color(0xFF5A5A64)

// Borders and dividers
val Border = Color(0xFF2A2A32)
val BorderLight = Color(0xFF3A3A44)

// === SEMANTIC ALIASES ===
val DarkBackground = Black900
val DarkSurface = Black800
val DarkCard = Black700
val DarkCardElevated = Black600

val AccentPrimary = Amber500
val AccentPrimaryLight = Amber400
val AccentPrimaryDark = Amber600

val AlertRed = Red500
val AlertRedLight = Red400
val SafeGreen = Green500
val SafeGreenLight = Green400
val InfoBlue = Blue500

val TextPrimary = TextWhite
val TextSecondary = TextGray
val TextTertiary = TextMuted

val DividerColor = Border
val BorderColor = BorderLight

// Risk colors
val RiskLow = Green500
val RiskMedium = Amber500
val RiskHigh = Red500

// Legacy compatibility
val AccentBlue = Blue500
val BrandBlue = Blue500
val WarningAmber = Amber500
