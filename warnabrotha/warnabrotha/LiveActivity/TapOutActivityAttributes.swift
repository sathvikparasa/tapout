//
//  TapOutActivityAttributes.swift
//  warnabrotha / TapOutWidget
//
//  Shared ActivityKit attributes model.
//  Target membership: BOTH warnabrotha AND TapOutWidget.
//  (Set in Xcode File Inspector → Target Membership.)
//

import ActivityKit
import Foundation

struct TapOutActivityAttributes: ActivityAttributes {
    // Static — set at activity start, never changes mid-session
    let lotName: String       // e.g. "Hutchison Field"
    let lotCode: String       // e.g. "HUTCH"
    let checkedInAt: Date     // parsed from ParkingSession.checkedInAt

    // Dynamic — updated via APNs push-to-update or local AppViewModel call
    struct ContentState: Codable, Hashable {
        var riskLevel: String             // "LOW", "MEDIUM", "HIGH"
        var probability: Double           // 0.0–1.0
        var lastSightingMinutesAgo: Int?  // nil = no recent sightings in 3h window
        var recentSightingsCount: Int
    }
}
