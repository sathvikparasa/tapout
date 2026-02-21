# Goal: Remove Notification Badge from Gear Icon

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

---

## Bug Description

The gear/settings icon in the top-right of the Home tab (`ButtonsTab.swift`) still shows a red notification badge dot. This badge was left over from when the button was a profile/notification icon. Now that it's a settings icon, the badge makes no sense and should be removed.

---

## Fix

**`warnabrotha/warnabrotha/Views/ButtonsTab.swift`** — around line 146.

The gear button label currently wraps the icon in a `ZStack` solely to show the badge dot. Since the badge is being removed, simplify the label to just the icon:

```swift
// Replace:
} label: {
    ZStack(alignment: .topTrailing) {
        Image(systemName: "gearshape.fill")
            .font(.system(size: 22))
            .foregroundColor(AppColors.textPrimary)

        if viewModel.unreadNotificationCount > 0 {
            Circle()
                .fill(AppColors.dangerBright)
                .frame(width: 10, height: 10)
                .offset(x: 2, y: -2)
        }
    }
}

// With:
} label: {
    Image(systemName: "gearshape.fill")
        .font(.system(size: 22))
        .foregroundColor(AppColors.textPrimary)
}
```

---

## Rules

- Only modify the gear button label in `ButtonsTab.swift`. No other changes.
- Do not commit to git without permission.
