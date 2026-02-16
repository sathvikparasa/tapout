# Goal

Add real email OTP verification using a Gmail SMTP server, replacing the current "instant verify" flow that only checks the email domain format. **Users must only go through the OTP and "Get Started" flow once** — after initial verification, the app should never ask them to sign in again (unless they reinstall on Android, which wipes SharedPreferences).

---

## Current State

Right now, authentication works like this:

1. **Device-based identity**: The iOS app generates a UUID (`device_id`) stored in Keychain; the Android app does the same via `TokenRepository` (SharedPreferences). This is the sole user identifier — there are no user accounts, usernames, or stored emails.
2. **Registration**: Device sends its UUID to `POST /auth/register` and gets back a JWT (currently 1-week expiry via `access_token_expire_hours = 168`, signed with `SECRET_KEY`, subject = `device_id`). **Problem: after 1 week the token expires, `getDeviceInfo()` returns 401, and both apps clear all auth state — forcing the user back through the Welcome + OTP flow.**
3. **Fake email verification**: User enters a `@ucdavis.edu` email → backend regex-checks the domain → immediately sets `email_verified = True` on the `devices` row. **No OTP is sent. No email is actually verified.** The email itself is not stored.
4. **Auth enforcement**: Authenticated routes use `get_current_device` (JWT → device lookup). Some routes additionally use `require_verified_device` to gate on `email_verified`.

### Key files

| Layer | File | Role |
|-------|------|------|
| Backend API | `backend/app/api/auth.py` | `/auth/register`, `/auth/verify-email`, `/auth/me` endpoints |
| Backend Service | `backend/app/services/auth.py` | `AuthService` class (JWT creation, email regex, device CRUD), `get_current_device` dependency |
| Backend Model | `backend/app/models/device.py` | `Device` SQLAlchemy model (id, device_id, email_verified, push_token, etc.) |
| Backend Schema | `backend/app/schemas/device.py` | Pydantic request/response models for auth endpoints |
| Backend Config | `backend/app/config.py` | `Settings` — has `secret_key`, `ucd_email_domain`, `access_token_expire_hours` |
| iOS View | `warnabrotha/.../Views/EmailVerificationView.swift` | Email input UI with `@ucdavis.edu` validation |
| iOS API | `warnabrotha/.../Services/APIClient.swift` | `register()`, `verifyEmail()`, `getDeviceInfo()` |
| iOS ViewModel | `warnabrotha/.../ViewModels/AppViewModel.swift` | Auth state management (`isAuthenticated`, `isEmailVerified`, `showEmailVerification`) |
| iOS Keychain | `warnabrotha/.../Services/KeychainService.swift` | Stores device UUID and JWT token |
| Android Screen | `android/.../ui/screens/EmailVerificationScreen.kt` | Compose email input UI with `@ucdavis.edu` validation, `onVerify` callback |
| Android API | `android/.../data/api/ApiService.kt` | Retrofit interface — `register()`, `verifyEmail()`, `getDeviceInfo()` |
| Android Models | `android/.../data/model/ApiModels.kt` | Data classes: `DeviceRegistration`, `EmailVerificationRequest/Response`, `TokenResponse` |
| Android Repo | `android/.../data/repository/AppRepository.kt` | `register()`, `verifyEmail()` — wraps ApiService calls with `Result<T>` |
| Android ViewModel | `android/.../ui/viewmodel/AppViewModel.kt` | `AppUiState` data class + `verifyEmail()`, `register()`, `checkAuthStatus()` |
| Android Token | `android/.../data/repository/TokenRepository.kt` | Stores device UUID and JWT token (SharedPreferences/EncryptedSharedPreferences) |
| Android Auth Interceptor | `android/.../data/api/AuthInterceptor.kt` | OkHttp interceptor that attaches Bearer token to requests |

---

## What Needs to Change

### 1. New DB table: `email_otps`

Store OTP codes linked to a device. Schema:

```
email_otps
├── id              (Integer, PK)
├── device_id       (Integer, FK → devices.id)
├── email           (String, the email the OTP was sent to)
├── otp_code        (String, 6-digit code)
├── created_at      (DateTime, when OTP was generated)
├── expires_at      (DateTime, created_at + 10 minutes)
├── verified_at     (DateTime, nullable — set when OTP is successfully verified)
├── attempts        (Integer, default 0 — track failed attempts)
```

Constraints:
- Max 3 active (unverified, unexpired) OTPs per device to prevent spam
- Max 5 OTP send requests per email address per hour (prevent spamming a victim's inbox via multiple device IDs)
- Max 5 verification attempts per OTP before it's invalidated
- OTPs expire after 10 minutes
- **Scrub after verification**: once an OTP is successfully verified, delete all `email_otps` rows for that device (both the verified row and any leftover unverified ones). We don't persist emails beyond what's needed for the verification flow.

### 2. Gmail SMTP setup

- Use a Gmail account with an **App Password** (not the account password — requires 2FA enabled on the Gmail account)
- Send via `smtplib` with `SMTP_SSL` on port 465, or `SMTP` on port 587 with STARTTLS
- New config values needed in `Settings` and GCP Secret Manager:
  - `SMTP_EMAIL` — the Gmail sender address
  - `SMTP_PASSWORD` — the Gmail App Password
- Create a new service: `backend/app/services/email.py` with an `async send_otp_email(to_email, otp_code)` function
- Email template should be simple: "Your WarnABrotha verification code is: **123456**. It expires in 10 minutes."

### 3. Backend API changes

**Split `/auth/verify-email` into two endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/send-otp` | POST | Accepts `{ email, device_id }`. Validates `@ucdavis.edu` domain, generates 6-digit OTP, stores in `email_otps`, sends email via SMTP. Returns `{ success, message }`. |
| `/auth/verify-otp` | POST | Accepts `{ email, device_id, otp_code }`. Looks up matching OTP, checks expiry + attempts, sets `email_verified = True` on the device, marks OTP as verified. Returns `{ success, message, email_verified }`. |

**`/auth/register` rate limiting:**
- Rate-limit by client IP: max 10 registrations per IP per hour. This prevents an attacker from filling the `devices` table with junk rows.
- Use `slowapi` (FastAPI rate-limiting library, wraps `limits`) with an in-memory backend. IPs are used as temporary keys with a TTL — they are **not** stored in the database or logged.
- On GCP App Engine, the client IP is available via the `X-Forwarded-For` header. `slowapi` handles this automatically with `get_remote_address`.
- 10/hr is generous enough to avoid false positives for users behind shared NAT (e.g., campus Wi-Fi).

**`/auth/send-otp` logic:**
1. Validate email is `@ucdavis.edu`
2. Look up device by `device_id` (must exist — call `/auth/register` first)
3. Check rate limit: no more than 3 unexpired OTPs for this device
4. Check rate limit: no more than 5 OTPs sent to this email address in the last hour (across all devices)
5. Generate a random 6-digit numeric code
6. Insert into `email_otps` with `expires_at = now + 10 min`
7. Send email via SMTP
8. Return success

**`/auth/verify-otp` logic:**
1. Look up the most recent unexpired, unverified OTP for this device + email
2. If not found → error "No pending verification"
3. Increment `attempts`
4. If `attempts > 5` → invalidate OTP, error "Too many attempts"
5. If `otp_code` doesn't match → error "Invalid code"
6. If expired → error "Code expired"
7. Set `email_verified = True` on the device
8. **Delete all `email_otps` rows for this device** — scrub emails from the DB after successful verification
9. Return success + new JWT token (so the token now reflects verified status)

### 4. Backend service changes

- Add OTP generation logic to `AuthService` or create a new `OTPService`
- Add `EmailService` for SMTP operations
- Keep existing `get_current_device` and `require_verified_device` as-is — they still work since we're still setting `email_verified` on the device

### 5. One-time sign-in: never re-prompt after initial OTP verification

The user must only see the Welcome screen and OTP flow **once, ever** (exception: Android reinstall, which wipes app data). After the initial verification, every subsequent app launch should silently authenticate without user interaction.

#### 5a. Long-lived JWT tokens (backend)

**`config.py`** — change `access_token_expire_hours` from `24 * 7` (1 week) to `24 * 365 * 10` (10 years). This is acceptable for a low-risk campus parking app where the "account" is just a device ID — there are no passwords or sensitive personal data at stake.

#### 5b. Silent token refresh on `/auth/register` (backend)

The `/auth/register` endpoint already does get-or-create — if the device exists, it returns it. **It already issues a fresh token every time it's called.** This means the apps can call `/auth/register` on every launch to silently get a new long-lived token, with no user interaction required. The device's `email_verified` status is preserved in the DB, so re-registering doesn't reset verification.

No backend code changes needed for this — just ensure the apps call `register()` on launch when the existing token is present (to refresh it), not only when first onboarding.

#### 5c. Resilient auth check on app launch (iOS + Android)

Currently, both apps call `getDeviceInfo()` on launch, and **if it fails for any reason** (expired token, network timeout, server down), they nuke all local auth state and force the user back to the Welcome screen. This is too aggressive.

**Fix for both platforms — change the startup flow to:**

1. If no local token exists → show Welcome screen (first-time user).
2. If a local token exists → call `/auth/register` with the stored `device_id`.
   - **Success** → save the fresh token, check `email_verified` on the response. If verified, go straight to main app. If not, show OTP screen (edge case: they registered but never finished verifying).
   - **Network error / timeout** → **do NOT clear auth state**. Use the existing local token optimistically and let the user into the app. Individual API calls will fail if the token is truly dead, but a transient network blip on launch should not lock the user out.
   - **401 from register** → this should never happen (register is unauthenticated), but if it does, clear state and show Welcome.

**iOS (`AppViewModel.swift`)** — replace `checkAuthAndLoad()`:
- Instead of calling `getDeviceInfo()` and clearing on failure, call `api.register()` to silently refresh the token.
- Only clear `keychain` and show Welcome if the device has no stored `device_id` at all (not just because a network call failed).

**Android (`AppViewModel.kt`)** — replace `checkAuthStatus()`:
- Same logic: call `repository.register()` to refresh token silently.
- On `Result.Error`, only clear state if the error is a definitive 401 — not on network timeouts.
- `AppRepository.register()` already calls `tokenRepository.getOrCreateDeviceId()` and saves the fresh token, so this works out of the box.

#### 5d. Never show "Get Started" / Welcome screen after first verification

Both apps should persist a local flag (e.g., `hasCompletedOnboarding`) independently of the auth token:

- **iOS**: Store `hasCompletedOnboarding = true` in `UserDefaults` after successful OTP verification. On launch, if this flag is `true`, skip the Welcome screen entirely — even if the token refresh is still in progress.
- **Android**: Store `hasCompletedOnboarding = true` in SharedPreferences after successful OTP verification. Same skip logic on launch.

This ensures the Welcome screen is shown exactly once, and the user goes straight to the main app on all subsequent launches.

### 6. iOS app changes (OTP UI)

**`EmailVerificationView.swift`** — convert to a two-step flow:

1. **Step 1 — Email input**: User enters email, taps "Send Code". Calls `POST /auth/send-otp`. On success, transition to step 2.
2. **Step 2 — OTP input**: Show a 6-digit code input field. User enters the code from their email, taps "Verify". Calls `POST /auth/verify-otp`. On success, proceed to main app.
3. Add a "Resend Code" button (with a cooldown timer, e.g., 30 seconds)

**`APIClient.swift`** — replace `verifyEmail()` with:
- `sendOTP(email:)` → calls `/auth/send-otp`
- `verifyOTP(email:code:)` → calls `/auth/verify-otp`

**`AppViewModel.swift`** — update auth flow:
- Add state for OTP step (`showOTPInput`, `otpEmail`, `canResend`, `resendCooldown`)
- `sendOTP()` and `verifyOTP()` methods replacing `verifyEmail()`

**`APIModels.swift`** — add new request/response models:
- `SendOTPRequest`, `SendOTPResponse`
- `VerifyOTPRequest`, `VerifyOTPResponse`

### 7. Android app changes (OTP UI)

The Android app mirrors the iOS flow using Jetpack Compose + Hilt + Retrofit. The same two-step OTP flow must be implemented here.

**`EmailVerificationScreen.kt`** — convert to a two-step flow:

1. **Step 1 — Email input** (current screen, mostly reusable): User enters email, taps "Submit". Instead of calling `onVerify(email)` directly, call a new `onSendOTP(email)` callback. On success, transition to step 2.
2. **Step 2 — OTP input**: Add a new Compose state/screen section showing a 6-digit code input (use `KeyboardType.Number`). User enters the code and taps "Verify". Calls `onVerifyOTP(email, code)`. On success, proceed to main app.
3. Add a "Resend Code" button with a 30-second cooldown timer.
4. The current `onVerify: (String) -> Unit` callback signature changes — either split into `onSendOTP` + `onVerifyOTP` callbacks, or manage the two-step state internally within the screen.

**`ApiService.kt`** — replace `verifyEmail()` with two new Retrofit endpoints:
```kotlin
@POST("auth/send-otp")
suspend fun sendOTP(@Body request: SendOTPRequest): Response<SendOTPResponse>

@POST("auth/verify-otp")
suspend fun verifyOTP(@Body request: VerifyOTPRequest): Response<VerifyOTPResponse>
```

**`ApiModels.kt`** — add new data classes:
```kotlin
data class SendOTPRequest(
    val email: String,
    @SerializedName("device_id") val deviceId: String
)

data class SendOTPResponse(
    val success: Boolean,
    val message: String
)

data class VerifyOTPRequest(
    val email: String,
    @SerializedName("device_id") val deviceId: String,
    @SerializedName("otp_code") val otpCode: String
)

data class VerifyOTPResponse(
    val success: Boolean,
    val message: String,
    @SerializedName("email_verified") val emailVerified: Boolean
)
```

**`AppRepository.kt`** — replace `verifyEmail()` with:
- `sendOTP(email: String): Result<SendOTPResponse>` — calls `apiService.sendOTP(...)` with device ID from `tokenRepository`
- `verifyOTP(email: String, otpCode: String): Result<VerifyOTPResponse>` — calls `apiService.verifyOTP(...)` with device ID from `tokenRepository`

**`AppViewModel.kt`** — update auth flow:
- Add OTP-related fields to `AppUiState`:
  ```kotlin
  val otpStep: OTPStep = OTPStep.EMAIL_INPUT,  // EMAIL_INPUT or CODE_INPUT
  val otpEmail: String? = null,
  val resendCooldownSeconds: Int = 0
  ```
- Replace `verifyEmail()` with `sendOTP(email)` and `verifyOTP(code)` methods
- Add `resendOTP()` with cooldown timer logic (use `viewModelScope.launch` + `delay`)
- On successful OTP verification, set `isEmailVerified = true`, `showEmailVerification = false`, then call `loadInitialData()`

**`WelcomeScreen.kt` / `MainActivity.kt`** — update any navigation logic that references the old `verifyEmail` callback to use the new two-step flow.

---

## Migration Plan

Since the `devices` table already has `email_verified`, no changes to that table are needed. The only DB migration is adding the `email_otps` table.

For existing users who are already `email_verified = True`: they stay verified. The new OTP flow only applies to new verifications.

### Deployment order
1. Add `SMTP_EMAIL` and `SMTP_PASSWORD` secrets to GCP Secret Manager
2. Update `SECRET_NAMES` in `config.py` to include the new secrets
3. Deploy backend with new table + endpoints (old `/auth/verify-email` can be kept temporarily for backward compatibility)
4. Deploy iOS update with the new two-step verification UI
5. Deploy Android update with the new two-step verification UI
6. Remove old `/auth/verify-email` endpoint once all clients are updated

---

## Risks and Considerations

- **Gmail SMTP rate limits**: Gmail allows ~500 emails/day for regular accounts. For a campus app this is likely fine, but monitor usage. If it becomes an issue, consider SendGrid or Mailgun.
- **App Passwords**: The Gmail account needs 2FA enabled to generate an App Password. Store it in GCP Secret Manager, never in code.
- **OTP brute force**: The 5-attempt limit + 10-minute expiry mitigate this. Per-email rate limiting (5/hr) prevents inbox-spamming across multiple device IDs.
- **Device UUID security**: Both platforms generate RFC 4122 v4 random UUIDs (122 bits of randomness) — effectively unguessable. No additional device-secret is needed. iOS uses `UUID().uuidString`, Android uses `UUID.randomUUID().toString()`.
- **Email deliverability**: Gmail SMTP emails might land in spam. The email content should be short and avoid spammy language. Consider adding a note in the app: "Check your spam folder."
- **Existing device model is preserved**: We're not refactoring away from device-based identity — just adding real email verification on top of it. A future "user accounts" migration could build on this.
- **Android reinstall = re-verification**: SharedPreferences are wiped on uninstall, so Android users will need to re-verify after reinstalling. This is acceptable. iOS Keychain persists across reinstalls, so iOS users are unaffected.
- **10-year token expiry**: Functionally permanent, but not literally — avoids edge cases with `exp: None` in JWT libraries. The silent refresh on each launch means tokens stay fresh regardless.

---

## Communication

- **Ask questions if something is unclear.** If instructions are ambiguous, ask rather than guess.
- **Flag risks before acting.** If an approach could break existing functionality, say so before implementing.
- **Show your work incrementally.** For multi-file changes, explain what you're changing and why before writing code.
