# Goal: Build a Preferences Page

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

---

## Objective

Build a Preferences sheet that slides up from the gear icon in the top bar of `ButtonsTab.swift`. It lets the user pick their preferred parking payment app (AMP Park or Honk Mobile), which controls where push notification taps redirect them.

---

## Exact Changes Required

### 1. `warnabrotha/warnabrotha/Views/ButtonsTab.swift`

- Change the top-bar button icon from `"person.crop.circle"` to `"gearshape.fill"` (line ~143).
- Add `@State private var showPreferences = false` to `ButtonsTab`.
- Replace the `// Profile placeholder` comment with `showPreferences = true`.
- Add `.sheet(isPresented: $showPreferences) { PreferencesView() }` to the root view in `ButtonsTab`.

### 2. Create `warnabrotha/warnabrotha/Views/PreferencesView.swift` (**new file — add to Xcode target**)

Build this view to match the Figma "Noti Preferences" screen (node `299:7` in file `u4urUqE3Mns7qdHLs8LcE4`). Use the Figma MCP to fetch the design. Key layout from the Figma:

**Header**
- Title: `"Preferences"` — use `.displayFont(size: 28)`, `AppColors.textPrimary`
- Standard top padding, no back button (it's a sheet)

**Section**
- Label: `"What Parking app do you use?"` — `.appFont(size: 16, weight: .bold)`, `AppColors.textPrimary`

**Two selection cards** (rounded rect, `AppColors.surface`, border `AppColors.border`, `cornerRadius: 12`)
Each card contains:
- App name text: `"AMP Parking"` / `"Honk Mobile"` — `.appFont(size: 15, weight: .semibold)`
- App icon image on the right (use SF Symbol `"car.fill"` for AMP, `"p.circle.fill"` for Honk as placeholders — Figma has images but we don't have the assets)
- Selection indicator: filled `Circle().fill(AppColors.accent)` with checkmark when selected, empty `Circle().stroke(AppColors.border)` when not selected
- Tapping a card calls `ParkingPaymentApp.setPreferred(app)` and updates local `@State var selected`

**Tip card** (below the two option cards)
- Light background: `AppColors.accent.opacity(0.08)`, `cornerRadius: 12`
- Info icon: `"info.circle.fill"` in `AppColors.accent`
- Body text: `"Selecting your parking app allows our app to take you directly to your desired parking app, decreasing the time it takes you to pay for parking after a report."` — `.appFont(size: 13)`, `AppColors.textSecondary`

**Preference persistence**
- On appear, read `ParkingPaymentApp.preferred` to set initial selection state.
- `ParkingPaymentApp` enum and `setPreferred(_:)` already exist in `warnabrothaApp.swift`. Use them directly — do not redefine them.

---

## Rules

- **Use the Figma MCP** to fetch node `299:7` from file `u4urUqE3Mns7qdHLs8LcE4` for exact spacing, colors, and layout. Match it.
- **Use the existing TapOut theme** — `AppColors`, `.appFont()`, `.displayFont()`, `.cardStyle()`. No hardcoded hex colors.
- **No new ViewModel class.** All state is local `@State` in `PreferencesView`.
- **Do not modify `.xcodeproj`** — flag the new file so the user can add it to the Xcode target manually.
- Do not commit to git without permission.
