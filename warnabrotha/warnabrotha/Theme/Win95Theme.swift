//
//  TapOutTheme.swift
//  TapOut
//
//  TapOut design system — sage green accent, clean modern UI.
//

import SwiftUI
import UIKit

// MARK: - Colors

struct AppColors {
    // Backgrounds
    static let background = Color(hex: "F7F7F7")
    static let cardBackground = Color.white
    static let darkBackground = Color(hex: "1E293B")

    // Text
    static let textPrimary = Color(hex: "0F172A")
    static let textSecondary = Color(hex: "64748B")
    static let textMuted = Color(hex: "94A3B8")
    static let textOnDark = Color.white

    // Accent (sage green)
    static let accent = Color(hex: "9CAF88")
    static let accentLight = Color(hex: "9CAF88").opacity(0.1)
    static let accentVeryLight = Color(hex: "9CAF88").opacity(0.05)
    static let accentMedium = Color(hex: "9CAF88").opacity(0.6)

    // Status
    static let danger = Color(hex: "E57373")
    static let dangerBright = Color(hex: "EF4444")
    static let dangerLight = Color(hex: "E57373").opacity(0.1)
    static let warning = Color(hex: "FFD54F")
    static let success = Color(hex: "22C55E")
    static let live = Color(hex: "22C55E")

    // Borders & Dividers
    static let border = Color(hex: "E2E8F0")
    static let borderLight = Color(hex: "F1F5F9")
    static let pillBorder = Color(hex: "CBD5E1")

    // Overlays
    static let overlayDark = Color(hex: "2D2D27").opacity(0.4)
    static let overlayLight = Color.white.opacity(0.8)
    static let frosted = Color.white.opacity(0.9)
}

// MARK: - Color Extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 6:
            (a, r, g, b) = (255, (int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = ((int >> 24) & 0xFF, (int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Typography

struct AppFont: ViewModifier {
    enum Family {
        case primary   // Plus Jakarta Sans
        case display   // DM Sans
    }

    let family: Family
    let size: CGFloat
    let weight: Font.Weight

    func body(content: Content) -> some View {
        content.font(font)
    }

    private var font: Font {
        // Use system font with matching weight — swap to custom fonts when bundled
        switch family {
        case .primary:
            return .system(size: size, weight: weight, design: .default)
        case .display:
            return .system(size: size, weight: .heavy, design: .default)
        }
    }
}

extension View {
    func appFont(size: CGFloat = 14, weight: Font.Weight = .regular) -> some View {
        modifier(AppFont(family: .primary, size: size, weight: weight))
    }

    func displayFont(size: CGFloat = 30) -> some View {
        modifier(AppFont(family: .display, size: size, weight: .heavy))
    }
}

// MARK: - Card Style

struct CardModifier: ViewModifier {
    var padding: CGFloat = 16
    var cornerRadius: CGFloat = 16

    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .fill(AppColors.cardBackground)
            )
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(AppColors.border, lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.05), radius: 2, y: 1)
    }
}

extension View {
    func cardStyle(padding: CGFloat = 16, cornerRadius: CGFloat = 16) -> some View {
        modifier(CardModifier(padding: padding, cornerRadius: cornerRadius))
    }
}

// MARK: - Primary Button

struct PrimaryButton: View {
    let title: String
    let icon: String?
    let color: Color
    let textColor: Color
    let action: () -> Void

    @State private var isPressed = false

    init(
        title: String,
        icon: String? = nil,
        color: Color = AppColors.accent,
        textColor: Color = .white,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.icon = icon
        self.color = color
        self.textColor = textColor
        self.action = action
    }

    var body: some View {
        Button(action: {
            let generator = UIImpactFeedbackGenerator(style: .medium)
            generator.impactOccurred()
            action()
        }) {
            HStack(spacing: 8) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 20, weight: .semibold))
                }
                Text(title)
                    .appFont(size: 14, weight: .bold)
            }
            .foregroundColor(textColor)
            .frame(maxWidth: .infinity)
            .frame(height: 56)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(color)
            )
            .scaleEffect(isPressed ? 0.97 : 1.0)
        }
        .buttonStyle(PlainButtonStyle())
        .animation(.easeInOut(duration: 0.1), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - Pill / Tag

struct PillView: View {
    let text: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(text)
                .appFont(size: 12, weight: .bold)
                .textCase(.uppercase)
                .tracking(0.5)
                .foregroundColor(isSelected ? .white : AppColors.textSecondary)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(
                    Capsule()
                        .fill(isSelected ? AppColors.accent : AppColors.cardBackground)
                )
                .overlay(
                    Capsule()
                        .stroke(isSelected ? Color.clear : AppColors.pillBorder, lineWidth: 1)
                )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Live Badge

struct LiveBadge: View {
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(AppColors.live)
                .frame(width: 6, height: 6)
            Text("LIVE")
                .appFont(size: 10, weight: .bold)
                .foregroundColor(AppColors.live)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(AppColors.live.opacity(0.1))
        )
    }
}

// MARK: - Risk Level Badge

struct RiskBadge: View {
    let level: String

    private var color: Color {
        switch level.uppercased() {
        case "HIGH": return AppColors.dangerBright
        case "MEDIUM": return AppColors.warning
        case "LOW": return AppColors.success
        default: return AppColors.textMuted
        }
    }

    private var textColor: Color {
        switch level.uppercased() {
        case "HIGH": return AppColors.dangerBright
        case "MEDIUM": return Color(hex: "F59E0B")
        case "LOW": return AppColors.success
        default: return AppColors.textMuted
        }
    }

    var body: some View {
        Text(level.uppercased())
            .appFont(size: 14, weight: .bold)
            .foregroundColor(textColor)
            .padding(.horizontal, 16)
            .padding(.vertical, 6)
            .background(
                Capsule()
                    .fill(color.opacity(0.15))
            )
    }
}

// MARK: - Dashboard Action Button (tall square, icon on top)

struct DashboardActionButton: View {
    let title: String
    let systemIcon: String
    let color: Color
    var textColor: Color = .white
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: {
            let generator = UIImpactFeedbackGenerator(style: .medium)
            generator.impactOccurred()
            action()
        }) {
            VStack(spacing: 12) {
                Image(systemName: systemIcon)
                    .font(.system(size: 48, weight: .regular))
                    .foregroundColor(textColor)

                Text(title)
                    .displayFont(size: 12)
                    .foregroundColor(textColor)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 196)
            .background(
                RoundedRectangle(cornerRadius: 40)
                    .fill(color)
            )
            .scaleEffect(isPressed ? 0.97 : 1.0)
        }
        .buttonStyle(PlainButtonStyle())
        .animation(.easeInOut(duration: 0.1), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
}

// MARK: - Risk Bar Chart (signal-strength bars)

struct RiskBarChart: View {
    let activeBars: Int // 1=LOW, 2=MEDIUM, 3=HIGH

    private let barWidth: CGFloat = 8
    private let gap: CGFloat = 3
    private let barHeights: [CGFloat] = [12, 24, 36]

    private let activeColors: [Color] = [
        Color(hex: "81C784"),  // green (LOW bar)
        Color(hex: "FFD54F"),  // yellow (MEDIUM bar)
        Color(hex: "EF4444"),  // red (HIGH bar)
    ]
    private let inactiveColor = Color(hex: "F2F2EB")

    var body: some View {
        HStack(alignment: .bottom, spacing: gap) {
            ForEach(0..<3) { index in
                RoundedRectangle(cornerRadius: 2)
                    .fill(index < activeBars ? activeColors[index] : inactiveColor)
                    .frame(width: barWidth, height: barHeights[index])
            }
        }
        .frame(width: 30, height: 40, alignment: .bottom)
    }
}

// MARK: - Stacked Card Edge

struct StackedCardEdge: View {
    var inset: CGFloat = 8

    var body: some View {
        RoundedRectangle(cornerRadius: 16)
            .fill(AppColors.cardBackground)
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(AppColors.border, lineWidth: 1)
            )
            .frame(height: 8)
            .padding(.horizontal, inset)
            .offset(y: -2)
    }
}

// MARK: - Notification Badge

struct NotificationBadge: View {
    let count: Int

    var body: some View {
        if count > 0 {
            Text("\(count)")
                .appFont(size: 10, weight: .bold)
                .foregroundColor(.white)
                .frame(minWidth: 18, minHeight: 18)
                .background(Circle().fill(AppColors.dangerBright))
        }
    }
}
