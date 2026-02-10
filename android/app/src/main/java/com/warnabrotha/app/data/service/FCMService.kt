package com.warnabrotha.app.data.service

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
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

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        val title = message.notification?.title ?: return
        val body = message.notification?.body ?: return
        val type = message.data["type"]
        val lotId = message.data["parking_lot_id"]

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("notification_type", type)
            putExtra("parking_lot_id", lotId)
        }

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
