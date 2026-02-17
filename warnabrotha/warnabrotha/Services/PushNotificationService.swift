//
//  PushNotificationService.swift
//  warnabrotha
//
//  Coordinates APNs permission requests, token registration, and backend sync.
//

import UIKit
import UserNotifications

@MainActor
class PushNotificationService {
    static let shared = PushNotificationService()

    private init() {}

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
        KeychainService.shared.savePushToken(token)
        do {
            try await APIClient.shared.updateDevice(pushToken: token, isPushEnabled: true)
        } catch {
            print("Failed to send push token to backend: \(error)")
        }
    }
}
