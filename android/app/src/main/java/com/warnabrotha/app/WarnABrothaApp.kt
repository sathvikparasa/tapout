package com.warnabrotha.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class WarnABrothaApp : Application() {
    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        val channel = NotificationChannel(
            "taps_alerts",
            "TAPS Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Alerts when TAPS has been spotted at your parking lot"
        }
        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.createNotificationChannel(channel)
    }
}
