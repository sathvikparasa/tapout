//
//  LiveActivityService.swift
//  warnabrotha
//
//  Manages the TapOut Live Activity lifecycle: start on check-in,
//  update when risk data changes, end on check-out, recover on relaunch.
//

import ActivityKit
import Foundation

@MainActor
class LiveActivityService {
    static let shared = LiveActivityService()
    private init() {}

    private var currentActivity: Activity<TapOutActivityAttributes>?

    // MARK: - Start

    func start(session: ParkingSession, prediction: PredictionResponse,
               lastSightingMinutesAgo: Int?, recentSightingsCount: Int) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        // End any stale activities from a previous session
        await endAll()

        let checkedInDate = parseCheckedInDate(session.checkedInAt)

        let attributes = TapOutActivityAttributes(
            lotName: session.parkingLotName,
            lotCode: session.parkingLotCode,
            checkedInAt: checkedInDate
        )
        let state = TapOutActivityAttributes.ContentState(
            riskLevel: prediction.riskLevel,
            probability: prediction.probability,
            lastSightingMinutesAgo: lastSightingMinutesAgo,
            recentSightingsCount: recentSightingsCount
        )
        do {
            let activity = try Activity.request(
                attributes: attributes,
                content: .init(state: state, staleDate: Date().addingTimeInterval(300)),
                pushType: .token  // Required: enables APNs push-to-update
            )
            currentActivity = activity
            observePushToken(for: activity)
        } catch {
            print("LiveActivity start failed: \(error)")
        }
    }

    // MARK: - Update (local — called when app is in foreground)

    func update(prediction: PredictionResponse, lastSightingMinutesAgo: Int?,
                recentSightingsCount: Int) async {
        guard let activity = currentActivity else { return }
        let state = TapOutActivityAttributes.ContentState(
            riskLevel: prediction.riskLevel,
            probability: prediction.probability,
            lastSightingMinutesAgo: lastSightingMinutesAgo,
            recentSightingsCount: recentSightingsCount
        )
        await activity.update(.init(state: state, staleDate: Date().addingTimeInterval(300)))
    }

    // MARK: - End

    func end() async {
        guard let activity = currentActivity else { return }
        await activity.end(nil, dismissalPolicy: .immediate)
        currentActivity = nil
        // Clear the stored activity push token from the backend
        try? await APIClient.shared.updateActivityPushToken(nil)
    }

    // MARK: - Recovery on app launch

    /// Called after loadInitialData() if the user is still parked.
    /// Attaches to an existing running activity (if the app was killed while parked)
    /// or starts a fresh one.
    func recoverIfNeeded(session: ParkingSession, prediction: PredictionResponse,
                         lastSightingMinutesAgo: Int?, recentSightingsCount: Int) async {
        if let existing = Activity<TapOutActivityAttributes>.activities.first {
            // Re-attach to the already-running activity
            currentActivity = existing
            observePushToken(for: existing)
            // Push fresh data into it
            await update(prediction: prediction,
                         lastSightingMinutesAgo: lastSightingMinutesAgo,
                         recentSightingsCount: recentSightingsCount)
        } else {
            // No running activity — start fresh
            await start(session: session, prediction: prediction,
                        lastSightingMinutesAgo: lastSightingMinutesAgo,
                        recentSightingsCount: recentSightingsCount)
        }
    }

    // MARK: - Private helpers

    private func endAll() async {
        for activity in Activity<TapOutActivityAttributes>.activities {
            await activity.end(nil, dismissalPolicy: .immediate)
        }
        currentActivity = nil
    }

    /// Observes push token changes and syncs them to the backend.
    private func observePushToken(for activity: Activity<TapOutActivityAttributes>) {
        Task {
            for await pushTokenData in activity.pushTokenUpdates {
                let token = pushTokenData.map { String(format: "%02x", $0) }.joined()
                try? await APIClient.shared.updateActivityPushToken(token)
            }
        }
    }

    /// Parses an ISO8601 date string from the backend, trying fractional seconds first.
    private func parseCheckedInDate(_ isoString: String) -> Date {
        let withFractional = ISO8601DateFormatter()
        withFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = withFractional.date(from: isoString) { return date }

        let plain = ISO8601DateFormatter()
        if let date = plain.date(from: isoString) { return date }

        // Should not reach here in practice
        print("LiveActivityService: failed to parse date '\(isoString)', using now")
        return Date()
    }
}
