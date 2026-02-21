//
//  warnabrothaApp.swift
//  warnabrotha
//
//  Created by Abhinav Tata on 1/20/26.
//

import SwiftUI
import UserNotifications

// MARK: - Parking Payment App Preference

enum ParkingPaymentApp: String {
    case ampPark    = "ampPark"
    case honkMobile = "honkMobile"

    static var preferred: ParkingPaymentApp {
        let raw = UserDefaults.standard.string(forKey: "preferredParkingApp") ?? ""
        return ParkingPaymentApp(rawValue: raw) ?? .ampPark  // Default: AMP Park
    }

    static func setPreferred(_ app: ParkingPaymentApp) {
        UserDefaults.standard.set(app.rawValue, forKey: "preferredParkingApp")
    }

    /// URL schemes to try first (opens the app if installed)
    var candidateSchemes: [String] {
        switch self {
        case .ampPark:    return ["amppark://", "aimsmobilepay://"]
        case .honkMobile: return ["honkmobile://"]
        }
    }

    /// App Store deep link (opens App Store app directly)
    var appStoreURL: String {
        switch self {
        case .ampPark:    return "itms-apps://itunes.apple.com/app/id1475971159"
        case .honkMobile: return "itms-apps://itunes.apple.com/app/id915957520"
        }
    }

    /// Web fallback
    var webURL: String {
        switch self {
        case .ampPark:    return "https://apps.apple.com/us/app/amp-park/id1475971159"
        case .honkMobile: return "https://parking.honkmobile.com/signup"
        }
    }
}

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        Task {
            await PushNotificationService.shared.sendTokenToBackend(token)
        }
    }

    func application(_ application: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("APNs registration failed: \(error.localizedDescription)")
    }

    // Show notifications even when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .badge])
    }

    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo

        if let type = userInfo["type"] as? String, type == "TAPS_SPOTTED" {
            openParkingPaymentApp()
        }

        completionHandler()
    }

    private func openParkingPaymentApp() {
        let app = ParkingPaymentApp.preferred

        // Tier 1: Open the app directly if installed
        for scheme in app.candidateSchemes {
            if let url = URL(string: scheme), UIApplication.shared.canOpenURL(url) {
                UIApplication.shared.open(url)
                return
            }
        }

        // Tier 2: Open App Store page
        if let url = URL(string: app.appStoreURL) {
            UIApplication.shared.open(url)
            return
        }

        // Tier 3: Web fallback
        if let url = URL(string: app.webURL) {
            UIApplication.shared.open(url)
        }
    }
}

@main
struct warnabrothaApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
