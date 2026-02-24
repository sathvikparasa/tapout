# Feat: Risk Meter Info Popup

## Objective

Make the risk meter card tappable. Tapping it opens a bottom sheet explaining what LOW, MEDIUM, and HIGH risk mean so users understand how the system works.

## Design Reference

Fetch the exact visual design from Figma before writing any UI code:

- **File:** https://www.figma.com/design/u4urUqE3Mns7qdHLs8LcE4/TapOut
- **Layer:** All pages under "CLAUDE IMPLEMENTATION"
- Use `get_figma_data` to extract colors, spacing, corner radii, and typography. Use `download_figma_images` for any assets. Do not guess any design values.

## File to Modify

**Only touch:** `warnabrotha/warnabrotha/Views/ButtonsTab.swift`

The risk meter card is the `riskMeterCard` computed property (~line 230). It lives inside `riskIndicatorsSection`, which is rendered in the main `body` VStack.

## Implementation

### 1. Add state to `ButtonsTab`

```swift
@State private var showRiskInfo = false
```

### 2. Make the card tappable

Wrap `riskMeterCard` in `riskIndicatorsSection` with a `.onTapGesture` (or `Button`) that sets `showRiskInfo = true`. Add a small info icon (`"info.circle"`) to the card's header row (next to "Current Risk Meter" and `LiveBadge`) to signal it's tappable.

### 3. Add the sheet

Attach `.sheet(isPresented: $showRiskInfo)` on `riskIndicatorsSection` (not the whole body). The sheet content is a self-contained `RiskInfoSheet` view defined at the bottom of the file.

### 4. `RiskInfoSheet` content

Three rows — one per risk level — each showing:
- Colored icon matching the level (use `riskLevelColor` logic: LOW = `AppColors.success`, MEDIUM = `AppColors.warning`, HIGH = `AppColors.dangerBright`)
- Level label (LOW / MEDIUM / HIGH)
- One-line description:
  - **LOW** — No recent TAPS activity. You're likely safe.
  - **MEDIUM** — Some recent reports. Stay alert.
  - **HIGH** — Active TAPS presence reported. Move your car.

Match all typography, spacing, corner radii, and colors exactly to the Figma design.

## Constraints

- **Do not modify** `AppViewModel.swift`, `APIModels.swift`, or any file in `Services/`
- **Do not modify** `.xcodeproj` or `.pbxproj`
- **Do not commit** anything to git
- Pure SwiftUI only — no UIKit, no external libraries
- Do not break check-in/out, reporting, feed, or any other existing functionality
