# Notification Redirect — Full Flow Documentation

This documents every step of the TAPS_SPOTTED notification → parking app redirect chain, all known failure points, and how to diagnose them.

---

## The Intended Flow

```
User reports TAPS
  → Backend sends APNs push
    → User taps notification banner
      → iOS calls didReceive in AppDelegate
        → type == "TAPS_SPOTTED" check passes
          → tryOpenURLs runs after 0.5s delay
            → tries amppark:// → success → AMP Park opens ✓
            → OR tries aimsmobilepay:// → success → AMP Park opens ✓
            → OR falls back to App Store
            → OR falls back to web
```

---

## Step 1 — Backend sends the APNs payload

**File:** `backend/app/services/notification.py` → `_send_apns()`

The APNs message dict is built as:
```python
{
    "aps": {
        "alert": { "title": "...", "body": "..." },
        "sound": "default",
        "badge": N,
    },
    **(data or {}),   # spreads type, parking_lot_id, etc. at TOP LEVEL
}
```

The `data` dict passed in from `notify_parked_users()` is:
```python
{
    "type": "TAPS_SPOTTED",
    "parking_lot_id": <int>,
    "parking_lot_name": <str>,
    "parking_lot_code": <str>,
    "checked_in_count": <int>,
}
```

So the full APNs payload delivered to the device looks like:
```json
{
  "aps": { "alert": {...}, "sound": "default", "badge": 1 },
  "type": "TAPS_SPOTTED",
  "parking_lot_id": 3,
  "parking_lot_name": "Hutchinson",
  "parking_lot_code": "HUTCH",
  "checked_in_count": 2
}
```

### ⚠️ Failure point: backend not deployed
The `**(data or {})` spread fix was made locally. If the backend has not been deployed to GCP (`gcloud app deploy` from `backend/`), the live server still sends the OLD payload:
```python
"data": data or {}   # type is nested under "data", NOT at top level
```
In that case `userInfo["type"]` in iOS is `nil` → the type check fails → the app just opens itself (NOT the App Store). **If the user ends up at the App Store**, the backend fix IS deployed.

---

## Step 2 — iOS receives the tap

**File:** `warnabrotha/warnabrothaApp.swift` → `userNotificationCenter(_:didReceive:)`

```swift
let userInfo = response.notification.request.content.userInfo
print("🔔 Notification tapped — userInfo: \(userInfo)")

if let type = userInfo["type"] as? String, type == "TAPS_SPOTTED" {
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
        self.openParkingPaymentApp()
    }
}
completionHandler()
```

This fires in three states:
- **Foreground** — user sees banner, taps it
- **Background** — app suspended, user taps notification
- **Cold start** — app was killed, user taps notification (0.5s delay helps here)

### ⚠️ Failure point: debug print removed
The `print("🔔 Notification tapped — userInfo: \(userInfo)")` line was added earlier for diagnosis. Check if it's still there. If not, re-add it to confirm:
1. `didReceive` is actually being called
2. What `userInfo` actually contains (confirms backend payload structure)

---

## Step 3 — URL scheme resolution

**File:** `warnabrotha/warnabrothaApp.swift` → `tryOpenURLs()`

```swift
private func tryOpenURLs(_ urls: [URL], fallbackAppStore: String, fallbackWeb: String) {
    guard let url = urls.first else {
        // All schemes exhausted → App Store
        UIApplication.shared.open(appStoreURL) { ... }
        return
    }
    UIApplication.shared.open(url) { success in
        if success { return }
        self.tryOpenURLs(Array(urls.dropFirst()), ...)  // try next
    }
}
```

For AMP Park (default preference), the schemes tried in order are:
1. `amppark://`
2. `aimsmobilepay://`

### ⚠️ Failure point: URL schemes are unverified guesses
`amppark://` and `aimsmobilepay://` were inferred from the app name and developer name. They have **never been confirmed** to be AMP Park's actual registered URL schemes. If neither matches, `open()` returns `false` for both, and the flow falls through to the App Store — which is exactly what is currently happening.

**How to find the real scheme:**
1. Install AMP Park on a physical device
2. Add a breakpoint inside the `open()` completion handlers
3. See which URL returns `success == true`

OR — check AMP Park's Info.plist by extracting their IPA:
1. Download AMP Park from App Store via iTunes (or use iMazing)
2. Extract the `.ipa`, rename to `.zip`, unzip
3. Open `Payload/AMP\ Park.app/Info.plist`
4. Look for `CFBundleURLTypes` → `CFBundleURLSchemes`

The real scheme could be something like:
- `aims://`
- `aimsmobile://`
- `amppark://` (correct, needs verification)
- Entirely different

---

## Step 4 — Info.plist whitelist

**File:** `warnabrotha/Info.plist` → `LSApplicationQueriesSchemes`

```xml
<key>LSApplicationQueriesSchemes</key>
<array>
    <string>amppark</string>
    <string>aimsmobilepay</string>
    <string>honkmobile</string>
</array>
```

This is required for `canOpenURL` (not used anymore) but does **not** affect `UIApplication.shared.open()`. The `open()` call works regardless of this list — it is NOT a failure point for the current implementation.

---

## Step 5 — User preference

**File:** `warnabrotha/warnabrothaApp.swift` → `ParkingPaymentApp.preferred`

```swift
static var preferred: ParkingPaymentApp {
    let raw = UserDefaults.standard.string(forKey: "preferredParkingApp") ?? ""
    return ParkingPaymentApp(rawValue: raw) ?? .ampPark  // defaults to AMP Park
}
```

Unless the user has explicitly set a preference via PreferencesView, this always returns `.ampPark`.

---

## Current Diagnosis

| Step | Status | Evidence |
|---|---|---|
| Backend payload structure | ✅ likely fixed | User goes to App Store (not just opens app), meaning `type` check is passing |
| `didReceive` being called | ✅ likely working | Same as above |
| `type == "TAPS_SPOTTED"` check | ✅ likely passing | Same as above |
| URL schemes `amppark://` / `aimsmobilepay://` | ❌ **likely wrong** | Both `open()` calls return `false` → falls to App Store |

---

## Most Likely Fix

Find AMP Park's actual URL scheme (step 3 above) and update `candidateSchemes` in `warnabrothaApp.swift`:

```swift
case .ampPark: return ["<real_scheme>://"]
```

And add the real scheme (without `://`) to `LSApplicationQueriesSchemes` in `Info.plist`.
