# Feature: iOS Push Notifications (APNs)

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Objective

Enable iOS push notifications so that when a user reports a TAPS sighting, all users with an active parking session at that lot receive a system push notification via Apple Push Notification service (APNs). The **backend already fully supports APNs** via `aioapns` — this is a **client-side only** implementation.

---

## Operational Rules

- **Supabase MCP is available.** If you need to inspect the live database schema (e.g. verify `devices` table columns or `notifications` table structure), use the Supabase MCP tool. This is optional — use it if you're unsure about column names or types.
- **Do not modify any backend files.** The backend APNs integration (`backend/app/services/notification.py`) is complete and working. The `PATCH /auth/me` endpoint already accepts `push_token` and `is_push_enabled`.
- **Do not create a new ViewModel.** All notification state belongs in the existing `AppViewModel`. The app uses a single-ViewModel architecture.
- **Do not modify existing views unless specified.** The only view changes are adding a notification permission prompt after email verification.
- **Entitlements and Xcode capabilities are manual steps.** Flag them clearly — do not attempt to modify `.xcodeproj` or `.pbxproj` files directly.
- **Keep the existing `KeychainService` pattern.** Push token storage goes in `KeychainService`, not a new service.

---

## Current Architecture Snapshot

### What the Backend Already Does

When `POST /sightings` is called, the backend:
1. Creates a `TapsSighting` record
2. Calls `NotificationService.notify_parked_users(db, lot_id, lot_name, lot_code)`
3. For each device with an active session at that lot:
   - Creates an in-app `Notification` DB record (always, for polling fallback)
   - If `device.is_push_enabled == True` and `device.push_token` is not null:
     - Detects token format (APNs = 64 hex chars, FCM = longer with colons)
     - Sends APNs push via `aioapns` with this payload:
       ```json
       {
         "aps": {
           "alert": { "title": "TAPS Alert!", "body": "TAPS spotted at {lot_name}..." },
           "sound": "default",
           "badge": 1
         },
         "data": {
           "type": "taps_spotted",
           "parking_lot_id": 1,
           "parking_lot_name": "Hutchison",
           "parking_lot_code": "HUTCH"
         }
       }
       ```

### Backend Endpoints Used by This Feature

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `PATCH` | `/auth/me` | Send push token to backend. Body: `{"push_token": "hex...", "is_push_enabled": true}` |
| `GET` | `/notifications/unread` | Polling fallback — returns `NotificationList` with `unreadCount` |
| `POST` | `/notifications/read` | Mark notifications as read. Body: `{"notification_ids": [1, 2]}` |

### iOS App Files (Current State)

| File | Relevant State |
|------|---------------|
| `warnabrotha/warnabrothaApp.swift` | Simple `@main App` struct. No `AppDelegate`. No push registration. |
| `warnabrotha/Services/KeychainService.swift` | Stores auth token and device UUID. No push token storage. |
| `warnabrotha/Services/APIClient.swift` | Has `getUnreadNotifications()` and `markNotificationsRead()`. No `updateDevice()` method for PATCH /auth/me. |
| `warnabrotha/ViewModels/AppViewModel.swift` | No notification permission state. No push token handling. No unread count. |
| `warnabrotha/Models/APIModels.swift` | `NotificationItem`, `NotificationList`, `MarkReadRequest` already defined. `DeviceRegistration` has `pushToken` field (always nil). Missing `DeviceUpdate` model. |
| `warnabrotha/ContentView.swift` | No notification permission prompt. |
| `warnabrotha/Info.plist` | Only has font config. No background modes. |

---

## Implementation Plan

### Phase 1: AppDelegate for Push Token Registration

**Create push notification handling in `warnabrothaApp.swift`.**

The SwiftUI app needs a `UIApplicationDelegate` to receive APNs token callbacks. Use `@UIApplicationDelegateAdaptor`.

**Add to `warnabrothaApp.swift`:**

```swift
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        Task {
            await PushNotificationService.shared.sendTokenToBackend(token)
        }
    }

    func application(_ application: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("APNs registration failed: \(error.localizedDescription)")
    }

    // Show notifications even when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .badge])
    }

    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        completionHandler()
    }
}
```

**Update the `@main` App struct:**
```swift
@main
struct warnabrothaApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    // ... existing body
}
```

### Phase 2: Push Notification Service

**Create `warnabrotha/Services/PushNotificationService.swift`.**

This is a lightweight singleton that coordinates permission requests, token storage, and backend sync. Keep it minimal.

```swift
import UIKit
import UserNotifications

@MainActor
class PushNotificationService {
    static let shared = PushNotificationService()

    func requestPermissionAndRegister() async -> Bool {
        let center = UNUserNotificationCenter.current()
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            if granted {
                UIApplication.shared.registerForRemoteNotifications()
            }
            return granted
        } catch {
            print("Notification permission error: \(error)")
            return false
        }
    }

    func sendTokenToBackend(_ token: String) async {
        KeychainService.savePushToken(token)
        do {
            try await APIClient.shared.updateDevice(pushToken: token, isPushEnabled: true)
        } catch {
            print("Failed to send push token to backend: \(error)")
        }
    }
}
```

### Phase 3: KeychainService Update

**Add push token storage to `KeychainService.swift`:**

```swift
// Add these methods alongside existing token methods:
static func savePushToken(_ token: String) { /* save to keychain with key "push_token" */ }
static func getPushToken() -> String? { /* retrieve from keychain */ }
```

Use the same Keychain pattern as `saveToken()`/`getToken()` with a new key `"push_token"`.

### Phase 4: APIClient Update

**Add `updateDevice()` to `APIClient.swift`:**

```swift
func updateDevice(pushToken: String, isPushEnabled: Bool) async throws {
    // PATCH /auth/me with body: {"push_token": pushToken, "is_push_enabled": isPushEnabled}
}
```

**Add the request model to `APIModels.swift`:**

```swift
struct DeviceUpdate: Codable {
    let pushToken: String?
    let isPushEnabled: Bool?

    enum CodingKeys: String, CodingKey {
        case pushToken = "push_token"
        case isPushEnabled = "is_push_enabled"
    }
}
```

Follow the existing `APIClient` patterns for authenticated PATCH requests with Bearer token.

### Phase 5: AppViewModel Updates

**Add to `AppViewModel`:**

1. New published properties:
   ```swift
   @Published var notificationPermissionGranted: Bool = false
   @Published var unreadNotificationCount: Int = 0
   ```

2. New methods:
   - `requestNotificationPermission()` — calls `PushNotificationService.shared.requestPermissionAndRegister()`, updates `notificationPermissionGranted`
   - `fetchUnreadNotificationCount()` — calls `GET /notifications/unread`, updates `unreadNotificationCount`

3. Call `fetchUnreadNotificationCount()` inside `loadInitialData()` and `refresh()`.

4. After `register()` succeeds and email is verified, call `requestNotificationPermission()`.

### Phase 6: Trigger Permission Prompt

Request notification permission **after email verification succeeds**. In `AppViewModel.verifyEmail()`, after a successful verification response, call `requestNotificationPermission()`. This ensures the user has committed to the app before being prompted.

Do NOT add a separate UI view for the permission — iOS shows a system dialog automatically when `requestAuthorization` is called.

---

## Manual Steps (Cannot Be Automated)

These must be done in Xcode by the developer:

1. **Enable Push Notifications capability:**
   - Xcode → Target → Signing & Capabilities → + Capability → Push Notifications
   - This creates the `.entitlements` file automatically

2. **Enable Background Modes → Remote notifications:**
   - Xcode → Target → Signing & Capabilities → + Capability → Background Modes → check "Remote notifications"

3. **Apple Developer Portal:**
   - Ensure the App ID has Push Notifications enabled
   - Generate an APNs Auth Key (`.p8` file) if not already done
   - Configure backend env vars: `APNS_KEY_ID`, `APNS_TEAM_ID`, `APNS_KEY_PATH`, `APNS_BUNDLE_ID`

---

## Files to Create

| File | Purpose |
|------|---------|
| `warnabrotha/Services/PushNotificationService.swift` | Singleton coordinating permission, registration, and backend token sync |

## Files to Modify

| File | Changes |
|------|---------|
| `warnabrotha/warnabrothaApp.swift` | Add `AppDelegate` class with APNs callbacks + `UNUserNotificationCenterDelegate`. Add `@UIApplicationDelegateAdaptor`. |
| `warnabrotha/Services/KeychainService.swift` | Add `savePushToken()` and `getPushToken()` methods |
| `warnabrotha/Services/APIClient.swift` | Add `updateDevice(pushToken:isPushEnabled:)` method (PATCH /auth/me) |
| `warnabrotha/Models/APIModels.swift` | Add `DeviceUpdate` struct |
| `warnabrotha/ViewModels/AppViewModel.swift` | Add `notificationPermissionGranted`, `unreadNotificationCount` properties. Add `requestNotificationPermission()`, `fetchUnreadNotificationCount()`. Call permission request after email verification. |

---

## Verification

After implementation, the end-to-end flow should be:

1. User opens app → registers → verifies email
2. iOS system dialog: "WarnABrotha Would Like to Send You Notifications" → user taps Allow
3. `didRegisterForRemoteNotificationsWithDeviceToken` fires → hex token sent to backend via `PATCH /auth/me`
4. User checks into lot "HUTCH"
5. Another user reports TAPS at "HUTCH" → `POST /sightings`
6. Backend calls `notify_parked_users()` → detects APNs token → sends push via `aioapns`
7. User's phone shows banner: "TAPS Alert! TAPS spotted at Hutchison Parking Structure..."
8. If push fails or is denied, `GET /notifications/unread` polling still works as fallback
