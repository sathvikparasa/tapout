# Fix: Nav Bar Icon Jump on Tab Switch

## Bug Description

When there is at least one recent sighting in `ButtonsTab`, switching tabs (Home → Feed/Scan/Map) causes the tab bar icons to shift upward. Switching back to Home causes them to shift back down. The tab bar height/position should be completely independent of tab content.

**Reproduction:**
1. Ensure there is a recent sighting (so `viewModel.feed?.sightings.first` is non-nil — this renders the stacked card layout in `recentActivitySection`)
2. Open the Home tab — note the tab bar position
3. Tap Feed, Scan, or Map tab — the tab bar icons jump upward
4. Tap Home again — they jump back down

## Root Cause

**File:** `warnabrotha/warnabrotha/ContentView.swift`

The authenticated layout uses a `VStack(spacing: 0)` where tab content sits above `AppTabBar`. When `ButtonsTab` renders the stacked recent-sighting cards (which have `.padding(.bottom, 8)` and absolute offsets), the content height can exceed the `maxHeight: .infinity` frame and push the tab bar, or the intrinsic height of the tab bar changes between tabs because the content height influences the VStack layout calculation.

The fix is to isolate `AppTabBar` so its position is pinned to the bottom of the screen and completely immune to tab content height changes.

## Files to Change

- `warnabrotha/warnabrotha/ContentView.swift` — only the authenticated `VStack` layout (lines ~26–57). Do not touch `AppTabBar`, `TabBarItem`, or any tab view files.

## Constraints

- Do not modify `.xcodeproj` / `.pbxproj`
- Do not commit anything to git
- Do not refactor unrelated code — surgical fix only
- Keep `hideTabBar` opacity/hitTesting logic intact (used by MapTab)
- Use only SwiftUI — no UIKit layout overrides
