//
//  TapOutLiveActivityWidget.swift
//  TapOutWidget
//
//  Live Activity UI: lock screen banner + Dynamic Island.
//  Target membership: TapOutWidget only.
//
//  SETUP:
//  1. In Xcode: File → New → Target → Widget Extension
//     - Product Name: TapOutWidget
//     - Bundle ID: com.warnabrotha.tapout.TapOutWidget
//     - Uncheck "Include Configuration Intent" and "Include Live Activity"
//  2. Delete the auto-generated TapOutWidget.swift body and add this file.
//  3. Add TapOutActivityAttributes.swift to BOTH targets in File Inspector.
//  4. Add NSSupportsLiveActivities to TapOutWidget's Info.plist.
//

import ActivityKit
import SwiftUI
import WidgetKit

// MARK: - Local color constants (mirror of AppTheme — cannot import across targets)

private extension Color {
    static let tapAccent    = Color(hex: "9CAF88")  // sage green
    static let tapDanger    = Color(hex: "EF4444")  // HIGH risk red
    static let tapWarning   = Color(hex: "FFD54F")  // MEDIUM risk yellow
    static let tapSuccess   = Color(hex: "22C55E")  // LOW risk green
    static let tapPrimary   = Color(hex: "0F172A")
    static let tapSecondary = Color(hex: "64748B")
    static let tapBG        = Color(hex: "F7F7F7")

    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = (int >> 16) & 0xFF
        let g = (int >> 8)  & 0xFF
        let b =  int        & 0xFF
        self.init(.sRGB,
                  red: Double(r) / 255,
                  green: Double(g) / 255,
                  blue: Double(b) / 255,
                  opacity: 1)
    }
}

// MARK: - Helpers

private func riskColor(for level: String) -> Color {
    switch level {
    case "HIGH":   return .tapDanger
    case "MEDIUM": return .tapWarning
    case "LOW":    return .tapSuccess
    default:       return .tapSecondary
    }
}

private func riskBars(for level: String) -> Int {
    switch level {
    case "HIGH":   return 3
    case "MEDIUM": return 2
    default:       return 1
    }
}

private func formattedDuration(from start: Date) -> String {
    let seconds = Int(Date().timeIntervalSince(start))
    let h = seconds / 3600
    let m = (seconds % 3600) / 60
    return h > 0 ? "\(h)h \(m)m" : "\(m)m"
}

// MARK: - Widget Bundle Entry Point

@main
struct TapOutWidgetBundle: WidgetBundle {
    var body: some Widget {
        TapOutLiveActivityWidget()
    }
}

// MARK: - Live Activity Widget

struct TapOutLiveActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: TapOutActivityAttributes.self) { context in
            // Lock Screen / StandBy expanded view
            TapOutLockScreenView(context: context)
        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded (long-press)
                DynamicIslandExpandedRegion(.leading) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(context.attributes.lotCode)
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(.tapAccent)
                        Text("Parked \(formattedDuration(from: context.attributes.checkedInAt))")
                            .font(.system(size: 11))
                            .foregroundColor(.tapSecondary)
                    }
                    .padding(.leading, 4)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text(context.state.riskLevel)
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(riskColor(for: context.state.riskLevel))
                        Text("\(Int(context.state.probability * 100))%")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(riskColor(for: context.state.riskLevel))
                    }
                    .padding(.trailing, 4)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    if let mins = context.state.lastSightingMinutesAgo {
                        Text("⚠️ TAPS spotted \(mins == 0 ? "just now" : "\(mins)m ago")")
                            .font(.system(size: 12))
                            .foregroundColor(.tapDanger)
                    } else {
                        Text("No recent sightings")
                            .font(.system(size: 12))
                            .foregroundColor(.tapSecondary)
                    }
                }
            } compactLeading: {
                // Compact leading — lot code pill
                Text(context.attributes.lotCode)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.tapAccent)
                    .padding(.horizontal, 6)
                    .background(Capsule().fill(Color.tapAccent.opacity(0.15)))
            } compactTrailing: {
                // Compact trailing — signal bars
                HStack(spacing: 2) {
                    let active   = riskBars(for: context.state.riskLevel)
                    let barColor = riskColor(for: context.state.riskLevel)
                    ForEach(0..<3, id: \.self) { i in
                        RoundedRectangle(cornerRadius: 1)
                            .fill(i < active ? barColor : Color.gray.opacity(0.3))
                            .frame(width: 4, height: CGFloat([8, 12, 16][i]))
                    }
                }
            } minimal: {
                // Minimal — risk dot when competing with another activity
                Circle()
                    .fill(riskColor(for: context.state.riskLevel))
                    .frame(width: 10, height: 10)
            }
        }
    }
}

// MARK: - Lock Screen View

struct TapOutLockScreenView: View {
    let context: ActivityViewContext<TapOutActivityAttributes>

    var body: some View {
        VStack(spacing: 0) {
            // Main row
            HStack(spacing: 16) {
                // Left: lot name + duration
                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        Text("TapOut")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundColor(.tapPrimary)
                        // LIVE badge
                        HStack(spacing: 3) {
                            Circle()
                                .fill(Color.tapSuccess)
                                .frame(width: 5, height: 5)
                            Text("LIVE")
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(.tapSuccess)
                        }
                        .padding(.horizontal, 7)
                        .padding(.vertical, 3)
                        .background(Capsule().fill(Color.tapSuccess.opacity(0.12)))
                    }
                    Text(context.attributes.lotName)
                        .font(.system(size: 15, weight: .bold))
                        .foregroundColor(.tapPrimary)
                    Text("Parked \(formattedDuration(from: context.attributes.checkedInAt))")
                        .font(.system(size: 12))
                        .foregroundColor(.tapSecondary)
                }

                Spacer()

                // Right: signal bars + risk label + probability
                VStack(alignment: .trailing, spacing: 4) {
                    HStack(alignment: .bottom, spacing: 2) {
                        let active   = riskBars(for: context.state.riskLevel)
                        let barColor = riskColor(for: context.state.riskLevel)
                        ForEach(0..<3, id: \.self) { i in
                            RoundedRectangle(cornerRadius: 2)
                                .fill(i < active ? barColor : Color.gray.opacity(0.25))
                                .frame(width: 6, height: CGFloat([10, 18, 26][i]))
                        }
                    }
                    Text("\(context.state.riskLevel) RISK")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(riskColor(for: context.state.riskLevel))
                    Text("\(Int(context.state.probability * 100))%")
                        .font(.system(size: 20, weight: .heavy))
                        .foregroundColor(riskColor(for: context.state.riskLevel))
                }
            }
            .padding(16)
            .background(Color.tapBG)

            // Sighting strip (only shown when there are recent sightings)
            if let mins = context.state.lastSightingMinutesAgo {
                Divider()
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.tapDanger)
                        .font(.system(size: 11))
                    Text("TAPS spotted \(mins == 0 ? "just now" : "\(mins) min ago")")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.tapDanger)
                    Spacer()
                    Text("\(context.state.recentSightingsCount) report\(context.state.recentSightingsCount == 1 ? "" : "s")")
                        .font(.system(size: 11))
                        .foregroundColor(.tapSecondary)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.tapDanger.opacity(0.06))
            }
        }
    }
}
