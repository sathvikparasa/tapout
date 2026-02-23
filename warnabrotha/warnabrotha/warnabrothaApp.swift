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
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.openParkingPaymentApp()
            }
        }

        completionHandler()
    }

    private func openParkingPaymentApp() {
        let app = ParkingPaymentApp.preferred
        let schemes = app.candidateSchemes.compactMap { URL(string: $0) }
        tryOpenURLs(schemes, fallbackAppStore: app.appStoreURL, fallbackWeb: app.webURL)
    }

    private func tryOpenURLs(_ urls: [URL], fallbackAppStore: String, fallbackWeb: String) {
        guard let url = urls.first else {
            // All schemes failed — try App Store
            if let appStoreURL = URL(string: fallbackAppStore) {
                UIApplication.shared.open(appStoreURL) { success in
                    if !success, let webURL = URL(string: fallbackWeb) {
                        UIApplication.shared.open(webURL)
                    }
                }
            }
            return
        }

        UIApplication.shared.open(url) { success in
            if success { return }
            // This scheme failed — try the next one
            self.tryOpenURLs(Array(urls.dropFirst()), fallbackAppStore: fallbackAppStore, fallbackWeb: fallbackWeb)
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
