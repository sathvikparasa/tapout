//
//  ButtonsTab.swift
//  warnabrotha
//
//  Windows 95 style buttons tab with big half-screen action buttons.
//

import SwiftUI

struct ButtonsTab: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var showReportConfirmation = false
    @State private var reportNotes = ""
    @State private var showLotDropdown = false

    var body: some View {
        ZStack(alignment: .top) {
        VStack(spacing: 0) {
            // Location header with dropdown
            Button {
                withAnimation(.easeInOut(duration: 0.15)) {
                    showLotDropdown.toggle()
                }
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "mappin.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(Win95Colors.titleBarActive)

                    if let lot = viewModel.selectedLot {
                        Text(lot.name)
                            .win95Font(size: 18)
                            .foregroundColor(Win95Colors.textPrimary)
                    } else {
                        Text("Select a location")
                            .win95Font(size: 18)
                            .foregroundColor(Win95Colors.textDisabled)
                    }

                    Spacer()

                    Image(systemName: showLotDropdown ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14))
                        .foregroundColor(Win95Colors.textPrimary)
                }
            }
            .buttonStyle(PlainButtonStyle())
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
            .background(Win95Colors.windowBackground)
            .overlay(
                Rectangle()
                    .fill(Win95Colors.buttonShadow.opacity(0.5))
                    .frame(height: 1),
                alignment: .bottom
            )

            // Risk Card Section
            HStack(spacing: 12) {
                Win95RiskCard(
                    riskLevel: viewModel.prediction?.riskLevel ?? "MEDIUM",
                    riskMessage: viewModel.riskMessage
                )

                Button {
                    Task { await viewModel.refresh() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 12))
                        .foregroundColor(Win95Colors.textPrimary)
                        .padding(8)
                        .background(Win95Colors.buttonFace)
                        .beveledBorder(raised: true, width: 1)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(16)
            .background(Win95Colors.windowBackground)

            // Divider
            Rectangle()
                .fill(Win95Colors.buttonShadow.opacity(0.5))
                .frame(height: 1)

            Spacer()

            // Main buttons area - centered with consistent padding
            VStack(spacing: 16) {
                // Report TAPS button (RED - primary action)
                Win95BigButton(
                    title: "I SAW TAPS",
                    subtitle: "Report a sighting",
                    color: Win95Colors.dangerRed,
                    height: 120
                ) {
                    showReportConfirmation = true
                }

                // Check-in/out button (secondary action)
                if viewModel.isParked {
                    Win95BigButton(
                        title: "I'M LEAVING",
                        subtitle: "from \(viewModel.currentSession?.parkingLotName ?? "lot")",
                        color: Win95Colors.warningYellow,
                        height: 72
                    ) {
                        Task {
                            await viewModel.checkOut()
                        }
                    }
                } else {
                    Win95BigButton(
                        title: "I PARKED HERE",
                        subtitle: "Get TAPS alerts",
                        color: Win95Colors.neutralGray,
                        height: 72
                    ) {
                        Task {
                            await viewModel.checkIn()
                        }
                    }
                }
            }
            .padding(.horizontal, 20)

            Spacer()

            // Status bar at bottom
            Win95StatusBar(viewModel: viewModel)
        }
        .background(Win95Colors.windowBackground)

        // Win95-styled dropdown overlay
        if showLotDropdown {
            VStack(spacing: 0) {
                ForEach(viewModel.parkingLots) { lot in
                    Button {
                        viewModel.selectLot(lot.id)
                        withAnimation(.easeInOut(duration: 0.15)) {
                            showLotDropdown = false
                        }
                    } label: {
                        HStack(spacing: 8) {
                            if lot.id == viewModel.selectedLotId {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 13))
                                    .foregroundColor(Win95Colors.selectionText)
                            } else {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 13))
                                    .hidden()
                            }
                            Text(lot.name)
                                .win95Font(size: 16)
                                .foregroundColor(
                                    lot.id == viewModel.selectedLotId
                                        ? Win95Colors.selectionText
                                        : Win95Colors.textPrimary
                                )
                            Spacer()
                        }
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .background(
                            lot.id == viewModel.selectedLotId
                                ? Win95Colors.selectionBackground
                                : Win95Colors.inputBackground
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .background(Win95Colors.inputBackground)
            .beveledBorder(raised: false, width: 1)
            .padding(.horizontal, 16)
            .padding(.top, 50)
        }

        } // ZStack
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

}

// MARK: - Windows 95 Status Bar

struct Win95StatusBar: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        HStack(spacing: 0) {
            // Parked count
            StatusBarItem(
                icon: "car.fill",
                text: "\(viewModel.selectedLot?.activeParkers ?? 0) parked"
            )

            StatusBarDivider()

            // Reports count
            StatusBarItem(
                icon: "exclamationmark.triangle.fill",
                text: "\(viewModel.selectedLot?.recentSightings ?? 0) reports"
            )

            StatusBarDivider()

            // Session status
            if viewModel.isParked {
                StatusBarItem(
                    icon: "checkmark.circle.fill",
                    text: "Parked",
                    color: Win95Colors.safeGreen
                )
            } else {
                StatusBarItem(
                    icon: "circle",
                    text: "Not parked",
                    color: Win95Colors.textDisabled
                )
            }
        }
        .frame(height: 28)
        .background(Win95Colors.buttonFace)
        .overlay(
            Rectangle()
                .fill(Win95Colors.buttonShadow)
                .frame(height: 1),
            alignment: .top
        )
    }
}

struct StatusBarDivider: View {
    var body: some View {
        Rectangle()
            .fill(Win95Colors.buttonShadow)
            .frame(width: 1)
            .padding(.vertical, 4)
    }
}

struct StatusBarItem: View {
    let icon: String
    let text: String
    var color: Color = Win95Colors.textPrimary

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 11))
            Text(text)
                .win95Font(size: 12)
        }
        .foregroundColor(color)
        .frame(maxWidth: .infinity)
    }
}

#Preview {
    VStack(spacing: 0) {
        Win95TitleBar(title: "WarnABrotha", icon: "car.fill")
        ButtonsTab(viewModel: AppViewModel())
    }
    .background(Win95Colors.windowBackground)
}
