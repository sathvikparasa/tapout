# Goal: Fix Feed Item Time Formatting & Vote Display

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Objective

Fix two bugs in how feed items are displayed across the iOS app.

---

## Operational Rules

- **Use the existing TapOut theme** defined in `warnabrotha/warnabrotha/Theme/Win95Theme.swift` (renamed to TapOutTheme). Use `AppColors`, `.appFont()`, `.displayFont()`, `.cardStyle()`, `PrimaryButton`, `LiveBadge`, etc.
- **Follow the existing MVVM pattern.** All new state goes in `AppViewModel` as `@Published` properties. Do not create new ViewModel classes.
- **Keep it native SwiftUI.** Use only Apple frameworks.
- **Do not modify `.xcodeproj` or `.pbxproj` files.**
- Do not commit anything to git without prior permission.
- Ask questions if you are confused.
- I will build and run the app.

---

## Key Files

| File | Purpose |
|------|---------|
| `warnabrotha/warnabrotha/Views/ProbabilityTab.swift` | Feed tab — contains `FeedCardView` (the main feed card used in the feed list) |
| `warnabrotha/warnabrotha/Views/ButtonsTab.swift` | Home/Dashboard tab — contains the "Recent Activity" stacked card that shows the most recent sighting |
| `warnabrotha/warnabrotha/Models/APIModels.swift` | `FeedSighting` model — has `upvotes: Int`, `downvotes: Int`, `netScore: Int`, `minutesAgo: Int` |

---

## Bug 1: Time Formatting

### Problem

Time-ago text is inconsistent and poorly formatted in two places:

1. **`ButtonsTab.swift` line ~300** — The "Recent Activity" stacked card displays time as raw `"\(sighting.minutesAgo)m ago"` (e.g. `"47m ago"`). This is terse and doesn't handle hours.

2. **`ProbabilityTab.swift` lines ~219-226** — The `FeedCardView.timeText` computed property handles minutes vs hours but doesn't match the desired format (e.g. it shows `"1 hour ago"` instead of `"1h 0m ago"`, and `"47 mins ago"` instead of `"47 minutes ago"`).

### Fix

Create a **single shared helper** (either a static function or an extension on `Int`) that converts `minutesAgo: Int` to a human-readable string. Use this logic (ported from the backend's Python implementation):

```
Input: minutesAgo (Int)

- If minutesAgo <= 1  →  "just now"
- If minutesAgo < 60  →  "{minutesAgo} minutes ago"
- Else:
    - hours = minutesAgo / 60
    - remainingMinutes = minutesAgo % 60
    - If remainingMinutes > 0  →  "{hours}h {remainingMinutes}m ago"
    - Else  →  "{hours} hour(s) ago"  (pluralize correctly)
```

Then replace:
- `ButtonsTab.swift` line ~300: Replace `"\(sighting.minutesAgo)m ago"` with a call to the shared helper.
- `ProbabilityTab.swift` `FeedCardView.timeText`: Replace the existing logic with a call to the shared helper.

---

## Bug 2: Vote Display — Show Separate Upvote/Downvote Counts

### Problem

The `FeedCardView` vote section (in `ProbabilityTab.swift` lines ~184-207) currently shows:

```
[thumbsup]  {netScore}  [thumbsdown]
```

This displays a single aggregate `netScore` number between the two vote buttons. The user wants to see individual counts instead.

### Fix

Change the vote section layout from the current single-number display to show **separate counts next to each button**:

```
[thumbsup] {upvotes}    {downvotes} [thumbsdown]
```

Specifically:
- Show `sighting.upvotes` count **next to the upvote button**, colored `AppColors.accent` (sage green — the same color the upvote icon uses when active).
- Show `sighting.downvotes` count **next to the downvote button**, colored `AppColors.danger` (red — the same color the downvote icon uses when active).
- Remove the single `netScore` text that currently sits between the two buttons.
- Keep the existing vote toggle behavior (tapping calls `onVote`).

---

## Files to Modify

| File | Changes |
|------|---------|
| `warnabrotha/warnabrotha/Views/ProbabilityTab.swift` | Update `FeedCardView` vote section to show separate counts; update `timeText` to use shared helper |
| `warnabrotha/warnabrotha/Views/ButtonsTab.swift` | Update "Recent Activity" card time text to use shared helper |

You may place the shared time formatting helper wherever makes sense (e.g. an extension on `Int` in the theme file, or a private helper in `ProbabilityTab.swift` — use your judgment).
