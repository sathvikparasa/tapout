# WarnABrotha / TapOut — Comprehensive Testing Plan

## Executive Summary

### Current State
- **Backend (Python FastAPI):** 83 tests across 8 files, but 16 tests in `test_predictions.py` are **broken** — they reference methods (`_calculate_time_of_day_factor`, `_get_risk_level`, etc.) that were removed when the prediction service was rewritten to use `_classify_risk()`.
- **Android (Kotlin Compose):** **Zero tests.** Test directories don't exist. Test dependencies (JUnit 4, Espresso, Compose Test) are declared in `build.gradle.kts` but unused.
- **Untested backend services:** `notification.py` push sending (`send_push_notification`, `_send_apns`, `_send_fcm`) and the entire `reminder.py` service have no tests.

### Strategy
1. Fix what's broken first (prediction tests)
2. Cover untested critical paths (push notifications, reminders)
3. Fill gaps in existing backend test suites
4. Stand up Android test infrastructure and write unit tests
5. Add integration, security, and performance tests
6. Wire everything into CI/CD

---

## 1. Current State Audit

| Module | File | Tests | Status |
|--------|------|-------|--------|
| Auth | `test_auth.py` | 13 | Working |
| Feed | `test_feed.py` | 17 | Working |
| Health | `test_health.py` | 2 | Working |
| Notifications | `test_notifications.py` | 8 | Working (in-app only; push untested) |
| Parking Lots | `test_parking_lots.py` | 8 | Working |
| Parking Sessions | `test_parking_sessions.py` | 10 | Working |
| Predictions | `test_predictions.py` | 16 | **BROKEN** — all reference removed methods |
| Sightings | `test_sightings.py` | 9 | Working |
| Reminder Service | *(none)* | 0 | **No test file** |
| Push Notifications | *(none)* | 0 | **Untested** |
| Android (all) | *(none)* | 0 | **No test files or directories** |

**Effective working tests: 67 / 83**

---

## 2. Priority 1 — Critical Fixes

### 2A. Rewrite Prediction Tests

**File:** `backend/tests/test_predictions.py`

The prediction service (`backend/app/services/prediction.py`) was rewritten. The current API:

- `PredictionService.predict(db, timestamp?, lot_id?)` — main entry point
- `PredictionService._classify_risk(hours_ago: float) -> str` — risk classification:
  - 0–1 hours → `"HIGH"`
  - 1–2 hours → `"LOW"`
  - 2–4 hours → `"MEDIUM"`
  - \>4 hours → `"HIGH"`
- `PredictionService._format_time_ago(hours_ago: float) -> str`
- `PredictionService._build_no_sighting_response(now, lot_name?)` — no sightings today
- `PredictionService._build_sighting_response(now, hours_ago, sighting, lot)` — with sighting data

**Delete all 16 existing tests. Replace with:**

```
class TestClassifyRisk:
    test_classify_risk_very_recent           — hours_ago=0.5 → "HIGH"
    test_classify_risk_boundary_one_hour     — hours_ago=1.0 → edge case
    test_classify_risk_low_range             — hours_ago=1.5 → "LOW"
    test_classify_risk_boundary_two_hours    — hours_ago=2.0 → edge case
    test_classify_risk_medium_range          — hours_ago=3.0 → "MEDIUM"
    test_classify_risk_boundary_four_hours   — hours_ago=4.0 → edge case
    test_classify_risk_old                   — hours_ago=6.0 → "HIGH"
    test_classify_risk_zero                  — hours_ago=0.0 → "HIGH"

class TestFormatTimeAgo:
    test_format_minutes_ago                  — hours_ago=0.5 → "30 minutes ago" (or similar)
    test_format_one_hour_ago                 — hours_ago=1.0
    test_format_several_hours_ago            — hours_ago=3.0

class TestBuildResponses:
    test_build_no_sighting_response          — verify PredictionResponse fields when no sightings
    test_build_no_sighting_with_lot_name     — verify lot_name appears in response
    test_build_sighting_response             — verify response includes risk, time_ago, sighting data

class TestPredict:
    test_predict_no_sightings_today          — db with no sightings → no-sighting response
    test_predict_with_recent_sighting        — sighting 30min ago → HIGH risk
    test_predict_with_old_sighting           — sighting 3h ago → MEDIUM risk
    test_predict_specific_lot                — lot_id filter works
    test_predict_nonexistent_lot             — lot_id doesn't exist → appropriate handling
    test_predict_custom_timestamp            — passing specific timestamp

class TestPredictionEndpoints:
    test_get_global_prediction               — GET /api/v1/predictions
    test_get_lot_prediction                  — GET /api/v1/predictions/{lot_id}
    test_post_prediction_specific_time       — POST /api/v1/predictions
    test_prediction_requires_auth            — no token → 401/403
```

**Mocking notes:**
- `TestPredict` and `TestBuildResponses` need `db_session` fixture with `TapsSighting` and `ParkingLot` rows
- Endpoint tests use the `client` and `auth_headers` fixtures from `conftest.py`

---

### 2B. Push Notification Tests

**File to create:** `backend/tests/test_push_notifications.py`

Tests for `NotificationService.send_push_notification`, `_send_apns`, `_send_fcm`, and `_is_fcm_token`.

```
class TestIsFcmToken:
    test_fcm_token_detected                  — long alphanumeric token with colon → True
    test_apns_token_detected                 — 64-char hex string → False
    test_empty_token                         — "" → False

class TestSendPushNotification:
    test_send_to_fcm_token                   — FCM token routes to _send_fcm (mock _send_fcm)
    test_send_to_apns_token                  — APNs token routes to _send_apns (mock _send_apns)
    test_send_with_data_payload              — extra data dict passed through
    test_send_with_empty_token               — gracefully returns False
    test_send_returns_false_on_failure       — underlying send fails → returns False

class TestSendFcm:
    test_send_fcm_success                    — mock google.auth + requests.post → True
    test_send_fcm_http_error                 — mock 400/500 response → False
    test_send_fcm_missing_credentials        — no service account → False
    test_send_fcm_message_format             — verify FCM v1 payload structure

class TestSendApns:
    test_send_apns_success                   — mock APNs client → True
    test_send_apns_failure                   — mock APNs error → False
    test_send_apns_client_init               — _get_apns_client creates client once
    test_send_apns_missing_cert              — no cert configured → None client → False

class TestSendCheckoutReminder:
    test_send_checkout_reminder_success       — device has push_token, push enabled → sends notification
    test_send_checkout_reminder_no_push_token — device has no push_token → skips push, still creates in-app
    test_send_checkout_reminder_push_disabled — is_push_enabled=False → skips push

class TestNotifyParkedUsers:
    test_notify_single_user                  — one user parked → one notification created + push sent
    test_notify_multiple_users               — three users parked → three notifications
    test_notify_no_users_parked              — no active sessions → returns 0
    test_notify_user_no_push_token           — user without push_token → in-app only
```

**Mocking notes:**
- `_send_fcm`: mock `google.auth.default`, `google.auth.transport.requests.Request`, and `requests.post`
- `_send_apns`: mock the `gobiko.apns` client (or whatever APNs library is used)
- `send_push_notification`: mock `_send_fcm` and `_send_apns` directly
- `notify_parked_users` and `send_checkout_reminder`: need `db_session` with `Device`, `ParkingSession`, `ParkingLot` rows; mock `send_push_notification`

---

### 2C. Reminder Service Tests

**File to create:** `backend/tests/test_reminders.py`

Tests for `ReminderService.process_pending_reminders` and `run_reminder_job`.

```
class TestProcessPendingReminders:
    test_no_pending_reminders                — no sessions needing reminders → returns 0
    test_session_under_3_hours               — checked_in 2h ago → not yet due → returns 0
    test_session_over_3_hours                — checked_in 3.5h ago, reminder_sent=False → sends reminder, returns 1
    test_session_already_reminded            — checked_in 4h ago, reminder_sent=True → skips → returns 0
    test_session_already_checked_out         — checked_out_at set → skips
    test_multiple_sessions_due               — 3 sessions due → sends 3 reminders, returns 3
    test_mixed_sessions                      — 1 due + 1 not due + 1 already reminded → returns 1
    test_reminder_sets_flag                  — after processing, session.reminder_sent == True
    test_reminder_calls_notification_service — verify NotificationService.send_checkout_reminder called with correct args

class TestRunReminderJob:
    test_run_reminder_job_calls_process      — verify it calls process_pending_reminders
    test_run_reminder_job_handles_errors     — exception in process → logged, not raised
```

**Mocking notes:**
- Need `db_session` with `ParkingSession` rows at various `checked_in_at` times
- Mock `NotificationService.send_checkout_reminder` to avoid actual push sending
- Mock `datetime.now()` or use `freezegun` for deterministic time testing

**New fixture needed in `conftest.py`:**
```python
@pytest.fixture
async def active_session(db_session, verified_device, test_parking_lot):
    """A parking session checked in 4 hours ago, no reminder sent."""
    session = ParkingSession(
        device_id=verified_device.id,
        parking_lot_id=test_parking_lot.id,
        checked_in_at=datetime.utcnow() - timedelta(hours=4),
        reminder_sent=False,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
```

---

## 3. Priority 2 — Backend Gap Filling

Additional tests for modules that have coverage but are missing edge cases.

### 3A. Auth Service (`test_auth.py`)

```
test_is_valid_ucd_email_valid              — "user@ucdavis.edu" → True
test_is_valid_ucd_email_invalid_domain     — "user@gmail.com" → False
test_is_valid_ucd_email_empty              — "" → False
test_is_valid_ucd_email_no_at              — "userucdavis.edu" → False
test_create_access_token_default_expiry    — token decodes with expected exp
test_create_access_token_custom_expiry     — custom timedelta reflected
test_decode_token_valid                    — round-trip encode/decode
test_decode_token_expired                  — expired token → None
test_decode_token_invalid                  — garbage string → None
test_get_or_create_device_new              — new device_id → creates Device
test_get_or_create_device_existing         — existing device_id → returns same Device
test_get_or_create_device_updates_push     — existing device + new push_token → updates
test_verify_email_success                  — valid UCD email → (True, message)
test_verify_email_invalid                  — non-UCD email → (False, message)
test_verify_email_already_verified         — re-verify same email → idempotent
test_get_current_device_valid_token        — valid Bearer token → returns Device
test_get_current_device_no_token           — missing auth → HTTPException
test_require_verified_device_verified      — email_verified=True → returns device
test_require_verified_device_unverified    — email_verified=False → HTTPException
```

### 3B. Notification Service — In-App (`test_notifications.py`)

```
test_create_notification_taps_spotted      — type=TAPS_SPOTTED → saved with correct fields
test_create_notification_checkout_reminder — type=CHECKOUT_REMINDER → saved
test_get_unread_empty                      — no notifications → empty list
test_get_unread_with_read_and_unread       — only unread returned
test_get_unread_respects_limit             — limit=2 with 5 unread → 2 returned
test_get_all_notifications_pagination      — offset/limit work correctly
test_get_all_notifications_total_count     — total count matches
test_mark_notifications_read               — specific IDs marked, others untouched
test_mark_notifications_read_empty_list    — empty list → 0 updated
test_mark_notifications_read_wrong_device  — can't mark another device's notifications
```

### 3C. Parking Lots (`test_parking_lots.py`)

```
test_list_lots_empty                       — no lots → empty list
test_list_lots_only_active                 — inactive lots excluded
test_get_lot_by_id                         — returns correct lot with stats
test_get_lot_by_id_not_found               — 404
test_get_lot_by_code                       — code lookup works
test_get_lot_by_code_not_found             — 404
test_lot_stats_include_active_sessions     — session count reflects checkins
test_lot_stats_include_latest_sighting     — most recent sighting included
```

### 3D. Parking Sessions (`test_parking_sessions.py`)

```
test_checkin_success                        — creates session, returns 201
test_checkin_already_checked_in             — second checkin → error
test_checkin_invalid_lot                    — nonexistent lot → 404
test_checkin_requires_verification          — unverified device → 403
test_checkout_success                       — sets checked_out_at
test_checkout_no_active_session             — nothing to check out → error
test_get_current_session_active             — returns active session
test_get_current_session_none               — no active session → null/204
test_session_history_empty                  — no history → empty list
test_session_history_ordered                — most recent first
test_session_history_includes_checked_out   — completed sessions included
```

### 3E. Sightings (`test_sightings.py`)

```
test_report_sighting_success               — creates sighting, returns 201
test_report_sighting_with_notes            — notes saved
test_report_sighting_invalid_lot           — nonexistent lot → 404
test_report_sighting_requires_verification — unverified device → 403
test_list_sightings_recent                 — returns last N sightings
test_list_sightings_empty                  — no sightings → empty list
test_get_latest_sighting_for_lot           — returns most recent at that lot
test_get_latest_sighting_no_data           — no sightings at lot → null/404
test_sighting_triggers_notification        — reporting sighting calls notify_parked_users
```

### 3F. Feed & Voting (`test_feed.py`)

```
test_get_all_feeds                         — grouped by lot, last 3 hours
test_get_all_feeds_excludes_old            — sightings >3h ago excluded
test_get_feed_for_lot                      — only sightings at that lot
test_get_feed_for_lot_empty                — no sightings → empty
test_vote_upvote                           — creates upvote
test_vote_downvote                         — creates downvote
test_vote_change_type                      — upvote then downvote → updates
test_vote_duplicate_same_type              — upvote twice → idempotent or error
test_remove_vote                           — deletes vote
test_remove_vote_nonexistent               — nothing to remove → error/noop
test_get_vote_counts                       — returns correct up/down tallies
test_vote_on_nonexistent_sighting          — 404
test_vote_requires_verification            — unverified → 403
test_feed_includes_vote_counts             — feed response includes vote tallies
test_feed_includes_user_vote_status        — response shows if current device voted
```

---

## 4. Priority 3 — Backend Integration Tests (Cross-Module Interactions)

**File to create:** `backend/tests/test_integration.py`

These tests verify that state changes from one endpoint/service are correctly reflected by other endpoints that read that state. All lot stats (`active_parkers`, `recent_sightings`, `risk_level`) are **live queries with no caching**, so every mutation should be immediately visible.

> **Key data flows in the system:**
> - Check-in/check-out → lot stats (active parkers count) → notification targeting pool
> - Sighting reported → predictions (risk level) → lot stats (recent sightings count) → feed → notifications to parked users
> - Votes → feed vote counts
> - Notification creation → unread count; mark-as-read → unread count
> - Active sessions older than 3h → reminder service → notification creation

### 4A. Check-in / Check-out ↔ Lot Stats

```
test_checkin_increases_active_parkers
    1. GET /lots/{id} → active_parkers = 0
    2. POST /sessions/checkin at that lot
    3. GET /lots/{id} → active_parkers = 1

test_checkout_decreases_active_parkers
    1. Check in device at lot → active_parkers = 1
    2. POST /sessions/checkout
    3. GET /lots/{id} → active_parkers = 0

test_multiple_users_parked_at_lot
    1. 3 devices check in at lot A
    2. GET /lots/{lot_a_id} → active_parkers = 3
    3. 1 device checks out
    4. GET /lots/{lot_a_id} → active_parkers = 2

test_checkin_only_affects_target_lot
    1. Device checks in at lot A
    2. GET /lots/{lot_a_id} → active_parkers = 1
    3. GET /lots/{lot_b_id} → active_parkers = 0

test_checkout_after_lot_switch
    1. Device checks in at lot A → lot A active_parkers = 1
    2. Device checks out from lot A → lot A active_parkers = 0
    3. Device checks in at lot B → lot B active_parkers = 1, lot A still 0
```

### 4B. Sighting ↔ Predictions ↔ Lot Stats

The prediction service reads from `taps_sightings` to compute risk. The lot details endpoint calls `PredictionService.predict()` and also counts recent sightings (last 24h).

```
test_sighting_updates_lot_risk_level
    1. GET /lots/{id} → risk_level reflects no recent sightings
    2. POST /sightings at that lot (creates TapsSighting)
    3. GET /lots/{id} → risk_level now "HIGH" (sighting just reported, 0 hours ago)

test_sighting_updates_prediction_endpoint
    1. GET /predictions/{lot_id} → no-sighting response
    2. POST /sightings at that lot
    3. GET /predictions/{lot_id} → HIGH risk, time_ago ≈ "just now"

test_sighting_increments_recent_sightings_count
    1. GET /lots/{id} → recent_sightings_24h = 0
    2. POST /sightings at that lot
    3. GET /lots/{id} → recent_sightings_24h = 1
    4. POST /sightings again
    5. GET /lots/{id} → recent_sightings_24h = 2

test_sighting_at_lot_a_does_not_affect_lot_b_prediction
    1. POST /sightings at lot A
    2. GET /predictions/{lot_a_id} → HIGH risk
    3. GET /predictions/{lot_b_id} → still no-sighting response

test_prediction_changes_as_sighting_ages
    1. POST /sightings at lot (freeze time at T)
    2. GET /predictions/{lot_id} → HIGH (0-1h)
    3. Advance time 1.5 hours
    4. GET /predictions/{lot_id} → LOW (1-2h)
    5. Advance time to 3 hours total
    6. GET /predictions/{lot_id} → MEDIUM (2-4h)
    7. Advance time to 5 hours total
    8. GET /predictions/{lot_id} → HIGH (>4h, stale)

test_newer_sighting_overrides_older_for_prediction
    1. POST /sightings at lot (freeze time at T)
    2. Advance time 3 hours → risk is MEDIUM
    3. POST new sighting at same lot
    4. GET /predictions/{lot_id} → HIGH again (most recent sighting is fresh)
```

### 4C. Sighting → Notification → Push Flow

When a sighting is reported, `notify_parked_users()` queries active `ParkingSession` rows to decide who gets notified. Check-in/check-out changes this pool.

```
test_sighting_creates_notifications_for_parked_users
    1. Create parking lot, two devices, check both in
    2. Third device reports sighting at that lot
    3. Verify both parked devices received TAPS_SPOTTED notifications
    4. Verify send_push_notification called for devices with push tokens

test_sighting_notification_skips_reporter
    1. Device A checked in at lot, Device A reports sighting
    2. Verify Device A does NOT get notified about their own sighting

test_checked_out_user_not_notified
    1. Device A checks in at lot
    2. Device A checks out
    3. Device B reports sighting at that lot
    4. Verify Device A does NOT receive notification (no longer parked)

test_checkin_then_sighting_then_checkout_then_sighting
    1. Device A checks in at lot
    2. Device B reports sighting → Device A notified (count = 1 notification)
    3. Device A checks out
    4. Device C reports sighting → Device A NOT notified (still 1 notification total)

test_notification_targets_only_users_at_sighted_lot
    1. Device A checks in at lot 1
    2. Device B checks in at lot 2
    3. Sighting reported at lot 1
    4. Device A receives notification, Device B does not

test_sighting_notification_count_matches_parked_users
    1. 5 devices check in at lot
    2. 2 devices check out
    3. Sighting reported → POST /sightings returns notified_count = 3
```

### 4D. Check-in ↔ Reminder ↔ Notification

The reminder service queries sessions where `checked_in_at <= now - 3h` AND `checked_out_at IS NULL` AND `reminder_sent = FALSE`. It then creates a CHECKOUT_REMINDER notification.

```
test_full_reminder_flow
    1. Device checks in
    2. Advance time 3+ hours (freezegun)
    3. Run process_pending_reminders
    4. Verify CHECKOUT_REMINDER notification created
    5. GET /notifications/unread → includes the reminder
    6. Verify session.reminder_sent = True
    7. Run process_pending_reminders again → no duplicate reminder

test_checkout_before_reminder_prevents_notification
    1. Device checks in
    2. Device checks out after 2 hours
    3. Advance time to 3+ hours
    4. Run process_pending_reminders
    5. Verify no reminder sent (session already checked out)
    6. GET /notifications/unread → empty

test_reminder_does_not_fire_for_recent_session
    1. Device checks in
    2. Advance time only 2 hours (under threshold)
    3. Run process_pending_reminders → returns 0
    4. No notification created

test_multiple_users_get_independent_reminders
    1. Device A checks in at lot 1
    2. Device B checks in at lot 2
    3. Advance time 3+ hours
    4. Run process_pending_reminders → returns 2
    5. Each device has its own CHECKOUT_REMINDER notification
    6. Reminders reference correct lot names
```

### 4E. Voting ↔ Feed Display

Votes mutate the `votes` table. The feed endpoint performs live queries to count upvotes/downvotes per sighting.

```
test_vote_reflected_in_feed
    1. Report sighting at lot
    2. GET /feed/{lot_id} → sighting has upvotes=0, downvotes=0
    3. POST /feed/sightings/{id}/vote (upvote)
    4. GET /feed/{lot_id} → sighting has upvotes=1, downvotes=0

test_vote_change_reflected_in_feed
    1. Device upvotes sighting
    2. GET /feed → upvotes=1
    3. Device changes vote to downvote
    4. GET /feed → upvotes=0, downvotes=1

test_remove_vote_reflected_in_feed
    1. Device upvotes sighting
    2. GET /feed → upvotes=1
    3. DELETE /feed/sightings/{id}/vote
    4. GET /feed → upvotes=0

test_vote_tallies_accurate_with_multiple_voters
    1. 3 devices upvote sighting
    2. 1 device changes to downvote
    3. GET /feed → upvotes=2, downvotes=1

test_votes_isolated_per_sighting
    1. Device upvotes sighting A
    2. Device downvotes sighting B
    3. GET /feed → sighting A: 1 up 0 down; sighting B: 0 up 1 down

test_feed_shows_current_user_vote_status
    1. Device A upvotes sighting
    2. GET /feed (as Device A) → user_vote = "upvote"
    3. GET /feed (as Device B) → user_vote = null
```

### 4F. Sighting ↔ Feed

Sightings appear in the feed. The feed only shows sightings from the last 3 hours.

```
test_new_sighting_appears_in_feed
    1. GET /feed/{lot_id} → empty
    2. POST /sightings at lot
    3. GET /feed/{lot_id} → 1 sighting

test_sighting_disappears_from_feed_after_3_hours
    1. POST /sightings (freeze time at T)
    2. GET /feed → 1 sighting
    3. Advance time 3+ hours
    4. GET /feed → 0 sightings (excluded by 3-hour window)

test_sighting_at_lot_a_not_in_lot_b_feed
    1. POST /sightings at lot A
    2. GET /feed/{lot_a_id} → 1 sighting
    3. GET /feed/{lot_b_id} → 0 sightings

test_all_feeds_groups_by_lot
    1. POST /sightings at lot A
    2. POST /sightings at lot B (x2)
    3. GET /feed → lot A has 1 sighting, lot B has 2 sightings
```

### 4G. Auth Flow ↔ Protected Endpoints

Verification state gates access to check-in, sighting reporting, and voting.

```
test_full_registration_to_action_flow
    1. POST /auth/register → get token
    2. GET /auth/me → email_verified=False
    3. POST /sessions/checkin → 403 (unverified)
    4. POST /sightings → 403 (unverified)
    5. POST /auth/verify-email with UCD email → verified
    6. GET /auth/me → email_verified=True
    7. POST /sessions/checkin → 201 (now works)
    8. POST /sightings → 201 (now works)

test_token_persistence_across_re_registration
    1. Register device_id="abc" → token A
    2. Register again with device_id="abc" → token B
    3. Verify device record is same (same DB id)
    4. Verify token B works for authenticated endpoints
```

### 4H. Notification Lifecycle (Create → Read → Mark Read → Unread Count)

```
test_notification_lifecycle
    1. GET /notifications/unread → empty (count = 0)
    2. Device checks in, sighting reported → TAPS_SPOTTED notification created
    3. GET /notifications/unread → count = 1
    4. POST /notifications/read with notification IDs
    5. GET /notifications/unread → count = 0
    6. GET /notifications → still shows the notification (with read_at set)

test_mark_all_read_clears_unread_count
    1. Create 3 notifications (via sightings or reminders)
    2. GET /notifications/unread → count = 3
    3. POST /notifications/read/all
    4. GET /notifications/unread → count = 0

test_new_notification_after_mark_read
    1. Sighting → notification created
    2. POST /notifications/read → unread = 0
    3. Another sighting → new notification created
    4. GET /notifications/unread → count = 1 (only the new one)
```

### 4I. Push Token Update ↔ Notification Delivery

```
test_push_token_update_affects_notification_delivery
    1. Device registers without push token
    2. Sighting reported → in-app notification created, but no push sent
    3. PATCH /auth/me with push_token
    4. Sighting reported → in-app notification created AND push sent (mock send_push_notification)

test_push_disabled_skips_push_but_creates_in_app
    1. Device has push_token but is_push_enabled=False
    2. Sighting reported
    3. In-app notification created, push NOT sent
```

### 4J. Session State ↔ Current Session Endpoint

```
test_current_session_reflects_checkin
    1. GET /sessions/current → null/204
    2. POST /sessions/checkin at lot A
    3. GET /sessions/current → active session at lot A

test_current_session_reflects_checkout
    1. POST /sessions/checkin
    2. GET /sessions/current → active session
    3. POST /sessions/checkout
    4. GET /sessions/current → null/204

test_session_history_grows_with_completed_sessions
    1. GET /sessions/history → empty
    2. Check in, check out
    3. GET /sessions/history → 1 session (with checked_out_at)
    4. Check in, check out again
    5. GET /sessions/history → 2 sessions, most recent first
```

---

## 5. Priority 4 — Android Unit Tests

### 5A. Test Infrastructure Setup

**Create directories:**
```
android/app/src/test/java/com/warnabrotha/app/
android/app/src/test/java/com/warnabrotha/app/data/
android/app/src/test/java/com/warnabrotha/app/ui/
```

**Add dependencies to `android/app/build.gradle.kts`:**
```kotlin
// Unit testing
testImplementation("junit:junit:4.13.2")  // already present
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
testImplementation("io.mockk:mockk:1.13.13")
testImplementation("app.cash.turbine:turbine:1.2.0")  // StateFlow testing
testImplementation("org.robolectric:robolectric:4.14.1")

// Android instrumented testing
androidTestImplementation("androidx.test.ext:junit:1.2.1")  // already present
androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")  // already present
androidTestImplementation("androidx.compose.ui:ui-test-junit4")  // already present
androidTestImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
androidTestImplementation("io.mockk:mockk-android:1.13.13")
```

### 5B. AppViewModel Tests

**File:** `android/app/src/test/java/com/warnabrotha/app/ui/viewmodel/AppViewModelTest.kt`

Uses: `mockk` for `AppRepository`, `kotlinx-coroutines-test` for `runTest`, `turbine` for StateFlow assertions.

```
class AppViewModelTest {
    // Setup: mock AppRepository, create AppViewModel, use TestDispatcher

    // Auth
    test_initial_state_is_default              — uiState matches AppUiState defaults
    test_check_auth_status_with_token          — hasToken()=true → isLoggedIn=true, loadInitialData called
    test_check_auth_status_no_token            — hasToken()=false → isLoggedIn=false
    test_register_success                      — repository.register() Success → isLoggedIn=true
    test_register_failure                      — repository.register() Error → error message set
    test_verify_email_success                  — repository.verifyEmail() Success → isEmailVerified=true
    test_verify_email_invalid_email            — repository.verifyEmail() Error → error message set

    // Data Loading
    test_load_initial_data_loads_lots          — after login, parkingLots populated
    test_load_initial_data_loads_feeds         — after login, feeds populated
    test_select_lot                            — selectLot(id) → selectedLotId updated, lot data loaded
    test_select_feed_filter                    — selectFeedFilter(lotId) → feedFilterLotId updated

    // Check-in / Check-out
    test_checkin_success                       — checkIn() Success → currentSession set, success message
    test_checkin_failure                       — checkIn() Error → error message set
    test_checkin_at_lot_success                — checkInAtLot(lotId) → session at that lot
    test_checkout_success                      — checkOut() Success → currentSession null, success message
    test_checkout_failure                      — checkOut() Error → error message set

    // Sighting Reporting
    test_report_sighting_success               — reportSighting() → success message, feeds refreshed
    test_report_sighting_with_notes            — notes passed to repository
    test_report_sighting_at_lot_success        — reportSightingAtLot(lotId) → correct lot used

    // Voting
    test_vote_upvote                           — vote(id, "upvote") → repository.vote called
    test_vote_downvote                         — vote(id, "downvote") → repository.vote called

    // Notifications
    test_notification_permission_granted       — onNotificationPermissionResult(true) → syncs push token
    test_notification_permission_denied        — onNotificationPermissionResult(false) → no crash
    test_fetch_unread_count                    — fetchUnreadNotificationCount() → unreadCount updated

    // UI State
    test_clear_error                           — clearError() → error=null
    test_clear_success_message                 — clearSuccessMessage() → successMessage=null
    test_refresh_reloads_data                  — refresh() → lots, feeds, session reloaded
}
```

### 5C. AppRepository Tests

**File:** `android/app/src/test/java/com/warnabrotha/app/data/repository/AppRepositoryTest.kt`

Uses: `mockk` for `ApiService` and `TokenRepository`.

```
class AppRepositoryTest {
    // Setup: mock ApiService + TokenRepository

    // Auth
    test_register_success                      — apiService.register returns 200 → Result.Success
    test_register_network_error                — apiService.register throws → Result.Error
    test_register_saves_token                  — on success, tokenRepository.saveToken called
    test_verify_email_success                  — 200 response → Result.Success
    test_verify_email_failure                  — 400 response → Result.Error with message
    test_get_device_info_success               — 200 → Result.Success(DeviceResponse)

    // Parking
    test_get_parking_lots_success              — returns list of ParkingLot
    test_get_parking_lot_success               — returns ParkingLotWithStats
    test_checkin_success                        — 201 → Result.Success(ParkingSession)
    test_checkin_error_already_checked_in       — 409/400 → Result.Error
    test_checkout_success                       — 200 → Result.Success(CheckoutResponse)
    test_get_current_session_active             — 200 with body → Result.Success(ParkingSession)
    test_get_current_session_none               — 200 with null body → Result.Success(null)

    // Sightings & Feed
    test_report_sighting_success               — 201 → Result.Success(SightingResponse)
    test_get_feed_success                      — 200 → Result.Success(FeedResponse)
    test_get_all_feeds_success                 — 200 → Result.Success(AllFeedsResponse)

    // Voting
    test_vote_success                          — 200 → Result.Success(VoteResult)
    test_remove_vote_success                   — 200 → Result.Success(VoteResult)

    // Predictions & Stats
    test_get_prediction_success                — 200 → Result.Success(PredictionResponse)
    test_get_global_stats_success              — 200 → Result.Success(GlobalStatsResponse)

    // Token delegation
    test_has_token_delegates                   — calls tokenRepository.hasToken()
    test_get_saved_push_token_delegates        — calls tokenRepository.getPushToken()
    test_save_push_token_delegates             — calls tokenRepository.savePushToken()
}
```

### 5D. TokenRepository Tests

**File:** `android/app/src/test/java/com/warnabrotha/app/data/repository/TokenRepositoryTest.kt`

Uses: Robolectric for `Context` (EncryptedSharedPreferences needs Android APIs).

```
class TokenRepositoryTest {
    // Setup: Robolectric ApplicationProvider.getApplicationContext()

    test_save_and_get_token                    — saveToken("abc") then getToken() → "abc"
    test_get_token_when_none_saved             — getToken() → null
    test_clear_token                           — saveToken, clearToken, getToken → null
    test_has_token_true                        — after saveToken → true
    test_has_token_false                       — before saveToken → false
    test_get_or_create_device_id_creates       — first call generates UUID
    test_get_or_create_device_id_stable        — second call returns same UUID
    test_save_and_get_push_token               — savePushToken("token") → getPushToken() returns "token"
    test_get_push_token_when_none              — getPushToken() → null
}
```

### 5E. AuthInterceptor Tests

**File:** `android/app/src/test/java/com/warnabrotha/app/data/api/AuthInterceptorTest.kt`

Uses: `mockk` for `TokenRepository` and OkHttp `Interceptor.Chain`.

```
class AuthInterceptorTest {
    test_adds_bearer_token                     — token exists → "Authorization: Bearer {token}" header added
    test_no_token_no_header                    — token is null → no Authorization header
    test_does_not_overwrite_existing_header     — request already has Authorization → behavior check
    test_passes_request_to_chain               — chain.proceed called with (possibly modified) request
}
```

### 5F. ApiModels Tests

**File:** `android/app/src/test/java/com/warnabrotha/app/data/model/ApiModelsTest.kt`

Basic serialization/deserialization tests using Gson directly.

```
class ApiModelsTest {
    // Verify JSON round-trips for critical models
    test_token_response_deserialization        — JSON string → TokenResponse
    test_parking_lot_deserialization           — JSON → ParkingLot with all fields
    test_parking_session_deserialization       — JSON → ParkingSession
    test_prediction_response_deserialization   — JSON → PredictionResponse
    test_feed_sighting_deserialization         — JSON → FeedSighting with votes
    test_notification_item_deserialization     — JSON → NotificationItem
    test_device_response_deserialization       — JSON → DeviceResponse
    test_null_fields_handled                   — nullable fields absent → null, not crash
}
```

---

## 6. Priority 5 — Android Integration Tests

### 6A. MockWebServer API Tests

**File:** `android/app/src/test/java/com/warnabrotha/app/data/api/ApiServiceTest.kt`

Uses: `okhttp3.mockwebserver.MockWebServer`, Retrofit instance pointed at mock server.

```
class ApiServiceTest {
    // Setup: MockWebServer, Retrofit with mock base URL

    test_register_sends_correct_request        — verify POST body and path
    test_register_parses_response              — mock 200 → TokenResponse parsed
    test_verify_email_sends_correct_request    — verify POST body
    test_get_parking_lots_parses_list          — mock JSON array → List<ParkingLot>
    test_checkin_sends_lot_id                  — verify POST body contains parking_lot_id
    test_report_sighting_sends_notes           — verify POST body
    test_vote_sends_correct_type               — verify POST body
    test_error_response_handling               — mock 400/500 → Response.isSuccessful = false
    test_auth_header_sent                      — AuthInterceptor adds header to outgoing request
}
```

### 6B. Compose UI Tests (Instrumented)

**File:** `android/app/src/androidTest/java/com/warnabrotha/app/ui/`

These require an emulator or device. Lower priority but valuable for regression.

```
class WelcomeScreenTest {
    test_welcome_screen_displays               — "Get Started" button visible
    test_get_started_navigates                 — click → registration triggered

class EmailVerificationScreenTest {
    test_email_input_displayed                 — text field visible
    test_submit_with_valid_email               — "user@ucdavis.edu" → verify called
    test_submit_with_invalid_email             — shows error

class MainScreenTest:
    test_bottom_nav_tabs_displayed             — Map, Feed, Report tabs visible
    test_tab_navigation                        — clicking tab switches content

class MapTabTest:
    test_map_displayed                         — map composable rendered
    test_lot_markers_shown                     — parking lots appear as markers

class FeedTabTest:
    test_sighting_cards_displayed              — feed items rendered
    test_vote_buttons_work                     — clicking upvote triggers vote

class ReportTabTest:
    test_checkin_button_displayed              — check-in button visible
    test_report_sighting_button                — report button visible
```

---

## 7. Priority 6 — Security Tests

**File:** `backend/tests/test_security.py`

```
class TestAuthSecurity:
    test_no_token_returns_401                  — requests without token → 401
    test_invalid_token_returns_401             — garbage token → 401
    test_expired_token_returns_401             — expired JWT → 401
    test_token_for_deleted_device              — device removed from DB → 401

class TestInputValidation:
    test_sighting_notes_max_length             — >500 chars → rejected
    test_email_xss_attempt                     — "<script>..." → rejected or sanitized
    test_sql_injection_in_lot_code             — "'; DROP TABLE..." → no effect
    test_oversized_request_body                — huge payload → 413 or rejected

class TestAccessControl:
    test_unverified_cannot_checkin              — email_verified=False → 403
    test_unverified_cannot_report_sighting      — 403
    test_cannot_read_other_device_notifications — device A can't see device B's notifications
    test_cannot_checkout_other_device_session    — device A can't checkout device B
```

---

## 8. Priority 7 — Performance Tests

**File:** `backend/tests/test_performance.py`

Uses: `time` module or `pytest-benchmark`.

```
class TestResponseTimes:
    test_health_check_fast                     — GET /health < 100ms
    test_list_lots_fast                        — GET /lots < 200ms
    test_prediction_fast                       — GET /predictions < 500ms

class TestConcurrentOperations:
    test_concurrent_sighting_reports           — 10 simultaneous sightings → all succeed
    test_concurrent_votes_same_sighting        — 10 devices vote simultaneously → correct tally
    test_concurrent_checkins_different_lots     — 10 devices check in at different lots → all succeed
```

---

## 9. CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx freezegun
      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term-missing -v
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  android-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: "temurin"
          java-version: "17"
      - name: Run unit tests
        run: |
          cd android
          ./gradlew testDebugUnitTest
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: android-test-results
          path: android/app/build/reports/tests/
```

---

## 10. Coverage Targets

| Module | Current | Target | Notes |
|--------|---------|--------|-------|
| Auth Service | ~70% | 90% | Add edge cases, token expiry |
| Prediction Service | 0% (broken) | 95% | Complete rewrite |
| Notification (in-app) | ~60% | 85% | Add edge cases |
| Notification (push) | 0% | 80% | New tests |
| Reminder Service | 0% | 90% | New tests |
| Parking Lots | ~70% | 85% | Add stats tests |
| Parking Sessions | ~70% | 85% | Add edge cases |
| Sightings | ~65% | 85% | Add notification trigger |
| Feed & Voting | ~75% | 85% | Add integrity tests |
| **Backend Overall** | **~55%** | **85%** | |
| Android ViewModel | 0% | 80% | New tests |
| Android Repository | 0% | 85% | New tests |
| Android TokenRepo | 0% | 90% | New tests |
| Android Interceptor | 0% | 95% | New tests |
| Android Models | 0% | 70% | Serialization tests |
| **Android Overall** | **0%** | **75%** | |

---

## 11. Implementation Sequencing

### Phase 1 (Week 1) — Fix Critical Breakage
- [ ] Rewrite `test_predictions.py` (22 new tests replacing 16 broken)
- [ ] Create `test_push_notifications.py` (22 tests)
- [ ] Create `test_reminders.py` (11 tests)
- [ ] Add `active_session` fixture to `conftest.py`
- **Estimated new tests: ~55**

### Phase 2 (Week 2) — Backend Gap Filling
- [ ] Expand `test_auth.py` with edge cases (~6 new tests)
- [ ] Expand `test_notifications.py` with in-app edge cases (~5 new tests)
- [ ] Expand `test_parking_lots.py` (~3 new tests)
- [ ] Expand `test_parking_sessions.py` (~3 new tests)
- [ ] Expand `test_sightings.py` (~3 new tests)
- [ ] Expand `test_feed.py` (~5 new tests)
- **Estimated new tests: ~25**

### Phase 3 (Week 3) — Backend Integration & Security
- [ ] Create `test_integration.py` (~42 cross-module interaction tests across 10 subsections)
- [ ] Create `test_security.py` (~10 tests)
- [ ] Create `test_performance.py` (~6 tests)
- **Estimated new tests: ~58**

### Phase 4 (Week 4) — Android Test Infrastructure
- [ ] Create test directories
- [ ] Add test dependencies to `build.gradle.kts`
- [ ] Write `TokenRepositoryTest.kt` (9 tests)
- [ ] Write `AuthInterceptorTest.kt` (4 tests)
- [ ] Write `ApiModelsTest.kt` (8 tests)
- **Estimated new tests: ~21**

### Phase 5 (Week 5) — Android Unit Tests
- [ ] Write `AppRepositoryTest.kt` (22 tests)
- [ ] Write `AppViewModelTest.kt` (25 tests)
- **Estimated new tests: ~47**

### Phase 6 (Week 6) — Android Integration, CI/CD
- [ ] Write `ApiServiceTest.kt` with MockWebServer (9 tests)
- [ ] Write Compose UI tests (10 tests)
- [ ] Set up `.github/workflows/test.yml`
- **Estimated new tests: ~19**

### Total

| | Current | After Plan |
|--|---------|-----------|
| Backend tests (working) | 67 | ~205 |
| Android tests | 0 | ~97 |
| **Total** | **67** | **~302** |
