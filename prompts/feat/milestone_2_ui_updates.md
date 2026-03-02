# Milestone 2 UI Fixes — iOS Feature Parity

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Operational Rules

- Use the existing TapOut theme in `warnabrotha/warnabrotha/Theme/AppTheme.swift` (`AppColors`, `PrimaryButton`, `DashboardActionButton`, `.appFont()`, `.displayFont()`).
- All new state goes in `AppViewModel` (`warnabrotha/warnabrotha/ViewModels/AppViewModel.swift`) as `@Published` properties. Do not create new ViewModel classes.
- Keep it native SwiftUI. No new files unless absolutely necessary — flag any that need Xcode target registration.
- Do not modify `.xcodeproj` or `.pbxproj` files.
- Do not commit anything to git without prior permission.
- Ask before making any change that could break existing functionality.

---

## Task 1 — Fix Button Width (too skinny)

**File:** `warnabrotha/warnabrotha/Views/ButtonsTab.swift` (~line 78–80)

The `HStack` containing the two `DashboardActionButton`s has compounded horizontal padding that makes the buttons too narrow:

```swift
.padding(.horizontal, 24)
.padding(12)          // ← this adds 12pt left+right ON TOP of the 24 already there
```

**Fix:** Change `.padding(12)` to `.padding(.vertical, 12)` so only vertical padding is added (not extra horizontal).

Before:
```swift
.padding(.horizontal, 24)
.padding(12)
```

After:
```swift
.padding(.horizontal, 24)
.padding(.vertical, 12)
```

Fetch the Figma file (`https://www.figma.com/design/u4urUqE3Mns7qdHLs8LcE4/TapOut`, layer "CLAUDE IMPLEMENTATION") to verify the intended button proportions if the above fix looks wrong.

---

## Task 2 — Risk Meter: Add Lot Name to Message

**File:** `warnabrotha/warnabrotha/Views/ButtonsTab.swift` (line ~287)

The risk message currently shows `viewModel.riskMessage` (e.g. "Officers on patrol") with no lot context.

**Fix:** Prefix the message with the selected lot name. In `riskMeterCard`, change the `Text` that displays the risk message:

Before:
```swift
Text(viewModel.riskMessage)
    .appFont(size: 10, weight: .medium)
    .foregroundColor(AppColors.textPrimary.opacity(0.6))
    .lineLimit(1)
```

After — prepend the lot name/code inline:
```swift
Text("\(viewModel.selectedLot?.name ?? "") — \(viewModel.riskMessage)")
    .appFont(size: 10, weight: .medium)
    .foregroundColor(AppColors.textPrimary.opacity(0.6))
    .lineLimit(1)
```

Use `viewModel.selectedLot?.name` (the full lot name, e.g. "Lot 1"). Fall back to empty string if nil so "Loading..." still shows correctly.

---

## Task 3 — Map Sheet: "CHECK IN" → "GET ALERTS"

**File:** `warnabrotha/warnabrotha/Views/MapTab.swift` (line ~413–419)

The lot detail sheet bottom panel has a `PrimaryButton` labeled "CHECK IN". It should match the main dashboard button text and icon.

Before:
```swift
PrimaryButton(
    title: "CHECK IN",
    icon: "arrow.down.circle",
    color: isCheckedInElsewhere ? AppColors.textMuted : AppColors.accent,
    action: onCheckIn
)
```

After:
```swift
PrimaryButton(
    title: "GET ALERTS",
    icon: "bell.fill",
    color: isCheckedInElsewhere ? AppColors.textMuted : AppColors.accent,
    action: onCheckIn
)
```

The `action` and disabled/opacity logic stay the same — only the label and icon change.

---

## Task 4 — Dropdown: Dismiss on Outside Tap

**File:** `warnabrotha/warnabrotha/Views/ButtonsTab.swift`

When `showLotDropdown == true`, tapping outside the dropdown should dismiss it. The dropdown is rendered inside a `ZStack(alignment: .top)` in `ButtonsTab.body`.

**Fix:** In `ButtonsTab.body`, inside the outer `ZStack`, add a full-screen transparent tap target beneath the dropdown's content layer. Add it as the first child of the outer `ZStack` so it sits below the UI but above the background:

```swift
// Dismiss dropdown on outside tap
if showLotDropdown {
    Color.clear
        .contentShape(Rectangle())
        .ignoresSafeArea()
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                showLotDropdown = false
            }
        }
        .zIndex(9) // below dropdown (zIndex 10) but above scrollable content
}
```

Place this block directly inside the outer `ZStack` in `body`, before (or after) the `VStack` that holds the main UI, so that when the dropdown is open the whole screen outside the dropdown responds to taps.

---

## Task 5 — Scan Result: "Scan Another" → "Done"

**File:** `warnabrotha/warnabrotha/Views/ScanTab.swift` (line ~428–432)

After a successful scan, the green `PrimaryButton` says "Scan Another". It should say "Done" and navigate to the scan history tab.

Before:
```swift
PrimaryButton(
    title: "Scan Another",
    icon: "doc.viewfinder",
    action: { viewModel.resetScan() }
)
```

After:
```swift
PrimaryButton(
    title: "Done",
    icon: "checkmark",
    action: {
        viewModel.resetScan()
        viewModel.scanSubTab = .records
    }
)
```

This resets scan state AND navigates to the history tab — a natural "done" flow. The `PrimaryButton` default color is `AppColors.accent` (sage green), so no color param needed.

---

## Task 6 — Feed: Show Whole Day (not last 3 hours)

**File:** `warnabrotha/warnabrotha/Views/FeedTab.swift` (lines 86 and 127)

The feed already loads all available sightings from the API (no client-side time filtering in `loadAllFeeds()`). The "3 hours" references are purely display text. Update both strings:

**Line ~86** — sub-header label:
```swift
// Before
Text("Showing reports from last 3 hours")

// After
Text("Showing today's reports")
```

**Line ~127** — end-of-list marker:
```swift
// Before
Text("End of 3-hour window")

// After
Text("End of today's reports")
```

No logic changes needed — data layer already returns all sightings.

---

## Verification Checklist

After making all changes, confirm:
- [ ] Dashboard buttons fill horizontal space without extra side margins
- [ ] Risk meter label reads e.g. "Lot 1 — Officers on patrol"
- [ ] Map sheet bottom button says "GET ALERTS" with `bell.fill` icon
- [ ] Tapping outside the lot selector dropdown dismisses it
- [ ] Post-scan green button says "Done" and goes to history tab
- [ ] Feed header says "Showing today's reports" / "End of today's reports"
