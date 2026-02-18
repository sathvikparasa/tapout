//
//  MapTab.swift
//  TapOut
//
//  Interactive campus parking map with lot markers, search, and bottom sheet.
//

import SwiftUI
import MapKit

// MARK: - Hardcoded fallback coordinates

private let defaultCoordinates: [String: CLLocationCoordinate2D] = [
    "MU": CLLocationCoordinate2D(latitude: 38.544416, longitude: -121.749561),
    "HUTCH": CLLocationCoordinate2D(latitude: 38.53969, longitude: -121.758182),
    "ARC": CLLocationCoordinate2D(latitude: 38.54304, longitude: -121.757572),
]

private let ucDavisCenter = CLLocationCoordinate2D(latitude: 38.5422, longitude: -121.7551)

struct MapTab: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var selectedLot: ParkingLot? = nil
    @State private var searchQuery = ""
    @State private var cameraPosition: MapCameraPosition = .region(
        MKCoordinateRegion(
            center: ucDavisCenter,
            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        )
    )

    private var filteredLots: [ParkingLot] {
        if searchQuery.isEmpty {
            return viewModel.parkingLots
        }
        let query = searchQuery.lowercased()
        return viewModel.parkingLots.filter {
            $0.name.lowercased().contains(query) || $0.code.lowercased().contains(query)
        }
    }

    var body: some View {
        ZStack(alignment: .top) {
            // Map
            Map(position: $cameraPosition) {
                ForEach(filteredLots) { lot in
                    let coord = coordinateFor(lot)
                    let isSelected = selectedLot?.id == lot.id

                    Annotation(lot.code, coordinate: coord) {
                        VStack(spacing: 4) {
                            ZStack {
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(isSelected ? AppColors.accent : AppColors.accent.opacity(0.6))
                                    .frame(width: 32, height: 32)
                                    .shadow(color: .black.opacity(isSelected ? 0.2 : 0.1), radius: isSelected ? 8 : 4, y: 2)

                                Image(systemName: "car.fill")
                                    .font(.system(size: 14, weight: .bold))
                                    .foregroundColor(.white)
                            }

                            Text(lot.code)
                                .appFont(size: 8, weight: .bold)
                                .textCase(.uppercase)
                                .foregroundColor(AppColors.textPrimary)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(
                                    Capsule()
                                        .fill(isSelected ? Color.white : Color.white.opacity(0.8))
                                )
                                .overlay(
                                    Capsule()
                                        .stroke(isSelected ? AppColors.accent.opacity(0.2) : Color.clear, lineWidth: 1)
                                )
                        }
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.25)) {
                                selectedLot = lot
                            }
                        }
                    }
                }
            }
            .mapStyle(.standard(pointsOfInterest: .excludingAll))
            .ignoresSafeArea(edges: .top)

            // Search bar overlay
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 16))
                    .foregroundColor(AppColors.textMuted)

                TextField("Search campus lots...", text: $searchQuery)
                    .appFont(size: 14, weight: .medium)
                    .foregroundColor(AppColors.textPrimary)
                    .autocorrectionDisabled()

                if !searchQuery.isEmpty {
                    Button {
                        searchQuery = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(AppColors.textMuted)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(12)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(.ultraThinMaterial)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(AppColors.border.opacity(0.5), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.1), radius: 10, y: 4)
            .padding(.horizontal, 17)
            .padding(.top, 56)

            // Map controls (right side)
            VStack(spacing: 8) {
                // My Location button
                Button {
                    withAnimation {
                        cameraPosition = .region(
                            MKCoordinateRegion(
                                center: ucDavisCenter,
                                span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
                            )
                        )
                    }
                } label: {
                    Image(systemName: "location.fill")
                        .font(.system(size: 16))
                        .foregroundColor(AppColors.textSecondary)
                        .frame(width: 48, height: 48)
                        .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(Color.white)
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(AppColors.borderLight, lineWidth: 1)
                        )
                        .shadow(color: .black.opacity(0.1), radius: 4, y: 2)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.trailing, 17)
            .padding(.top, 120)
            .frame(maxWidth: .infinity, alignment: .trailing)
        }
        .overlay(alignment: .bottom) {
            // Bottom sheet
            if let lot = selectedLot {
                LotBottomSheet(
                    lot: lot,
                    stats: viewModel.lotStats[lot.id],
                    isParked: viewModel.isParked,
                    currentSessionLotId: viewModel.currentSession?.parkingLotId,
                    onCheckIn: {
                        Task { await viewModel.checkInAtLot(lot.id) }
                    },
                    onCheckOut: {
                        Task { await viewModel.checkOut() }
                    },
                    onReportTaps: {
                        Task { await viewModel.reportSightingAtLot(lot.id) }
                    },
                    onDismiss: {
                        withAnimation { selectedLot = nil }
                    }
                )
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .alert("Confirmation", isPresented: $viewModel.showConfirmation) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.confirmationMessage)
        }
    }

    private func coordinateFor(_ lot: ParkingLot) -> CLLocationCoordinate2D {
        if let lat = lot.latitude, let lng = lot.longitude {
            return CLLocationCoordinate2D(latitude: lat, longitude: lng)
        }
        return defaultCoordinates[lot.code] ?? ucDavisCenter
    }
}

// MARK: - Lot Bottom Sheet

private struct LotBottomSheet: View {
    let lot: ParkingLot
    let stats: ParkingLotWithStats?
    let isParked: Bool
    let currentSessionLotId: Int?
    let onCheckIn: () -> Void
    let onCheckOut: () -> Void
    let onReportTaps: () -> Void
    let onDismiss: () -> Void

    private var isCheckedInHere: Bool {
        currentSessionLotId == lot.id
    }

    private var isCheckedInElsewhere: Bool {
        isParked && !isCheckedInHere
    }

    var body: some View {
        VStack(spacing: 0) {
            // Drag handle
            RoundedRectangle(cornerRadius: 2)
                .fill(AppColors.border)
                .frame(width: 48, height: 4)
                .padding(.top, 12)
                .padding(.bottom, 16)

            VStack(spacing: 20) {
                // Title row
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(lot.name) (\(lot.code))")
                            .appFont(size: 20, weight: .bold)
                            .foregroundColor(AppColors.textPrimary)
                            .tracking(-0.5)

                        Text("Zone \(lot.id) \u{2022} UC Davis Campus")
                            .appFont(size: 12, weight: .medium)
                            .foregroundColor(AppColors.textSecondary)
                    }

                    Spacer()

                    LiveBadge()
                }

                // Stat cards
                HStack(spacing: 12) {
                    StatCard(
                        icon: "person.2.fill",
                        value: "\(stats?.activeParkers ?? 0)",
                        label: "Users checked in"
                    )

                    StatCard(
                        icon: "hand.raised.fill",
                        value: "\(stats?.recentSightings ?? 0)",
                        label: "Taps in last hour"
                    )
                }

                // Warning if checked in elsewhere
                if isCheckedInElsewhere {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 14))
                            .foregroundColor(AppColors.warning)
                        Text("You're checked in at another lot")
                            .appFont(size: 12, weight: .medium)
                            .foregroundColor(AppColors.textSecondary)
                    }
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(AppColors.warning.opacity(0.1))
                    )
                }

                // Action buttons
                HStack(spacing: 12) {
                    if isCheckedInHere {
                        PrimaryButton(
                            title: "CHECK OUT",
                            icon: "arrow.right.circle",
                            color: AppColors.textSecondary,
                            action: onCheckOut
                        )
                    } else {
                        PrimaryButton(
                            title: "CHECK IN",
                            icon: "arrow.down.circle",
                            color: isCheckedInElsewhere ? AppColors.textMuted : AppColors.accent,
                            action: onCheckIn
                        )
                        .disabled(isCheckedInElsewhere)
                        .opacity(isCheckedInElsewhere ? 0.5 : 1)
                    }

                    PrimaryButton(
                        title: "REPORT TAPS",
                        icon: "exclamationmark.triangle",
                        color: AppColors.danger,
                        action: onReportTaps
                    )
                }
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 32)
        }
        .background(
            RoundedRectangle(cornerRadius: 24)
                .fill(Color.white)
                .shadow(color: .black.opacity(0.1), radius: 20, y: -10)
        )
        .overlay(alignment: .top) {
            RoundedRectangle(cornerRadius: 24)
                .stroke(AppColors.borderLight, lineWidth: 1)
        }
        .gesture(
            DragGesture()
                .onEnded { value in
                    if value.translation.height > 120 {
                        onDismiss()
                    }
                }
        )
    }
}

// MARK: - Stat Card

private struct StatCard: View {
    let icon: String
    let value: String
    let label: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(AppColors.accent)

                Text(value)
                    .appFont(size: 20, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)
            }

            Text(label.uppercased())
                .appFont(size: 10, weight: .semibold)
                .foregroundColor(AppColors.textSecondary)
                .tracking(-0.25)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(AppColors.background)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(AppColors.accent.opacity(0.05), lineWidth: 1)
        )
    }
}

#Preview {
    MapTab(viewModel: AppViewModel())
}
