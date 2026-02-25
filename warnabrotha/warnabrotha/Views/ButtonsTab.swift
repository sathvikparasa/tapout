//
//  ButtonsTab.swift
//  TapOut
//
//  TapOut Dashboard — main home screen with check-in, report, risk meter.
//

import SwiftUI

struct ButtonsTab: View {
    @ObservedObject var viewModel: AppViewModel
    @Binding var selectedTab: Int
    @State private var showReportConfirmation = false
    @State private var showLotDropdown = false
    @State private var showPreferences = false
    @State private var showRiskInfo = false

    private var screenHeight: CGFloat {
        UIScreen.main.bounds.height
    }

    var body: some View {
        ZStack(alignment: .top) {
            VStack(spacing: 0) {
                VStack(spacing: 16) {
                    // Lot selector
                    lotSelector
                        .padding(.horizontal, 20)
                        .padding(.top, 8)
                        .zIndex(10)

                    // Action buttons row
                    HStack(spacing: 20) {
                        // Check-in / Check-out button
                        if viewModel.isParked && viewModel.currentSession?.parkingLotId == viewModel.selectedLotId {
                            // Viewing the lot we're parked at → CHECK OUT
                            DashboardActionButton(
                                title: "CHECK OUT",
                                systemIcon: "arrow.right.circle",
                                color: AppColors.textSecondary
                            ) {
                                Task { await viewModel.checkOut() }
                            }
                        } else if viewModel.isParked {
                            // Parked elsewhere → tap to switch back
                            DashboardActionButton(
                                title: "AT \(viewModel.currentSession?.parkingLotCode ?? "LOT")",
                                systemIcon: "checkmark.circle.fill",
                                color: AppColors.textSecondary.opacity(0.5)
                            ) {
                                if let lotId = viewModel.currentSession?.parkingLotId {
                                    viewModel.selectLot(lotId)
                                }
                            }
                        } else {
                            // Not parked → CHECK IN
                            DashboardActionButton(
                                title: "GET \(viewModel.selectedLot?.code ?? "LOT") ALERTS",
                                systemIcon: "bell.fill",
                                color: AppColors.accent
                            ) {
                                UINotificationFeedbackGenerator().notificationOccurred(.success)
                                Task { await viewModel.checkIn() }
                            }
                        }

                        // Report button
                        DashboardActionButton(
                            title: "REPORT TAPS",
                            systemIcon: "exclamationmark.triangle.fill",
                            color: AppColors.danger
                        ) {
                            let gen = UIImpactFeedbackGenerator(style: .medium)
                            gen.impactOccurred()
                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { gen.impactOccurred() }
                            showReportConfirmation = true
                        }
                    }
                    .padding(.horizontal, 24)
                    .padding(12)
                    // Risk Indicators
                    riskIndicatorsSection
                        .padding(.horizontal, 20)

                    Text("Disclaimer: We cannot report all TAPS agents and do not guarantee 100% accuracy. Please be diligent in your parking practices.")
                        .appFont(size: 10)
                        .foregroundColor(AppColors.textMuted)
                        .multilineTextAlignment(.center)
                        .fixedSize(horizontal: false, vertical: true)
                        .frame(maxWidth: .infinity)
                        .padding(.horizontal, 32)

                    Spacer(minLength: 0)
                }
            }
            .background(AppColors.background)

            // Top bar
            topBar
        }
        .overlay {
            if showPreferences {
                ZStack {
                    Color.black.opacity(0.35)
                        .ignoresSafeArea()
                        .onTapGesture { showPreferences = false }

                    PreferencesView(onDismiss: { showPreferences = false })
                        .padding(.horizontal, 24)
                }
            } else if showRiskInfo {
                ZStack {
                    Color.black.opacity(0.35)
                        .ignoresSafeArea()
                        .onTapGesture { showRiskInfo = false }

                    RiskInfoSheet(
                        currentBars: viewModel.riskBars,
                        currentLevel: viewModel.prediction?.riskLevel ?? "UNKNOWN",
                        currentMessage: viewModel.riskMessage,
                        onDismiss: { showRiskInfo = false }
                    )
                    .padding(.horizontal, 24)
                }
            }
        }
        .alert("Report TAPS Sighting", isPresented: $showReportConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Report", role: .destructive) {
                Task {
                    await viewModel.reportSighting()
                }
            }
        } message: {
            Text("This will alert all users parked at \(viewModel.selectedLot?.name ?? "this lot"). Are you sure?")
        }
        .alert("Success", isPresented: $viewModel.showConfirmation) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.confirmationMessage)
        }
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.error ?? "An error occurred")
        }
    }

    // MARK: - Top Bar

    private var topBar: some View {
        HStack {
            (Text("Tap")
                .foregroundColor(AppColors.textPrimary)
            + Text("Out")
                .foregroundColor(AppColors.accent))
                .displayFont(size: 30)
                .tracking(-0.5)

            Spacer()

            Button {
                showPreferences = true
            } label: {
                Image(systemName: "gearshape.fill")
                    .font(.system(size: 22))
                    .foregroundColor(AppColors.textPrimary)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(
            AppColors.background
                .opacity(0.95)
                .ignoresSafeArea(edges: .top)
        )
    }

    // MARK: - Lot Selector

    private var lotSelector: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("SELECT PARKING ZONE")
                .appFont(size: 14, weight: .bold)
                .tracking(1)
                .foregroundColor(AppColors.accent)

            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    showLotDropdown.toggle()
                }
            } label: {
                HStack(spacing: 12) {
                    Image(systemName: "mappin.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(AppColors.accent)

                    if let lot = viewModel.selectedLot {
                        Text("\(lot.name) (\(lot.code))")
                            .appFont(size: 16, weight: .semibold)
                            .foregroundColor(AppColors.textPrimary)
                    } else {
                        Text("Select a location")
                            .appFont(size: 16, weight: .medium)
                            .foregroundColor(AppColors.textMuted)
                    }

                    Spacer()

                    Image(systemName: showLotDropdown ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(AppColors.textMuted)
                }
                .padding(16)
                .background(
                    UnevenRoundedRectangle(
                        topLeadingRadius: 16,
                        bottomLeadingRadius: showLotDropdown ? 0 : 16,
                        bottomTrailingRadius: showLotDropdown ? 0 : 16,
                        topTrailingRadius: 16
                    )
                    .fill(AppColors.cardBackground)
                )
                .overlay(
                    UnevenRoundedRectangle(
                        topLeadingRadius: 16,
                        bottomLeadingRadius: showLotDropdown ? 0 : 16,
                        bottomTrailingRadius: showLotDropdown ? 0 : 16,
                        topTrailingRadius: 16
                    )
                    .stroke(AppColors.border, lineWidth: 1)
                )
                .contentShape(Rectangle())
            }
            .buttonStyle(PlainButtonStyle())
            .overlay(alignment: .top) {
                GeometryReader { geo in
                    if showLotDropdown {
                        lotDropdownMenu
                            .offset(y: geo.size.height)
                    }
                }
                .allowsHitTesting(showLotDropdown)
            }
            .zIndex(1)
        }
        .padding(.top, 56) // space for top bar
    }

    // MARK: - Risk Meter Card

    private var riskMeterCard: some View {
        let riskLevel = viewModel.prediction?.riskLevel ?? "UNKNOWN"
        let activeBars = viewModel.riskBars // 1=LOW, 2=MEDIUM, 3=HIGH

        return VStack(alignment: .leading, spacing: 0) {
            // Header row: label + LIVE badge — pinned to top
            HStack {
                Text("Risk Meter")
                    .appFont(size: 14, weight: .bold)
                    .textCase(.uppercase)
                    .foregroundColor(AppColors.textPrimary.opacity(0.4))

                Image(systemName: "info.circle")
                    .font(.system(size: 12))
                    .foregroundColor(AppColors.textPrimary.opacity(0.3))

                Spacer()

                LiveBadge()
            }

            Spacer(minLength: 0).frame(maxHeight: 8)

            // Risk bars + level text + message
            HStack(spacing: 16) {
                // Signal-strength bar chart
                RiskBarChart(activeBars: activeBars)

                // Risk level + message
                VStack(alignment: .leading, spacing: 4) {
                    Text(riskLevel.uppercased())
                        .displayFont(size: 30)
                        .foregroundColor(riskLevelColor(riskLevel))

                    Text(viewModel.riskMessage)
                        .appFont(size: 10, weight: .medium)
                        .foregroundColor(AppColors.textPrimary.opacity(0.6))
                        .lineLimit(1)
                }
            }
        }
        .padding(20)
        .frame(height: screenHeight * 0.16)
        .background(
            RoundedRectangle(cornerRadius: 32)
                .fill(AppColors.cardBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 32)
                .stroke(Color.black.opacity(0.08), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.05), radius: 2, y: 1)
    }

    private func riskLevelColor(_ level: String) -> Color {
        switch level.uppercased() {
        case "HIGH": return AppColors.dangerBright
        case "MEDIUM": return AppColors.warning
        case "LOW": return AppColors.success
        default: return AppColors.textMuted
        }
    }

    // MARK: - Risk Indicators

    private var riskIndicatorsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Risk Indicators")
                    .appFont(size: 14, weight: .bold)
                    .tracking(1)
                    .textCase(.uppercase)
                    .foregroundColor(AppColors.accent)

                Spacer()

                Button {
                    selectedTab = 3
                } label: {
                    HStack(spacing: 4) {
                        Text("View Map")
                            .appFont(size: 12, weight: .semibold)
                            .foregroundColor(AppColors.accent)
                        Image(systemName: "chevron.right")
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(AppColors.accent)
                    }
                }
                .buttonStyle(PlainButtonStyle())
            }

            riskMeterCard
                .onTapGesture { showRiskInfo = true }

            recentActivitySection
        }
    }

    private var recentActivitySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let feed = viewModel.feed, let sighting = feed.sightings.first {

                Button {
                    selectedTab = 1
                } label: {
                    ZStack(alignment: .top) {
                        // Bottom-most layer (most inset)
                        RoundedRectangle(cornerRadius: 16)
                            .fill(AppColors.cardBackground)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(AppColors.border.opacity(0.3), lineWidth: 1)
                            )
                            .padding(.horizontal, 16)
                            .frame(height: 73)
                            .offset(y: 8)

                        // Middle layer
                        RoundedRectangle(cornerRadius: 16)
                            .fill(AppColors.cardBackground)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(AppColors.border.opacity(0.5), lineWidth: 1)
                            )
                            .padding(.horizontal, 8)
                            .frame(height: 73)
                            .offset(y: 4)

                        // Front card (top layer)
                        HStack(spacing: 12) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 20))
                                .foregroundColor(AppColors.danger)
                                .frame(width: 40, height: 40)
                                .background(
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(AppColors.dangerLight)
                                )

                            VStack(alignment: .leading, spacing: 4) {
                                Text("TAPS spotted: \(sighting.parkingLotCode)")
                                    .appFont(size: 14, weight: .semibold)
                                    .foregroundColor(AppColors.textPrimary)
                                    .lineLimit(1)

                                Text(sighting.minutesAgo.formattedTimeAgo)
                                    .appFont(size: 12)
                                    .foregroundColor(AppColors.textMuted)
                            }

                            Spacer()

                            Image(systemName: "chevron.right")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(AppColors.textMuted)
                        }
                        .cardStyle(cornerRadius: 16)
                    }
                    .padding(.bottom, 8)
                }
                .buttonStyle(PlainButtonStyle())
            } else {
                HStack(spacing: 12) {
                    Image(systemName: "checkmark.circle")
                        .font(.system(size: 20))
                        .foregroundColor(AppColors.success)

                    Text("No recent TAPS activity")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .cardStyle(cornerRadius: 16)
            }
        }
    }

    // MARK: - Lot Dropdown Menu

    private var lotDropdownMenu: some View {
        VStack(spacing: 0) {
            ForEach(viewModel.parkingLots) { lot in
                Button {
                    viewModel.selectLot(lot.id)
                    withAnimation(.easeInOut(duration: 0.15)) {
                        showLotDropdown = false
                    }
                } label: {
                    HStack(spacing: 12) {
                        Image(systemName: "mappin.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(
                                lot.id == viewModel.selectedLotId
                                    ? AppColors.accent
                                    : AppColors.textMuted
                            )

                        Text("\(lot.name) (\(lot.code))")
                            .appFont(size: 14, weight: lot.id == viewModel.selectedLotId ? .bold : .regular)
                            .foregroundColor(AppColors.textPrimary)

                        Spacer()

                        if lot.id == viewModel.selectedLotId {
                            Image(systemName: "checkmark")
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(AppColors.accent)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(
                        lot.id == viewModel.selectedLotId
                            ? AppColors.accentVeryLight
                            : Color.clear
                    )
                    .contentShape(Rectangle())
                }
                .buttonStyle(PlainButtonStyle())

                if lot.id != viewModel.parkingLots.last?.id {
                    Divider()
                        .padding(.leading, 44)
                }
            }
        }
        .background(
            UnevenRoundedRectangle(
                topLeadingRadius: 0,
                bottomLeadingRadius: 16,
                bottomTrailingRadius: 16,
                topTrailingRadius: 0
            )
            .fill(AppColors.cardBackground)
        )
        .overlay(
            UnevenRoundedRectangle(
                topLeadingRadius: 0,
                bottomLeadingRadius: 16,
                bottomTrailingRadius: 16,
                topTrailingRadius: 0
            )
            .stroke(AppColors.border, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.1), radius: 20, y: 10)
    }
}

// MARK: - Status Bar (Bottom info)

struct StatusInfoBar: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        HStack(spacing: 16) {
            StatusInfoItem(
                icon: "car.fill",
                value: "\(viewModel.selectedLot?.activeParkers ?? 0)",
                label: "Parked"
            )

            StatusInfoItem(
                icon: "exclamationmark.triangle.fill",
                value: "\(viewModel.selectedLot?.recentSightings ?? 0)",
                label: "Reports"
            )

            if viewModel.isParked {
                StatusInfoItem(
                    icon: "checkmark.circle.fill",
                    value: "Active",
                    label: "Session",
                    color: AppColors.success
                )
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(AppColors.cardBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(AppColors.border, lineWidth: 1)
        )
    }
}

struct StatusInfoItem: View {
    let icon: String
    let value: String
    let label: String
    var color: Color = AppColors.textSecondary

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 12))
                .foregroundColor(color)
            VStack(alignment: .leading, spacing: 0) {
                Text(value)
                    .appFont(size: 14, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)
                Text(label)
                    .appFont(size: 10)
                    .foregroundColor(AppColors.textMuted)
            }
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Risk Info Sheet

struct RiskInfoSheet: View {
    let currentBars: Int
    let currentLevel: String
    let currentMessage: String
    let onDismiss: () -> Void

    private struct ExplainRow {
        let bars: Int
        let label: String
        let color: Color
        let description: String
    }

    private let rows: [ExplainRow] = [
        ExplainRow(bars: 1, label: "LOW",    color: AppColors.success,     description: "Taps was spotted at this lot over an hour ago. Unlikely to return for another hour"),
        ExplainRow(bars: 2, label: "MEDIUM", color: AppColors.warning,     description: "Taps hasn't been spotted in 2 hours. They are likely to return soon"),
        ExplainRow(bars: 3, label: "HIGH",   color: AppColors.dangerBright, description: "Taps has been reported within the hour. They are likely still in the area ticketing cars."),
    ]

    private func levelColor(_ bars: Int) -> Color {
        switch bars {
        case 1: return AppColors.success
        case 2: return AppColors.warning
        case 3: return AppColors.dangerBright
        default: return AppColors.textMuted
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {

            // Header
            HStack(alignment: .center) {
                Text("Risk Meter")
                    .displayFont(size: 30)
                    .foregroundColor(AppColors.textPrimary)

                Spacer()

                Button(action: onDismiss) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 26))
                        .foregroundColor(AppColors.textMuted)
                }
                .buttonStyle(PlainButtonStyle())
            }

            // Subheader
            Text("What does this mean?")
                .appFont(size: 15, weight: .bold)
                .foregroundColor(AppColors.accent)

            // Explanation rows
            VStack(alignment: .leading, spacing: 24) {
            ForEach(rows, id: \.label) { row in
                HStack(alignment: .center, spacing: 16) {
                    RiskBarChart(activeBars: row.bars)

                    VStack(alignment: .leading, spacing: 0) {
                        Text(row.label)
                            .displayFont(size: 30)
                            .foregroundColor(row.color)

                        Text(row.description)
                            .appFont(size: 11, weight: .medium)
                            .foregroundColor(AppColors.textPrimary.opacity(0.6))
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            }

            // Disclaimer
            Text("Disclaimer: These estimates are based on patterns we've detected from our research. There is no guarantee of accuracy.")
                .appFont(size: 11, weight: .medium)
                .foregroundColor(AppColors.textPrimary.opacity(0.6))
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(24)
        .background(
            RoundedRectangle(cornerRadius: 32)
                .fill(AppColors.cardBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 32)
                .stroke(Color.black.opacity(0.05), lineWidth: 1)
        )
    }
}

#Preview {
    ButtonsTab(viewModel: AppViewModel(), selectedTab: .constant(0))
}
