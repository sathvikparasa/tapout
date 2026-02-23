# Fix: Notification Tap Always Opens App Store Instead of Installed App

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

---

## Bug

Tapping a TAPS_SPOTTED notification always opens the App Store, even when the preferred parking app (AMP Park or Honk Mobile) is already installed. The App Store is supposed to be a fallback only.

---

## Root Cause

In `warnabrothaApp.swift`, `openParkingPaymentApp()` uses `canOpenURL` to check if the app is installed before calling `open()`:

```swift
if let url = URL(string: scheme), UIApplication.shared.canOpenURL(url) {
    UIApplication.shared.open(url)
    return
}
```

`canOpenURL` is unreliable when called during notification handling — it returns `false` for installed apps if `UIApplication` isn't fully active yet (e.g., cold start or background-to-foreground transition). Since it always returns `false`, the code falls through directly to the App Store tier.

---

## Fix

**`warnabrotha/warnabrotha/warnabrothaApp.swift`**

Replace the synchronous `canOpenURL` → `open` pattern with a recursive async attempt using `open(_:completionHandler:)`, which reliably returns `false` in its completion block if the URL truly can't be opened. Also re-add the 0.5s delay to ensure `UIApplication` is ready after a cold start.

Replace `didReceive` and `openParkingPaymentApp()` with:

```swift
// Handle notification tap
func userNotificationCenter(_ center: UNUserNotificationCenter,
                            didReceive response: UNNotificationResponse,
                            withCompletionHandler completionHandler: @escaping () -> Void) {
    let userInfo = response.notification.request.content.userInfo

    if let type = userInfo["type"] as? String, type == "TAPS_SPOTTED" {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.openParkingPaymentApp()
        }
    }

    completionHandler()
}

private func openParkingPaymentApp() {
    let app = ParkingPaymentApp.preferred
    let schemes = app.candidateSchemes.compactMap { URL(string: $0) }
    tryOpenURLs(schemes, fallbackAppStore: app.appStoreURL, fallbackWeb: app.webURL)
}

private func tryOpenURLs(_ urls: [URL], fallbackAppStore: String, fallbackWeb: String) {
    guard let url = urls.first else {
        // All schemes failed — try App Store
        if let appStoreURL = URL(string: fallbackAppStore) {
            UIApplication.shared.open(appStoreURL) { success in
                if !success, let webURL = URL(string: fallbackWeb) {
                    UIApplication.shared.open(webURL)
                }
            }
        }
        return
    }

    UIApplication.shared.open(url) { success in
        if success {
            return
        }
        // This scheme failed — try the next one
        self.tryOpenURLs(Array(urls.dropFirst()), fallbackAppStore: fallbackAppStore, fallbackWeb: fallbackWeb)
    }
}
```

---

## Rules

- Only modify `warnabrothaApp.swift`. No other files need changes.
- Do not commit to git without permission.
