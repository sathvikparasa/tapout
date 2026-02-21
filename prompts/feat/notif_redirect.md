# Magic Feature — iOS: Notification Opens AMP Park App

When a user taps a TAPS Alert push notification, the app should open the **AMP Park** parking payment app. If AMP Park isn't installed, open its App Store page so the user can download it.

**Target app:** AMP Park by EDC Corporation
- App Store ID: `1475971159`
- App Store URL: `https://apps.apple.com/us/app/amp-park/id1475971159`

No backend changes needed.

---

## Files to Modify

| File | Change |
|------|--------|
| `warnabrotha/warnabrotha/Info.plist` | Add `LSApplicationQueriesSchemes` with AMP Park URL scheme candidates |
| `warnabrotha/warnabrotha/warnabrothaApp.swift` | Update `userNotificationCenter(_:didReceive:)` to open AMP Park |

---

## Step 1: Info.plist — Declare URL Schemes to Query

iOS requires apps to declare external URL schemes they want to check via `canOpenURL`. Add `LSApplicationQueriesSchemes` to `Info.plist`.

Add the following key/array to the existing `<dict>`:

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>amppark</string>
    <string>aimsmobilepay</string>
</array>
```

These are candidate URL schemes for AMP Park. If neither works, the fallback (App Store link) always works.

---

## Step 2: warnabrothaApp.swift — Handle Notification Tap

Replace the current no-op `didReceive` handler in `AppDelegate` with AMP Park launch logic.

### Current code (line 39–43):

```swift
func userNotificationCenter(_ center: UNUserNotificationCenter,
                            didReceive response: UNNotificationResponse,
                            withCompletionHandler completionHandler: @escaping () -> Void) {
    completionHandler()
}
```

### Replace with:

```swift
func userNotificationCenter(_ center: UNUserNotificationCenter,
                            didReceive response: UNNotificationResponse,
                            withCompletionHandler completionHandler: @escaping () -> Void) {
    let userInfo = response.notification.request.content.userInfo

    // Only redirect for TAPS_SPOTTED notifications
    if let type = userInfo["type"] as? String, type == "TAPS_SPOTTED" {
        openAMPParkApp()
    }

    completionHandler()
}

private func openAMPParkApp() {
    // Tier 1: Try known URL schemes to open AMP Park directly
    let candidateSchemes = ["amppark://", "aimsmobilepay://"]
    for scheme in candidateSchemes {
        if let url = URL(string: scheme), UIApplication.shared.canOpenURL(url) {
            UIApplication.shared.open(url)
            return
        }
    }

    // Tier 2: Open AMP Park in the App Store
    // itms-apps:// opens directly in App Store app (no Safari redirect)
    if let appStoreURL = URL(string: "itms-apps://itunes.apple.com/app/id1475971159") {
        UIApplication.shared.open(appStoreURL)
        return
    }

    // Tier 3: Web fallback (should never reach here)
    if let webURL = URL(string: "https://apps.apple.com/us/app/amp-park/id1475971159") {
        UIApplication.shared.open(webURL)
    }
}
```

### Logic (3-tier fallback):

1. **AMP Park installed** → open via URL scheme (`amppark://` or `aimsmobilepay://`)
2. **Not installed** → open App Store page via `itms-apps://` (opens App Store app directly)
3. **Web fallback** → open App Store web link in Safari (safety net)

### Important notes:

- The `data` payload from the backend already includes `"type": "TAPS_SPOTTED"` — check this field so only TAPS alerts redirect (not checkout reminders, etc.)
- `canOpenURL` requires the scheme to be declared in `LSApplicationQueriesSchemes` (Step 1)
- `itms-apps://` does NOT require `LSApplicationQueriesSchemes` — it always works on iOS
- The `openAMPParkApp()` method should be `private` on `AppDelegate`

---

## Verification

1. Build in Xcode — no compile errors
2. Test with AMP Park **installed**: tap TAPS notification → AMP Park opens
3. Test with AMP Park **not installed**: tap TAPS notification → App Store page opens
4. Test non-TAPS notification (e.g. checkout reminder): tap → normal app behavior (no redirect)
