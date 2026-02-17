package com.warnabrotha.app.data.service

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.warnabrotha.app.MainActivity
import com.warnabrotha.app.R
import com.warnabrotha.app.data.api.ApiService
import com.warnabrotha.app.data.model.DeviceUpdate
import com.warnabrotha.app.data.repository.TokenRepository
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class FCMService : FirebaseMessagingService() {

    companion object {
        const val AMP_PARK_PACKAGE = "com.aimsparking.aimsmobilepay"
        private const val PLAY_STORE_MARKET_URI = "market://details?id=$AMP_PARK_PACKAGE"
        private const val PLAY_STORE_WEB_URL =
            "https://play.google.com/store/apps/details?id=$AMP_PARK_PACKAGE"
    }

    @EntryPoint
    @InstallIn(SingletonComponent::class)
    interface FCMServiceEntryPoint {
        fun tokenRepository(): TokenRepository
        fun apiService(): ApiService
    }

    private fun getEntryPoint(): FCMServiceEntryPoint {
        return EntryPointAccessors.fromApplication(
            applicationContext,
            FCMServiceEntryPoint::class.java
        )
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        val entryPoint = getEntryPoint()
        val tokenRepository = entryPoint.tokenRepository()
        val apiService = entryPoint.apiService()

        tokenRepository.savePushToken(token)

        CoroutineScope(Dispatchers.IO).launch {
            try {
                apiService.updateDevice(DeviceUpdate(pushToken = token, isPushEnabled = true))
            } catch (e: Exception) {
                android.util.Log.e("FCMService", "Failed to sync push token with backend", e)
            }
        }
    }

    internal fun createNotificationIntent(type: String?, lotId: String?): Intent {
        // Tier 1: AMP Park app is installed — launch it directly
        packageManager.getLaunchIntentForPackage(AMP_PARK_PACKAGE)?.let { ampIntent ->
            ampIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            return ampIntent
        }

        // Tier 2: Open Play Store via market:// URI
        val marketIntent = Intent(Intent.ACTION_VIEW, Uri.parse(PLAY_STORE_MARKET_URI))
        if (marketIntent.resolveActivity(packageManager) != null) {
            marketIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            return marketIntent
        }

        // Tier 3: Open Play Store web URL (for devices without Play Store)
        val webIntent = Intent(Intent.ACTION_VIEW, Uri.parse(PLAY_STORE_WEB_URL))
        if (webIntent.resolveActivity(packageManager) != null) {
            webIntent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            return webIntent
        }

        // Tier 4: Fall back to our own MainActivity with original extras
        return Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("notification_type", type)
            putExtra("parking_lot_id", lotId)
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        val title = message.notification?.title ?: return
        val body = message.notification?.body ?: return
        val type = message.data["type"]
        val lotId = message.data["parking_lot_id"]

        val intent = createNotificationIntent(type, lotId)

        val pendingIntent = PendingIntent.getActivity(
            this,
            System.currentTimeMillis().toInt(),
            intent,
            PendingIntent.FLAG_ONE_SHOT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, "taps_alerts")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        val notificationManager =
            getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
