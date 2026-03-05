# Live Activity Implementation Plan — TapOut (iOS)

> **Status:** Code implementation complete. Manual Xcode and database steps still required (see [What You Need To Do](#what-you-need-to-do)).

---

## Context

TapOut users check in at a UC Davis parking lot and want real-time TAPS risk updates on their lock screen while they're in class. Without Live Activities, users must open the app to check risk — defeating the purpose. This feature adds an iOS Live Activity that shows the current lot, TAPS risk level, probability %, and last sighting time, updating in real-time via APNs push-to-update even when the app is fully backgrounded.

---

## Actual Architecture

### iOS App
- **Framework:** SwiftUI, minimum iOS 17.0
- **Bundle ID:** `com.warnabrotha.tapout`
- **Entry point:** `warnabrotha/warnabrothaApp.swift`

### Backend
- **Framework:** FastAPI 0.109.0, Python 3.12
- **Hosting:** Google App Engine (`tapout-485821`)
- **Database:** PostgreSQL on **Google Cloud SQL** via SQLAlchemy async ORM
- **Secrets:** GCP Secret Manager (loaded at startup via `config.py`)
- **Schema management:** SQLAlchemy `Base.metadata.create_all` on startup — **no Alembic**. Adding columns to existing tables requires a manual `ALTER TABLE` against Cloud SQL.
- **APNs library:** `aioapns==3.1` — already supports `PushType.LIVEACTIVITY`

---

## How It Works

```
Check In  →  LiveActivityService.start()  →  Activity<TapOutActivityAttributes>
                                                      ↓
                                            activity.pushTokenUpdates
                                                      ↓
                                            APIClient.updateActivityPushToken()
                                                      ↓ PATCH /auth/me
                                             backend saves device.activity_push_token

New Sighting  →  notify_parked_users()
                       ↓
                 _send_live_activity_update(activity_push_token)
                       ↓ APNs  (push-type: liveactivity, topic: ...push-type.liveactivity)
               Lock screen / Dynamic Island updates — no app process needed

loadLotData() called  →  LiveActivityService.update()   ← local fallback when app is open

Check Out  →  LiveActivityService.end()  →  clears device.activity_push_token on backend
```

---

## Files Changed (all code already written)

| File | Action | Notes |
|------|--------|-------|
| `warnabrotha/warnabrotha/LiveActivity/TapOutActivityAttributes.swift` | **Created** | Shared model — must be added to both targets in Xcode |
| `warnabrotha/warnabrotha/Services/LiveActivityService.swift` | **Created** | Main app target only |
| `warnabrotha/TapOutWidget/TapOutLiveActivityWidget.swift` | **Created** | Widget extension target only |
| `warnabrotha/TapOutWidget/Info.plist` | **Created** | Widget extension plist |
| `warnabrotha/warnabrotha/Info.plist` | **Modified** | Added `NSSupportsLiveActivities: true` |
| `warnabrotha/warnabrotha/ViewModels/AppViewModel.swift` | **Modified** | Hooks into `checkIn`, `checkInAtLot`, `checkOut`, `loadLotData`, `loadInitialData` |
| `warnabrotha/warnabrotha/Services/APIClient.swift` | **Modified** | Added `updateActivityPushToken(_:)` |
| `backend/app/models/device.py` | **Modified** | Added `activity_push_token` column |
| `backend/app/schemas/device.py` | **Modified** | Added `activity_push_token` to `DeviceUpdate` |
| `backend/app/api/auth.py` | **Modified** | Handles new field in `PATCH /auth/me` |
| `backend/app/services/notification.py` | **Modified** | Added `_send_live_activity_update()` + call in `notify_parked_users()` |
| `backend/migrations/add_activity_push_token_to_devices.sql` | **Created** | Run this manually against Cloud SQL |

---

## What You Need To Do

### Step 1 — Run the database migration

The `devices` table already exists in Cloud SQL, so adding the new column to the SQLAlchemy model alone is not enough — you must run the SQL manually.

**Option A — Cloud SQL Studio (easiest)**
1. Go to [console.cloud.google.com](https://console.cloud.google.com) → Cloud SQL → your instance → Cloud SQL Studio
2. Run:
```sql
ALTER TABLE devices ADD COLUMN IF NOT EXISTS activity_push_token VARCHAR(255);
```

**Option B — Cloud SQL Auth Proxy + psql**
```bash
cloud-sql-proxy tapout-485821:us-central1:YOUR_INSTANCE_NAME &
psql "host=127.0.0.1 port=5432 dbname=YOUR_DB user=YOUR_USER" \
  -c "ALTER TABLE devices ADD COLUMN IF NOT EXISTS activity_push_token VARCHAR(255);"
```

The migration file is at `backend/migrations/add_activity_push_token_to_devices.sql` for reference.

---

### Step 2 — Create the Widget Extension in Xcode

This cannot be done via code — Xcode must create the target.

1. Open `warnabrotha/warnabrotha.xcodeproj` in Xcode
2. **File → New → Target → Widget Extension**
3. Set:
   - Product Name: `TapOutWidget`
   - Bundle ID: `com.warnabrotha.tapout.TapOutWidget`
   - Deployment Target: iOS 17.0
   - **Uncheck** "Include Configuration Intent"
   - **Uncheck** "Include Live Activity"
4. Click Finish — Xcode will create a `TapOutWidget.swift` file
5. **Delete the contents** of that auto-generated `TapOutWidget.swift` (leave the file, just clear it, or delete the file entirely — the bundle entry point is already defined in `TapOutLiveActivityWidget.swift`)

---

### Step 3 — Add the widget source files to the new target

The code files already exist on disk. You need to tell Xcode which target they belong to.

**Add `TapOutLiveActivityWidget.swift` to the `TapOutWidget` target:**
1. In Xcode's file navigator, find `TapOutWidget/TapOutLiveActivityWidget.swift`
2. Select it → File Inspector (right panel) → Target Membership → check `TapOutWidget`

**Add `TapOutActivityAttributes.swift` to BOTH targets:**
1. Find `warnabrotha/LiveActivity/TapOutActivityAttributes.swift`
2. File Inspector → Target Membership → check **both** `warnabrotha` and `TapOutWidget`

> This is the most common mistake. If `TapOutActivityAttributes` is only in one target, the widget won't compile.

---

### Step 4 — Add `NSSupportsLiveActivities` to the widget's Info.plist

Xcode creates a separate `Info.plist` for the widget extension target. A pre-filled one is at `TapOutWidget/Info.plist`, but Xcode may generate its own. Either way:

1. In Xcode, open the widget extension's `Info.plist` (under the `TapOutWidget` folder in the navigator)
2. Add key `NSSupportsLiveActivities` = `Boolean` = `YES`

(The main app's `Info.plist` already has this key — it was added in code.)

---

### Step 5 — Deploy the backend

The backend changes are already written. Deploy normally:

```bash
cd backend
gcloud app deploy
```

The new `activity_push_token` field in the `PATCH /auth/me` handler will be live after deployment. Run the SQL migration (Step 1) **before** deploying so the column exists when the new code first tries to write to it.

---

## Critical Notes

**APNs topic for Live Activities**
Normal push notifications use topic `com.warnabrotha.tapout`. Live Activity pushes **must** use `com.warnabrotha.tapout.push-type.liveactivity`. This is already set in `notification.py`. Using the wrong topic silently fails.

**ContentState key casing**
The `content-state` JSON keys sent by the backend must exactly match the Swift `ContentState` property names in camelCase:
- `riskLevel`, `probability`, `lastSightingMinutesAgo`, `recentSightingsCount`

A mismatch silently fails — the Live Activity won't update and no error surfaces.

**`pushType: .token` is required**
`Activity.request(..., pushType: .token)` is set in `LiveActivityService.swift`. This is what causes the activity to generate a push token that gets sent to the backend. Without it, push-to-update never works.

**Simulator limitation**
Push-to-update (backend → lock screen update) only works on **physical devices**. On simulators, you can test start/end/local-update via the app, but APNs pushes won't arrive.

---

## Verification Checklist

1. `devices` table has `activity_push_token` column in Cloud SQL
2. Both targets build without errors in Xcode
3. **Simulator:** Check in → Live Activity appears on lock screen → Check out → dismisses immediately
4. **Simulator:** With app open, report a sighting → `loadLotData()` fires → Live Activity risk level updates locally
5. **Physical device:** After check-in, verify `device.activity_push_token` is populated in Cloud SQL
6. **Physical device:** Submit a sighting via `POST /api/v1/sightings` → within ~2s the lock screen Live Activity updates to HIGH RISK without opening the app
7. **Dynamic Island (iPhone 14 Pro+):** Compact leading shows lot code pill, trailing shows risk bars
8. **App restart:** Force-quit while parked → reopen → Live Activity still on lock screen and `recoverIfNeeded()` reattaches
9. **Checkout:** After checkout, verify `activity_push_token` is `NULL` in Cloud SQL
