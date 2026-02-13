# TapOut Android UI Redesign — Implementation Plan

## Overview

Complete UI redesign from dark tactical theme to light modern aesthetic. All existing functionality, API integrations, ViewModels, and business logic remain **untouched**. Only UI layer files change.

---

## Design System Summary (extracted from Figma)

### Color Palette
| Token | Hex | Usage |
|---|---|---|
| Primary Green | `#9CAF88` | Buttons, accents, active nav, icons |
| Alert Red | `#E57373` | Report TAPS button, alert icons |
| Background | `#F7F7F7` | Page backgrounds |
| Surface/Card | `#FFFFFF` | Cards, inputs, bottom sheets |
| Text Primary | `#0F172A` / `#2D2D27` | Headings, bold text |
| Text Secondary | `#64748B` | Descriptions, subtitles |
| Text Muted | `#94A3B8` | Placeholders, inactive nav |
| Border | `#E2E8F0` | Card borders, dividers |
| Border Light | `#F1F5F9` | Subtle borders |
| Live Green | `#22C55E` | LIVE indicator dot + text |
| Risk Yellow | `#FFD54F` | MEDIUM risk level |
| Risk Green | `#81C784` | LOW risk bar |
| Risk Empty | `#F2F2EB` | Empty risk bar |
| Green Overlay 5% | `rgba(156,175,136,0.05)` | Feature card backgrounds |
| Green Overlay 10% | `rgba(156,175,136,0.1)` | Icon backgrounds, badges |

### Typography
| Style | Font | Weight | Size |
|---|---|---|---|
| App Title | DM Sans | ExtraBold | 36sp / 30sp |
| Section Heading | DM Sans | ExtraBold | 30sp |
| Card Heading | Plus Jakarta Sans | Bold | 18-20sp |
| Body | Plus Jakarta Sans | Medium/Regular | 14-16sp |
| Label (uppercase) | Plus Jakarta Sans | Bold | 8-10sp |
| Button Text | DM Sans ExtraBold / Plus Jakarta Sans SemiBold | — | 12-14sp |
| Nav Label | DM Sans | ExtraBold | 10sp |
| Caption | Plus Jakarta Sans | Medium | 10-12sp |

### Radii
- Small: 8dp, 12dp
- Medium: 24dp
- Large: 32dp, 40dp (action buttons)
- Full: 9999dp (pills, chips, avatars)

### Shadows
- Card: `0px 1px 2px rgba(0,0,0,0.05)`
- Elevated: `0px 10px 15px -3px rgba(0,0,0,0.1)`
- Button: `0px 20px 25px -5px rgba(156,175,136,0.2)`
- Red Button: `0px 20px 25px -5px rgba(229,115,115,0.3)`

### Icons
- Material Symbols Outlined (Thin weight) for nav/large icons
- Material Icons / Material Icons Round for UI icons

---

## Screen-to-Code Mapping

| # | Figma Screen | Existing File | Notes |
|---|---|---|---|
| 1 | Welcome to TapOut | `WelcomeScreen.kt` | Same functionality, new look |
| 2 | Verify Student Email | `EmailVerificationScreen.kt` | Same functionality, new look |
| 3 | TapOut Dashboard | `ReportTab.kt` (Home tab) | Same functionality, new look |
| 4 | Recent Taps Feed | `FeedTab.kt` (Feed tab) | Same functionality, new look |
| 5 | Campus Parking Map | `MapTab.kt` (Map tab) | New: search bar + redesigned bottom sheet |

### Navigation Changes
| Current | New |
|---|---|
| COMMAND (shield) | Home (grid_view) |
| FEED (sensors) | Feed (rss_feed) |
| MAP (map) | Map (map/location_on) |

### Features to Preserve NOT in Figma
- Snackbar error/success messaging
- Pull-to-refresh behavior
- Notification permission dialog flow
- Check-out functionality (button state change on Dashboard)
- Vote toggling logic on feed items

### New UI Elements (not in current app)
- **Search bar on Map page** — "Search campus lots..." with glassmorphism
- **LIVE indicator badges** — green dot + "LIVE" text on Risk Meter and Map bottom sheet
- **Recent Activity card on Dashboard** — glassmorphism feed preview
- **"View Map" link on Dashboard** — navigates to Map tab

---

## Files Modified vs Untouched

### MODIFIED (UI layer only)
```
ui/theme/Color.kt          — Complete rewrite (new palette)
ui/theme/Theme.kt           — Switch to light color scheme
ui/theme/Type.kt            — New fonts (DM Sans + Plus Jakarta Sans)
ui/components/Components.kt — Redesign all shared components
ui/screens/WelcomeScreen.kt
ui/screens/EmailVerificationScreen.kt
ui/screens/ReportTab.kt
ui/screens/FeedTab.kt
ui/screens/MapTab.kt
ui/screens/MainScreen.kt    — Redesign bottom nav bar
MainActivity.kt             — Update status bar to light theme
```

### UNTOUCHED (data/business layer)
```
data/api/ApiService.kt
data/api/AuthInterceptor.kt
data/model/ApiModels.kt
data/repository/AppRepository.kt
data/repository/TokenRepository.kt
data/service/FCMService.kt
di/AppModule.kt
ui/viewmodel/AppViewModel.kt
WarnABrothaApp.kt
```

### POSSIBLY NEW
```
build.gradle.kts            — Add DM Sans / Plus Jakarta Sans font dependencies (if using Google Fonts library, otherwise bundle .ttf)
res/font/                   — Font files if bundling
```

---

## Phased Implementation

### Phase 0: Design System Foundation
**Files:** `Color.kt`, `Type.kt`, `Theme.kt`, `build.gradle.kts`

1. Replace entire `Color.kt` with new palette (green primary, light backgrounds, all tokens above)
2. Rewrite `Type.kt` with DM Sans + Plus Jakarta Sans font families and all style variants
3. Update `Theme.kt` to use `lightColorScheme()` instead of `darkColorScheme()`, map new colors
4. Update `MainActivity.kt` status bar — light status bar with dark icons (instead of dark bar with light icons)
5. Add font dependencies (either Google Fonts Compose library or bundle .ttf files in `res/font/`)

**Why first:** Every screen depends on the design tokens. Changing these first means all subsequent screen work uses the correct colors/fonts from the start.

**Risk:** App will look broken after this phase since screens still reference old color names. This is expected and resolved in subsequent phases.

---

### Phase 1: Auth Screens (Welcome + Email Verification)
**Files:** `WelcomeScreen.kt`, `EmailVerificationScreen.kt`

#### 1a. Welcome Screen
- Light #F7F7F7 background with subtle green blur circles (Canvas/Brush radial gradients)
- Centered TapOut branding: shield icon in green rounded container, "Tap" dark + "Out" green, subtitle
- 4 feature cards: green icon in rounded-8dp green bg, bold title, regular description, 12dp rounded border with 5% green overlay
- Green "GET STARTED" button (full width, 12dp radius, shadow, uppercase DM Sans)
- "Already have an account? Log In" footer text
- **Preserves:** `onGetStarted` callback → `viewModel.register()`

#### 1b. Email Verification Screen
- Back arrow button (green arrow_back_ios_new)
- Centered parking icon in green rounded container with shadow
- "Verify Your Student Email" heading + description
- "UNIVERSITY EMAIL" label (green, uppercase, tiny)
- Email input: white bg, rounded-12dp, 2px border, mail icon, placeholder "yourname@ucdavis.edu"
- Info hint with info icon: "Must use UC Davis email address"
- Green "SUBMIT →" button
- Illustration placeholder area (can use existing or omit initially)
- "Having trouble? Contact Support" footer
- **Preserves:** email validation logic, `onVerify(email)` callback

**Why second:** These screens are self-contained (no tab nav dependency) and are the entry point — verifying the design system works before tackling the main app.

---

### Phase 2: Main Screen + Navigation Bar
**Files:** `MainScreen.kt`

- Redesign bottom navigation bar:
  - Frosted glass effect: `backgroundColor = Color.White.copy(alpha = 0.95f)` with top border
  - Three items: Home (grid_view), Feed (rss_feed), Map (map)
  - Active: green icon + green label (DM Sans ExtraBold 10sp)
  - Inactive: muted (#2D2D27 at 30% opacity) icon + label
  - Feed tab notification badge: red circle with white count
- Remove old tactical "COMMAND/FEED/MAP" labels
- **Preserves:** tab state, selectedTab index, all tab composable references

**Why third:** The nav bar wraps all three main tabs. Getting this right creates the frame for phases 3-5.

---

### Phase 3: Dashboard (Home Tab)
**Files:** `ReportTab.kt`, `Components.kt` (partial)

- **Header:** "TapOut" logo (DM Sans ExtraBold 30sp, "Tap" dark + "Out" green) + notification bell button (white circle, subtle border/shadow)
- **Lot Selector:** "SELECT PARKING ZONE" green label + white dropdown card (rounded-24dp, shadow, chevron)
- **Action Buttons:** Two large side-by-side buttons (rounded-40dp):
  - CHECK IN: green (#9CAF88) with local_parking icon, DM Sans uppercase
  - REPORT TAPS: red (#E57373) with report icon, DM Sans uppercase
  - Both have colored shadows matching their background
- **Risk Meter Card:** White card (rounded-32dp, subtle border/shadow)
  - "CURRENT RISK METER" label + green LIVE badge (green dot + "LIVE")
  - Bar chart visualization: 3 bars (green/yellow/empty)
  - Risk level text: "MEDIUM" in yellow (DM Sans ExtraBold 30sp)
  - Subtitle: description text
- **Recent Activity:** Section header "Recent Activity" + "View Map >" link
  - Glassmorphism activity card (backdrop blur, semi-transparent white, rounded-24dp)
  - Red report icon in light red circle + event title + timestamp
- **Preserves:** lot selection, check-in/check-out, report sighting, risk prediction display, all ViewModel calls

**Components to extract/rebuild in Components.kt:**
- `TapOutLogo` — branded "TapOut" text
- `LotSelectorCard` — dropdown
- `ActionButton` — large rounded action button
- `RiskMeterCard` — risk visualization
- `ActivityCard` — glassmorphism feed item
- `LiveBadge` — green dot + LIVE text
- `SectionHeader` — title + optional action

---

### Phase 4: Feed Tab
**Files:** `FeedTab.kt`, `Components.kt` (partial)

- **Header:** Sticky with backdrop blur
  - Small TapOut logo
  - "Recent Taps" heading (DM Sans ExtraBold 30sp)
- **Filter Chips:** Horizontal scroll
  - Active chip: green fill (#9CAF88) with white text, rounded-full
  - Inactive chip: white fill with #E2E8F0 border, #64748B text
  - Chips: ALL LOTS, MU, HUTCH, ARC (dynamic from lot list)
- **Subheader:** "Showing reports from last 3 hours" + green LIVE badge
- **Feed Items:** White cards with green left border (12px thick), rounded-12dp
  - Time in green uppercase (11sp)
  - Lot name in bold (18sp)
  - Thumbs up/down icons with counts on right
  - Older items at 50% opacity (fade based on age)
- **End Indicator:** Dots + "END OF 3-HOUR WINDOW" text
- **Bottom Nav:** Feed tab active (green)
- **Preserves:** feed filter logic, vote up/down/toggle, feed data loading, notification badge count

**Components to rebuild:**
- `FeedItemCard` — card with left border accent
- `FilterChip` — active/inactive lot filter
- `VoteButtons` — thumbs up/down with counts

---

### Phase 5: Map Tab
**Files:** `MapTab.kt`, `Components.kt` (partial)

- **Search Bar (NEW):** Glassmorphism floating bar at top
  - Backdrop blur, semi-transparent white, rounded-12dp, shadow
  - Search icon + "Search campus lots..." placeholder
  - Filters map markers on text input (client-side lot name matching)
- **Map:** Google Maps (same setup) but with redesigned markers:
  - **Selected marker:** Large green icon (local_parking) in green rounded container with white border, shadow, green ring pulse, lot name label pill below
  - **Unselected markers:** Smaller, muted green, lot name label below
- **Map Controls:** Right side floating buttons
  - My Location button (white, rounded-12dp, shadow)
  - Zoom +/- buttons (stacked, white, rounded-12dp, shadow)
- **Bottom Sheet:** Redesigned lot details
  - Drag handle pill
  - Lot name (Bold 20sp) + subtitle "Zone XXXX • UC Davis Campus"
  - Green LIVE badge
  - Two stat cards side by side (rounded-12dp, #F7F7F7 bg):
    - Users checked in: group icon (green) + count
    - Taps in last hour: touch_app icon (green) + count
  - (CHECK IN / REPORT TAPS buttons can be added below stats, matching Dashboard button style but smaller)
- **Bottom Nav:** Map tab active (green, location_on icon)
- **Preserves:** Google Maps integration, marker tap handling, check-in/report from map, lot stats loading

**New ViewModel addition (minimal):**
- Add `searchQuery: String` to `AppUiState` for lot search filtering
- Add `updateSearchQuery(query: String)` function
- Filter `parkingLots` list based on query for marker visibility

---

## Implementation Order Rationale

```
Phase 0 (Foundation) → Phases 1-5 all depend on correct design tokens
Phase 1 (Auth)       → Self-contained, validates the design system works
Phase 2 (Nav)        → Frame for main app, needed before tab screens
Phase 3 (Dashboard)  → Primary screen, most components to build
Phase 4 (Feed)       → Reuses components from Phase 3
Phase 5 (Map)        → Most complex (Google Maps + new search), done last
```

Each phase produces a testable, reviewable increment. The app should build and run after each phase (though unfinished screens may look inconsistent until all phases complete).

---

## Risks & Notes

1. **Font bundling:** DM Sans and Plus Jakarta Sans are Google Fonts — we can either use `androidx.compose.ui.text.googlefonts` (requires internet) or bundle .ttf files in `res/font/` (offline, recommended for production). I recommend bundling.

2. **Glassmorphism in Compose:** The frosted glass / backdrop blur effect requires `Modifier.blur()` (API 31+) or a custom RenderEffect. For API 26+ support, we may need to approximate with semi-transparent backgrounds without actual blur on older devices.

3. **Map markers:** The Figma shows custom styled markers. In Google Maps Compose, custom markers require `BitmapDescriptor` from composable-rendered content. This is doable but requires `rememberMarkerState` + `MarkerComposable` or canvas-drawn bitmaps.

4. **Search bar on Map:** This is a new feature not in the current app. It needs a simple text filter over the parking lots list — minimal ViewModel change.

5. **Illustrations on Email Verification:** The Figma shows an SVG illustration. We can either download and bundle it as a vector drawable, or use a placeholder icon initially.

6. **"View Map" link on Dashboard:** Needs a callback to switch the selected tab from Home to Map. This is a minor wiring change in `MainScreen.kt`.
