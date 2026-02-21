# Goal: Fix Tab Bar Jumping on Home Tab

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

---

## Bug Description

The tab bar physically moves down when the user taps the Home tab, and back up when they leave it. All other tabs are stable. The tab bar should always stay pinned to the bottom of the screen regardless of which tab is selected.

---

## Root Cause

In `ContentView.swift`, the tab bar is conditionally included/excluded from the layout:

```swift
if !hideTabBar {
    AppTabBar(...)
}
```

`hideTabBar` is a `@State` owned by `ContentView` and passed as a `@Binding` to `MapTab`, which sets it to `true` when the search field is focused. When `hideTabBar` is `true`, `AppTabBar` is **removed from the VStack entirely**, which collapses the space it occupied and shifts the content above it. When it re-appears, the layout shifts back. This causes visible jumping.

Additionally, `hideTabBar` is never reset to `false` when the user switches away from the Map tab — so any residual `true` state carries over and the tab bar stays hidden on Home.

---

## Fix

**`warnabrotha/warnabrotha/ContentView.swift`**

Instead of conditionally inserting/removing `AppTabBar` from the layout, always render it but use `.opacity` and `.allowsHitTesting` to hide it when needed. This keeps the layout stable:

```swift
// Replace:
if !hideTabBar {
    AppTabBar(
        selectedTab: $selectedTab,
        feedBadgeCount: viewModel.unreadNotificationCount
    )
}

// With:
AppTabBar(
    selectedTab: $selectedTab,
    feedBadgeCount: viewModel.unreadNotificationCount
)
.opacity(hideTabBar ? 0 : 1)
.allowsHitTesting(!hideTabBar)
```

Also reset `hideTabBar` to `false` inside the existing `.onChange(of: selectedTab)` when switching away from the Map tab (tab 3):

```swift
.onChange(of: selectedTab) { _, tab in
    if tab == 1 {
        Task { await viewModel.markAllNotificationsRead() }
    }
    if tab != 3 {
        hideTabBar = false
    }
}
```

---

## Rules

- Only modify `ContentView.swift`. Do not touch `MapTab.swift` or `ButtonsTab.swift`.
- Do not commit to git without permission.
