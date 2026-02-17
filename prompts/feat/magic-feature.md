# Magic feature

A requirement of this project is to include a feature that the user feels is "like magic". We have decided on that feature to be the notification taking the user to the AMP parking app. So the behavior is that when the user clicks on the notification, they are taken straight to the AMP parking app.

## Implementation Plan

**Target app:** AMP Park (`com.aimsparking.aimsmobilepay`) — the app UC Davis uses for AggiePark parking payments.

### Files to Modify

| File | Change |
|------|--------|
| `android/app/src/main/AndroidManifest.xml` | Add `<queries>` block for package visibility |
| `android/app/src/main/java/.../data/service/FCMService.kt` | Replace intent logic with AMP app launch + fallbacks |
| `android/app/src/test/java/.../data/service/FCMServiceTest.kt` | Add tests for the new intent resolution |

No Gradle or backend changes needed.

### Step 1: AndroidManifest.xml — Add `<queries>`

Android 11+ (API 30+) requires declaring which external packages the app needs to query. Without this, `packageManager.getLaunchIntentForPackage()` returns `null` even if AMP Park is installed. Our `targetSdk = 35`, so this is mandatory.

Insert between `<uses-feature>` and `<application>`:

```xml
<queries>
    <package android:name="com.aimsparking.aimsmobilepay" />
    <intent>
        <action android:name="android.intent.action.VIEW" />
        <data android:scheme="market" />
    </intent>
</queries>
```

### Step 2: FCMService.kt — External App Launch Logic

Extract intent creation into a `createNotificationIntent()` method with a 4-tier fallback:

1. **AMP Park installed** → launch via `packageManager.getLaunchIntentForPackage()`
2. **Not installed, Play Store available** → open `market://details?id=com.aimsparking.aimsmobilepay`
3. **No Play Store** → open web URL `https://play.google.com/store/apps/details?id=...`
4. **Nothing available** → fall back to `MainActivity` with original extras preserved

### Step 3: FCMServiceTest.kt — Add Tests

3 new test cases using Robolectric shadow package manager:

1. AMP installed → verify intent targets AMP package
2. AMP not installed, Play Store available → verify `market://` intent
3. Nothing available → verify MainActivity fallback with extras

### Verification

1. `./gradlew assembleDebug` — compile check
2. `./gradlew testDebugUnitTest --tests "...FCMServiceTest"` — run tests
3. Manual test on device with/without AMP Park installed

