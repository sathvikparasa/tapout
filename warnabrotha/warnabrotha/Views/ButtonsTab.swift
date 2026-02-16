//
//  ButtonsTab.swift
//  TapOut
//
//  TapOut Dashboard — main home screen with check-in, report, risk meter.
//

import SwiftUI

struct ButtonsTab: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var showReportConfirmation = false
    @State private var reportNotes = ""
    @State private var showLotDropdown = false

    var body: some View {
        ZStack(alignment: .top) {
            ScrollView {
                VStack(spacing: 28) {
                    // Lot selector
                    lotSelector
                        .padding(.horizontal, 20)
                        .padding(.top, 8)

                    // Action buttons row
                    HStack(spacing: 20) {
                        // Check-in / Check-out button
                        if viewModel.isParked {
                            DashboardActionButton(
                                title: "CHECK OUT",
                                systemIcon: "arrow.right.circle",
                                color: AppColors.warning,
                                textColor: AppColors.textPrimary
                            ) {
                                Task { await viewModel.checkOut() }
                            }
                        } else {
                            DashboardActionButton(
                                title: "CHECK IN",
                                systemIcon: "p.circle.fill",
                                color: AppColors.accent
                            ) {
                                Task { await viewModel.checkIn() }
                            }
                        }

                        // Report button
                        DashboardActionButton(
                            title: "REPORT TAPS",
                            systemIcon: "exclamationmark.triangle.fill",
                            color: AppColors.danger
                        ) {
                            showReportConfirmation = true
                        }
                    }
                    .padding(.horizontal, 24)

                    // Risk meter card
                    riskMeterCard
                        .padding(.horizontal, 20)

                    // Recent activity
                    recentActivitySection
                        .padding(.horizontal, 20)

                    Spacer(minLength: 20)
                }
            }
            .background(AppColors.background)

            // Top bar
            topBar

            // Dropdown overlay
            if showLotDropdown {
                lotDropdownOverlay
            }
        }
        .alert("Report TAPS Sighting", isPresented: $showReportConfirmation) {
            TextField("Optional: Add details", text: $reportNotes)
            Button("Cancel", role: .cancel) {
                reportNotes = ""
            }
            Button("Report", role: .destructive) {
                Task {
                    await viewModel.reportSighting(notes: reportNotes.isEmpty ? nil : reportNotes)
                    reportNotes = ""
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
                .displayFont(size: 24)
                .tracking(-0.5)

            Spacer()

            Button {
                // Notifications action placeholder
            } label: {
                ZStack(alignment: .topTrailing) {
                    Image(systemName: "bell")
                        .font(.system(size: 22))
                        .foregroundColor(AppColors.textPrimary)

                    if viewModel.unreadNotificationCount > 0 {
                        Circle()
                            .fill(AppColors.dangerBright)
                            .frame(width: 10, height: 10)
                            .offset(x: 2, y: -2)
                    }
                }
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
                .appFont(size: 10, weight: .bold)
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
                    RoundedRectangle(cornerRadius: 16)
                        .fill(AppColors.cardBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(AppColors.border, lineWidth: 1)
                )
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.top, 56) // space for top bar
    }

    // MARK: - Risk Meter Card

    private var riskMeterCard: some View {
        let riskLevel = viewModel.prediction?.riskLevel ?? "UNKNOWN"
        let activeBars = viewModel.riskBars // 1=LOW, 2=MEDIUM, 3=HIGH

        return VStack(alignment: .leading, spacing: 16) {
            // Header row: label + LIVE badge
            HStack {
                Text("Current Risk Meter")
                    .appFont(size: 10, weight: .bold)
                    .textCase(.uppercase)
                    .foregroundColor(AppColors.textPrimary.opacity(0.4))

                Spacer()

                LiveBadge()
            }

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
                        .appFont(size: 11, weight: .medium)
                        .foregroundColor(AppColors.textPrimary.opacity(0.6))
                        .lineLimit(2)
                }
            }
        }
        .padding(24)
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

    // MARK: - Recent Activity

    private var recentActivitySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Activity")
                    .appFont(size: 14, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)

                Spacer()

                Button {
                    Task { await viewModel.refresh() }
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

            if let feed = viewModel.feed, let sighting = feed.sightings.first {
                let stackCount = min(feed.sightings.count, 3)

                VStack(spacing: 0) {
                    // Front card (most recent)
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
                            Text(sighting.notes ?? "Taps spotted: \(sighting.parkingLotCode)")
                                .appFont(size: 14, weight: .semibold)
                                .foregroundColor(AppColors.textPrimary)
                                .lineLimit(1)

                            Text("\(sighting.minutesAgo)m ago")
                                .appFont(size: 12)
                                .foregroundColor(AppColors.textMuted)
                        }

                        Spacer()
                    }
                    .cardStyle(cornerRadius: 12)

                    // Stacked card edges below
                    if stackCount >= 2 {
                        StackedCardEdge(inset: 8)
                    }
                    if stackCount >= 3 {
                        StackedCardEdge(inset: 16)
                    }
                }
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
                .cardStyle(cornerRadius: 12)
            }
        }
    }

    // MARK: - Lot Dropdown Overlay

    private var lotDropdownOverlay: some View {
        VStack(spacing: 0) {
            Color.clear
                .frame(height: 152) // offset below lot selector

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
                    }
                    .buttonStyle(PlainButtonStyle())

                    if lot.id != viewModel.parkingLots.last?.id {
                        Divider()
                            .padding(.leading, 44)
                    }
                }
            }
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(AppColors.cardBackground)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(AppColors.border, lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.1), radius: 20, y: 10)
            .padding(.horizontal, 20)

            Spacer()
        }
        .background(
            Color.black.opacity(0.001) // tap-to-dismiss area
                .onTapGesture {
                    withAnimation { showLotDropdown = false }
                }
        )
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

#Preview {
    ButtonsTab(viewModel: AppViewModel())
}
