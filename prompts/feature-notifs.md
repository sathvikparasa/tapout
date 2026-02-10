# Feature: Push Notifications via Firebase Cloud Messaging (Android)

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

## Objective

When a user taps the **"REPORT TAPS"** button for a parking lot, all users with an **active parking session** (checked in, not checked out) at that lot should receive a **push notification** on their Android device via Firebase Cloud Messaging (FCM). This integrates with the existing backend notification system that currently only supports APNs (iOS).

---

## Operational Rules (Feature-Specific)

- **Do not remove existing APNs logic.** The backend currently sends iOS push notifications via `aioapns`. FCM must be added *alongside* it, not as a replacement.
- **Do not create a new ViewModel.** Notification state must be added to the existing `AppUiState` data class and managed by `AppViewModel`. The app uses a single-ViewModel architecture.
- **Do not use XML layouts.** All new UI (permission dialogs, notification badges, etc.) must be Jetpack Compose.
- **Preserve AndroidManifest.xml contents.** When adding the FCM service and permissions, do not remove or alter existing entries (the `<activity>`, Google Maps `<meta-data>`, existing permissions).
- **Do not modify database schema without confirmation.** If adding a `platform` column to the `devices` table, flag it — this requires a Supabase migration.
- **Manual steps exist.** Firebase project creation, `google-services.json` download, and Firebase service account key generation are manual. Do not attempt to automate these — just clearly indicate where they are needed and what values are expected.

---

## Current Architecture Snapshot

### Backend (FastAPI on Google App Engine)

**Framework:** FastAPI 0.109.0, Python 3.12, deployed on GAE via `app.yaml`
**Database:** PostgreSQL via Supabase, SQLAlchemy async ORM (`asyncpg`)
**Auth:** Device-based JWT (no user accounts, just device UUIDs)

**Existing notification flow (defined in `backend/app/services/notification.py`):**
1. User calls `POST /api/v1/sightings` (handler in `backend/app/api/sightings.py`)
2. Handler calls `NotificationService.notify_parked_users(db, parking_lot_id, parking_lot_name)`
3. `notify_parked_users()` queries all `ParkingSession` rows where `parking_lot_id` matches AND `checked_out_at IS NULL`, eager-loading the related `Device`
4. For each device: creates a `Notification` DB record (always), then attempts APNs push if `device.is_push_enabled and device.push_token`
5. APNs push uses `aioapns` with this payload shape:
```json
{
  "aps": {
    "alert": { "title": "...", "body": "..." },
    "sound": "default",
    "badge": 1
  },
  "data": {
    "type": "taps_spotted",
    "parking_lot_id": 1
  }
}
```
6. Returns `users_notified` count back to the sightings handler

**Relevant backend files:**
| File | What it contains |
|------|-----------------|
| `backend/app/models/device.py` | `Device` model: `id`, `device_id` (UUID string), `email_verified`, `push_token` (String, nullable), `is_push_enabled` (Boolean, default False) |
| `backend/app/models/notification.py` | `Notification` model with `NotificationType` enum: `TAPS_SPOTTED`, `CHECKOUT_REMINDER` |
| `backend/app/models/parking_session.py` | `ParkingSession` model: active when `checked_out_at IS NULL` |
| `backend/app/services/notification.py` | `NotificationService` class with `send_push_notification()`, `notify_parked_users()`, `send_checkout_reminder()` |
| `backend/app/services/reminder.py` | Background scheduler (APScheduler, 5-min interval) for checkout reminders |
| `backend/app/config.py` | `Settings(BaseSettings)` — has `apns_*` fields, no Firebase fields yet |
| `backend/app/api/sightings.py` | `POST /sightings` handler that triggers notifications |
| `backend/app/api/auth.py` | `POST /register`, `PATCH /me` (updates `push_token`, `is_push_enabled`) |
| `backend/requirements.txt` | Uses `aioapns==3.1` — no `firebase-admin` |

### Android App (Kotlin / Jetpack Compose)

**Architecture:** MVVM, single `AppViewModel`, Hilt DI, 100% Compose, Material 3
**Networking:** Retrofit 2.11.0 + OkHttp 4.12.0 + Gson
**Build:** `compileSdk` 35, `minSdk` 26, `targetSdk` 35, Kotlin 2.0.21

**Current `AppUiState` (in `ui/viewmodel/AppViewModel.kt`):**
```kotlin
data class AppUiState(
    val isAuthenticated: Boolean = false,
    val isEmailVerified: Boolean = false,
    val showEmailVerification: Boolean = false,
    val parkingLots: List<ParkingLot> = emptyList(),
    val lotStats: Map<Int, ParkingLotWithStats> = emptyMap(),
    val selectedLot: ParkingLotWithStats? = null,
    val selectedLotId: Int? = null,
    val currentSession: ParkingSession? = null,
    val feed: FeedResponse? = null,
    val allFeedSightings: List<FeedSighting> = emptyList(),
    val allFeedsTotalCount: Int = 0,
    val feedFilterLotId: Int? = null,
    val totalRegisteredDevices: Int = 0,
    val prediction: PredictionResponse? = null,
    val displayedProbability: Double = 0.0,
    val isLoading: Boolean = false,
    val error: String? = null,
    val successMessage: String? = null
)
```

**Current `TokenRepository` (in `data/repository/TokenRepository.kt`):**
- Uses `EncryptedSharedPreferences` (AES256_GCM)
- Keys: `KEY_TOKEN = "auth_token"`, `KEY_DEVICE_ID = "device_id"`
- Methods: `saveToken()`, `getToken()`, `clearToken()`, `getOrCreateDeviceId()`, `hasToken()`
- **No push token storage exists yet**

**Current `DeviceRegistration` model (in `data/model/ApiModels.kt`):**
```kotlin
data class DeviceRegistration(
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("push_token") val pushToken: String? = null  // Always null today
)
```

**Current notification models (already defined in `ApiModels.kt`):**
```kotlin
data class NotificationItem(
    val id: Int,
    @SerializedName("notification_type") val notificationType: String,
    val title: String,
    val message: String,
    @SerializedName("parking_lot_id") val parkingLotId: Int?,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("read_at") val readAt: String?,
    @SerializedName("is_read") val isRead: Boolean
)

data class NotificationList(
    val notifications: List<NotificationItem>,
    @SerializedName("unread_count") val unreadCount: Int,
    val total: Int
)

data class MarkReadRequest(
    @SerializedName("notification_ids") val notificationIds: List<Int>
)
```

**Current `ApiService.kt` notification endpoints (already defined):**
```kotlin
@GET("notifications/unread")
suspend fun getUnreadNotifications(): Response<NotificationList>

@POST("notifications/read")
suspend fun markNotificationsRead(@Body request: MarkReadRequest): Response<Map<String, Any>>
```

**Current `AndroidManifest.xml`:**
```xml
<manifest>
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:name=".WarnABrothaApp"
        ...
        android:usesCleartextTraffic="true"
        tools:targetApi="31">
        <meta-data
            android:name="com.google.android.geo.API_KEY"
            android:value="${MAPS_API_KEY}" />
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

**Current `WarnABrothaApp.kt`:**
```kotlin
@HiltAndroidApp
class WarnABrothaApp : Application()
```

**Firebase status: NOT CONFIGURED.** No `google-services.json`, no Firebase dependencies, no `FirebaseMessagingService`, no notification channels.

---

## ViewModel State Requirements

Add the following fields to the existing `AppUiState` data class. **Do not create a separate ViewModel.**

```kotlin
data class AppUiState(
    // ... all existing fields remain unchanged ...

    // New notification fields:
    val pushToken: String? = null,                    // Current FCM token (null = not yet obtained)
    val notificationPermissionGranted: Boolean = false, // POST_NOTIFICATIONS permission status
    val unreadNotificationCount: Int = 0              // From GET /notifications/unread API
)
```

The `AppViewModel` must expose new functions:
- `fun requestNotificationPermission()` — triggers the Android 13+ permission request
- `fun fetchUnreadNotificationCount()` — calls `GET /notifications/unread` and updates `unreadNotificationCount`
- `fun updatePushToken(token: String)` — saves token locally + calls `PATCH /auth/me` to sync with backend
- `fun onNotificationPermissionResult(granted: Boolean)` — updates state and, if granted, fetches FCM token

---

## FCM Payload Contract

### TAPS Alert (sent by `notify_parked_users()`)

The backend must send this exact structure via `firebase_admin.messaging`:

```json
{
  "token": "<device FCM token>",
  "notification": {
    "title": "TAPS Alert!",
    "body": "TAPS has been spotted at Hutchison Parking Structure. Move your vehicle!"
  },
  "data": {
    "type": "TAPS_SPOTTED",
    "parking_lot_id": "1",
    "parking_lot_name": "Hutchison Parking Structure",
    "parking_lot_code": "HUTCH"
  },
  "android": {
    "priority": "high",
    "notification": {
      "channel_id": "taps_alerts",
      "sound": "default"
    }
  }
}
```

### Checkout Reminder (sent by `send_checkout_reminder()`)

```json
{
  "token": "<device FCM token>",
  "notification": {
    "title": "Still parked?",
    "body": "You've been parked at Hutchison Parking Structure for 3 hours. Don't forget to check out when you leave!"
  },
  "data": {
    "type": "CHECKOUT_REMINDER",
    "parking_lot_id": "1",
    "session_id": "42"
  },
  "android": {
    "priority": "high",
    "notification": {
      "channel_id": "taps_alerts",
      "sound": "default"
    }
  }
}
```

**Important:** All `data` values must be strings (FCM requirement). The `parking_lot_id` is `"1"`, not `1`.

### Android Parsing Contract

In `FCMService.onMessageReceived()`, extract data as:
```kotlin
val type = remoteMessage.data["type"]           // "TAPS_SPOTTED" or "CHECKOUT_REMINDER"
val lotId = remoteMessage.data["parking_lot_id"] // String, parse to Int if needed
val lotName = remoteMessage.data["parking_lot_name"] // Nullable for CHECKOUT_REMINDER
```

Display the `remoteMessage.notification?.title` and `remoteMessage.notification?.body` directly — do not reconstruct them from data fields.

---

## Implementation Notes & Gotchas

### Android 13+ Notification Permission
- `POST_NOTIFICATIONS` is a **runtime permission** starting from API 33 (Android 13).
- You **must** call `ActivityCompat.requestPermissions()` or use the Compose `rememberLauncherForActivityResult(RequestPermission)` pattern.
- If the user denies the permission, FCM tokens still work — messages arrive but are **silently dropped** by the OS. The app should still function normally via in-app polling.
- On API < 33, the permission is auto-granted. Check `Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU` before requesting.

### Emulator & Testing
- **Google Play Services is required** on the emulator to receive FCM messages. Use a "Google APIs" system image, not a plain AOSP image.
- If Play Services is missing, `FirebaseMessaging.getInstance().token` will fail. Wrap it in a try-catch and log the failure — don't crash.
- For local testing without FCM, the in-app `GET /notifications/unread` polling fallback still works.

### Token Lifecycle
- FCM tokens can **rotate at any time** (app reinstall, cache clear, Firebase-side rotation). The `onNewToken()` callback in `FCMService` handles this.
- `onNewToken()` fires **outside** the Hilt dependency graph since `FirebaseMessagingService` is instantiated by the system, not Hilt. Use `EntryPointAccessors.fromApplication()` to access `TokenRepository` and `ApiService` from within the service.
- Always call `PATCH /auth/me` with the fresh token when `onNewToken()` fires.

### Backend Platform Detection
- The `Device` model currently has no `platform` field. Rather than adding a DB column (which requires a Supabase migration), detect the platform by the push token format:
  - **APNs tokens:** 64 hex characters (e.g., `a1b2c3d4...`)
  - **FCM tokens:** Much longer, contain colons and alphanumeric characters (e.g., `bk3RNwTe3H0:CI2k_HHw...`)
- Add a helper function `is_fcm_token(token: str) -> bool` to `NotificationService`.
- **If a DB migration is acceptable**, a `platform` column is cleaner. Confirm with me before going that route.

### Notification Channel
- Android 8+ (API 26+) requires notification channels. Since `minSdk` is 26, this is **always required**.
- Create the channel in `WarnABrothaApp.onCreate()`, not in the service — channels should exist before any notification arrives.
- Channel ID: `"taps_alerts"`, Name: `"TAPS Alerts"`, Importance: `HIGH` (enables heads-up display).

---

## Implementation Plan

### Phase 1: Firebase Project Setup (Manual)

1. Create Firebase project in Firebase Console
2. Register the Android app with package name `com.warnabrotha.app`
3. Download `google-services.json` into `android/app/`
4. Generate a Firebase Admin SDK service account key JSON for the backend

### Phase 2: Android — Dependencies & Gradle

**`android/build.gradle.kts` (root):** Add Google Services plugin:
```kotlin
plugins {
    // existing plugins...
    id("com.google.gms.google-services") version "4.4.2" apply false
}
```

**`android/app/build.gradle.kts`:** Add Firebase BOM + FCM:
```kotlin
plugins {
    // existing plugins...
    id("com.google.gms.google-services")
}

dependencies {
    // existing deps...
    implementation(platform("com.google.firebase:firebase-bom:33.7.0"))
    implementation("com.google.firebase:firebase-messaging-ktx")
}
```

### Phase 3: Android — FCM Service & Notification Channel

1. **Create `data/service/FCMService.kt`:**
   - Extends `FirebaseMessagingService`
   - `onNewToken(token)`: save to `TokenRepository`, call `PATCH /auth/me`
   - `onMessageReceived(message)`: build and show system notification using the payload contract above
   - Use `EntryPointAccessors.fromApplication()` for Hilt access (since system instantiates the service)

2. **Update `WarnABrothaApp.kt`:**
   - Create `"taps_alerts"` notification channel in `onCreate()`

3. **Update `AndroidManifest.xml`** (append, don't remove existing):
   ```xml
   <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

   <service android:name=".data.service.FCMService" android:exported="false">
       <intent-filter>
           <action android:name="com.google.firebase.MESSAGING_EVENT" />
       </intent-filter>
   </service>
   ```

### Phase 4: Android — Token Management & Permission

1. **Update `TokenRepository`:**
   - Add `KEY_PUSH_TOKEN = "push_token"`
   - Add `savePushToken(token: String)` and `getPushToken(): String?`

2. **Update `AppViewModel`:**
   - Add new `AppUiState` fields (see ViewModel State Requirements above)
   - In `register()`: after successful registration, fetch FCM token via `FirebaseMessaging.getInstance().token.await()`, then call `PATCH /auth/me` with the token
   - Add `fetchUnreadNotificationCount()`: call `GET /notifications/unread`, update `unreadNotificationCount` in state
   - Call `fetchUnreadNotificationCount()` during `loadInitialData()` and `refresh()`

3. **Update `MainActivity.kt`:**
   - Request `POST_NOTIFICATIONS` permission after email verification succeeds (before entering `MainScreen`)
   - Use `rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission())` pattern
   - On granted: call `viewModel.onNotificationPermissionResult(true)` which triggers FCM token fetch
   - On denied: proceed normally — polling fallback still works

### Phase 5: Backend — Firebase Admin SDK

1. **Add to `requirements.txt`:**
   ```
   firebase-admin==6.4.0
   ```

2. **Update `app/config.py`** — add to `Settings`:
   ```python
   # Firebase Cloud Messaging
   firebase_credentials_json: Optional[str] = None  # JSON string of service account key
   ```

3. **Update `app/main.py`** — initialize Firebase in lifespan startup:
   ```python
   import firebase_admin
   from firebase_admin import credentials
   import json

   if settings.firebase_credentials_json:
       cred = credentials.Certificate(json.loads(settings.firebase_credentials_json))
       firebase_admin.initialize_app(cred)
   ```

4. **Update `app/services/notification.py`** — add FCM alongside APNs in `send_push_notification()`:
   ```python
   @classmethod
   async def send_push_notification(cls, push_token, title, body, data=None):
       if cls._is_fcm_token(push_token):
           return await cls._send_fcm(push_token, title, body, data)
       else:
           return await cls._send_apns(push_token, title, body, data)
   ```
   - Extract current APNs logic into `_send_apns()`
   - Add `_send_fcm()` using `firebase_admin.messaging.send()`
   - Add `_is_fcm_token()` helper (checks token length / format)
   - Handle `messaging.UnregisteredError` — set `device.push_token = None` for stale tokens

5. **Update `app.yaml`** — add env var:
   ```yaml
   env_variables:
     FIREBASE_CREDENTIALS_JSON: '{ ... service account JSON ... }'
   ```

### Phase 6: Verification

**End-to-end flow after implementation:**

1. User A opens app → registers → grants notification permission → FCM token sent to backend via `PATCH /auth/me`
2. User A checks into lot "HUTCH" via `POST /sessions/checkin`
3. User B taps "REPORT TAPS" at "HUTCH" → `POST /sightings`
4. Backend `notify_parked_users()` finds User A, creates DB notification, detects FCM token, sends via Firebase Admin SDK
5. User A's phone shows heads-up notification: "TAPS Alert! TAPS has been spotted at Hutchison Parking Structure..."
6. User A taps notification → app opens
7. `NotificationBadge` shows correct unread count from `GET /notifications/unread`

---

## Files to Create

| File | Purpose |
|------|---------|
| `android/app/src/main/java/com/warnabrotha/app/data/service/FCMService.kt` | Firebase Messaging Service — handles `onNewToken` and `onMessageReceived` |
| `android/app/google-services.json` | **Manual** — Firebase project config downloaded from console |
| Backend Firebase service account JSON | **Manual** — downloaded from Firebase Console > Project Settings > Service Accounts |

## Files to Modify

| File | What Changes |
|------|-------------|
| `android/build.gradle.kts` | Add `com.google.gms.google-services` plugin declaration |
| `android/app/build.gradle.kts` | Apply google-services plugin + add Firebase BOM + firebase-messaging-ktx |
| `android/app/src/main/AndroidManifest.xml` | Add `POST_NOTIFICATIONS` permission + register `FCMService` (preserve all existing entries) |
| `android/...WarnABrothaApp.kt` | Create `"taps_alerts"` notification channel in `onCreate()` |
| `android/...data/repository/TokenRepository.kt` | Add `savePushToken()` / `getPushToken()` with `KEY_PUSH_TOKEN` |
| `android/...data/model/ApiModels.kt` | No changes needed — `DeviceRegistration.pushToken` already exists |
| `android/...ui/viewmodel/AppViewModel.kt` | Add `pushToken`, `notificationPermissionGranted`, `unreadNotificationCount` to `AppUiState` + new functions |
| `android/...MainActivity.kt` | Add `POST_NOTIFICATIONS` permission request using `rememberLauncherForActivityResult` |
| `backend/requirements.txt` | Add `firebase-admin==6.4.0` |
| `backend/app/config.py` | Add `firebase_credentials_json: Optional[str] = None` |
| `backend/app/main.py` | Initialize Firebase Admin SDK in lifespan startup |
| `backend/app/services/notification.py` | Add `_send_fcm()`, `_is_fcm_token()`, refactor `send_push_notification()` to dispatch by token type |
| `backend/app.yaml` | Add `FIREBASE_CREDENTIALS_JSON` env var |
