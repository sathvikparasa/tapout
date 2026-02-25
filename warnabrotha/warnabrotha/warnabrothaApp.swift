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

    /// URL to open when a TAPS notification is tapped
    var redirectURL: String {
        switch self {
        case .ampPark:
            // No URL scheme or universal links — go straight to App Store
            return "itms-apps://itunes.apple.com/app/id1475971159"
        case .honkMobile:
            // Universal link — opens Honk Mobile app if installed, Safari otherwise
            return "https://honkmobile.com/home"
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
        guard let url = URL(string: app.redirectURL) else { return }

        switch app {
        case .ampPark:
            UIApplication.shared.open(url)
        case .honkMobile:
            // universalLinksOnly ensures the app opens directly regardless of default browser.
            // If Honk Mobile isn't installed, success == false → fall back to App Store.
            UIApplication.shared.open(url, options: [.universalLinksOnly: true]) { success in
                if !success, let appStoreURL = URL(string: "itms-apps://itunes.apple.com/app/id816255029") {
                    UIApplication.shared.open(appStoreURL)
                }
            }
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
