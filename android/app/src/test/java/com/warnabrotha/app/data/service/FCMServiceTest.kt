package com.warnabrotha.app.data.service

import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.ResolveInfo
import com.google.firebase.messaging.RemoteMessage
import com.warnabrotha.app.MainActivity
import com.warnabrotha.app.data.api.ApiService
import com.warnabrotha.app.data.model.DeviceUpdate
import com.warnabrotha.app.data.repository.TokenRepository
import dagger.hilt.android.EntryPointAccessors
import io.mockk.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows
import org.robolectric.annotation.Config
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class FCMServiceTest {

    private lateinit var fcmService: FCMService
    private val mockTokenRepository: TokenRepository = mockk(relaxed = true)
    private val mockApiService: ApiService = mockk(relaxed = true)

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        mockkStatic(EntryPointAccessors::class)
        val mockEntryPoint = mockk<FCMService.FCMServiceEntryPoint> {
            every { tokenRepository() } returns mockTokenRepository
            every { apiService() } returns mockApiService
        }
        every {
            EntryPointAccessors.fromApplication(any(), FCMService.FCMServiceEntryPoint::class.java)
        } returns mockEntryPoint

        fcmService = Robolectric.buildService(FCMService::class.java).create().get()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
        unmockkStatic(EntryPointAccessors::class)
    }

    private fun buildRemoteMessage(
        title: String? = "TAPS Alert",
        body: String? = "TAPS spotted at Lot A",
        data: Map<String, String> = mapOf("type" to "TAPS_SPOTTED", "parking_lot_id" to "1")
    ): RemoteMessage {
        val remoteMessage = mockk<RemoteMessage>(relaxed = true)
        val notification = if (title != null && body != null) {
            mockk<RemoteMessage.Notification> {
                every { getTitle() } returns title
                every { getBody() } returns body
            }
        } else null
        every { remoteMessage.notification } returns notification
        every { remoteMessage.data } returns data
        return remoteMessage
    }

    // ── onNewToken ──

    @Test
    fun onNewToken_savesTokenLocally() {
        fcmService.onNewToken("new-token")
        verify { mockTokenRepository.savePushToken("new-token") }
    }

    @Test
    fun onNewToken_syncsWithBackend() {
        fcmService.onNewToken("new-token")
        coVerify {
            mockApiService.updateDevice(DeviceUpdate(pushToken = "new-token", isPushEnabled = true))
        }
    }

    @Test
    fun onNewToken_backendFailure_doesNotCrash() {
        coEvery {
            mockApiService.updateDevice(any())
        } throws IOException("Network error")

        // Should not throw
        fcmService.onNewToken("new-token")

        // savePushToken should still be called
        verify { mockTokenRepository.savePushToken("new-token") }
    }

    // ── onMessageReceived ──

    @Test
    fun onMessageReceived_postsNotification() {
        val message = buildRemoteMessage()
        fcmService.onMessageReceived(message)

        val shadowManager = org.robolectric.Shadows.shadowOf(
            RuntimeEnvironment.getApplication()
                .getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        )
        assertEquals(1, shadowManager.activeNotifications.size)
    }

    @Test
    fun onMessageReceived_correctTitleAndBody() {
        val message = buildRemoteMessage(title = "Alert!", body = "TAPS at Lot B")
        fcmService.onMessageReceived(message)

        val shadowManager = org.robolectric.Shadows.shadowOf(
            RuntimeEnvironment.getApplication()
                .getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        )
        val notification = shadowManager.activeNotifications.first().notification
        // NotificationCompat stores title/body in extras
        assertEquals("Alert!", notification.extras.getString("android.title"))
        assertEquals("TAPS at Lot B", notification.extras.getString("android.text"))
    }

    @Test
    fun onMessageReceived_pendingIntentHasExtras() {
        val message = buildRemoteMessage(
            data = mapOf("type" to "TAPS_SPOTTED", "parking_lot_id" to "42")
        )
        fcmService.onMessageReceived(message)

        val shadowManager = org.robolectric.Shadows.shadowOf(
            RuntimeEnvironment.getApplication()
                .getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        )
        val notification = shadowManager.activeNotifications.first().notification
        val pendingIntent = notification.contentIntent
        val shadowPendingIntent = org.robolectric.Shadows.shadowOf(pendingIntent)
        val intent = shadowPendingIntent.savedIntent

        assertEquals("TAPS_SPOTTED", intent.getStringExtra("notification_type"))
        assertEquals("42", intent.getStringExtra("parking_lot_id"))
    }

    @Test
    fun onMessageReceived_nullNotification_noPost() {
        val message = buildRemoteMessage(title = null, body = null)
        fcmService.onMessageReceived(message)

        val shadowManager = org.robolectric.Shadows.shadowOf(
            RuntimeEnvironment.getApplication()
                .getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        )
        assertEquals(0, shadowManager.activeNotifications.size)
    }

    // ── createNotificationIntent ──

    @Test
    fun createNotificationIntent_ampInstalled_returnsAmpLaunchIntent() {
        val shadowPm = Shadows.shadowOf(RuntimeEnvironment.getApplication().packageManager)
        val ampLaunchIntent = Intent(Intent.ACTION_MAIN).apply {
            addCategory(Intent.CATEGORY_LAUNCHER)
            setPackage(FCMService.AMP_PARK_PACKAGE)
            setClassName(FCMService.AMP_PARK_PACKAGE, "${FCMService.AMP_PARK_PACKAGE}.MainActivity")
        }
        val resolveInfo = ResolveInfo().apply {
            activityInfo = ActivityInfo().apply {
                packageName = FCMService.AMP_PARK_PACKAGE
                name = "${FCMService.AMP_PARK_PACKAGE}.MainActivity"
            }
        }
        shadowPm.addResolveInfoForIntent(ampLaunchIntent, resolveInfo)

        val intent = fcmService.createNotificationIntent("TAPS_SPOTTED", "1")
        assertEquals(FCMService.AMP_PARK_PACKAGE, intent.`package`)
    }

    @Test
    fun createNotificationIntent_ampNotInstalled_returnsPlayStoreIntent() {
        val shadowPm = Shadows.shadowOf(RuntimeEnvironment.getApplication().packageManager)
        // Register only the Play Store market:// handler
        val marketIntent = Intent(
            Intent.ACTION_VIEW,
            android.net.Uri.parse("market://details?id=${FCMService.AMP_PARK_PACKAGE}")
        )
        val resolveInfo = ResolveInfo().apply {
            activityInfo = ActivityInfo().apply {
                packageName = "com.android.vending"
                name = "com.android.vending.AssetBrowserActivity"
            }
        }
        shadowPm.addResolveInfoForIntent(marketIntent, resolveInfo)

        val intent = fcmService.createNotificationIntent("TAPS_SPOTTED", "1")
        assertEquals(Intent.ACTION_VIEW, intent.action)
        assertEquals("market", intent.data?.scheme)
    }

    @Test
    fun createNotificationIntent_nonTapsType_goesToMainActivity() {
        // Even if AMP Park is installed, non-TAPS notifications should open our app
        val shadowPm = Shadows.shadowOf(RuntimeEnvironment.getApplication().packageManager)
        val ampLaunchIntent = Intent(Intent.ACTION_MAIN).apply {
            addCategory(Intent.CATEGORY_LAUNCHER)
            setPackage(FCMService.AMP_PARK_PACKAGE)
            setClassName(FCMService.AMP_PARK_PACKAGE, "${FCMService.AMP_PARK_PACKAGE}.MainActivity")
        }
        val resolveInfo = ResolveInfo().apply {
            activityInfo = ActivityInfo().apply {
                packageName = FCMService.AMP_PARK_PACKAGE
                name = "${FCMService.AMP_PARK_PACKAGE}.MainActivity"
            }
        }
        shadowPm.addResolveInfoForIntent(ampLaunchIntent, resolveInfo)

        val intent = fcmService.createNotificationIntent("reminder", "5")
        assertEquals(
            MainActivity::class.java.name,
            intent.component?.className
        )
        assertEquals("reminder", intent.getStringExtra("notification_type"))
        assertEquals("5", intent.getStringExtra("parking_lot_id"))
    }

    @Test
    fun createNotificationIntent_nothingAvailable_fallsBackToMainActivity() {
        // No packages registered — should fall back to MainActivity
        val intent = fcmService.createNotificationIntent("TAPS_SPOTTED", "42")
        assertEquals(
            MainActivity::class.java.name,
            intent.component?.className
        )
        assertEquals("TAPS_SPOTTED", intent.getStringExtra("notification_type"))
        assertEquals("42", intent.getStringExtra("parking_lot_id"))
    }
}
