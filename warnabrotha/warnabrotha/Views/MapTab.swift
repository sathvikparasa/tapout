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
    "MU": CLLocationCoordinate2D(latitude: 38.544552, longitude: -121.749712),
    "HUTCH": CLLocationCoordinate2D(latitude: 38.539711, longitude: -121.758379),
    "ARC": CLLocationCoordinate2D(latitude: 38.54313, longitude: -121.75756),
    "TERCERO": CLLocationCoordinate2D(latitude: 38.534834, longitude: -121.756463),
]

private let ucDavisCenter = CLLocationCoordinate2D(latitude: 38.5422, longitude: -121.7551)

private let lotDisplayNames: [String: String] = [
    "HUTCH": "Hutchinson Parking Structure",
    "MU": "Memorial Union",
    "ARC": "Gym",
    "TERCERO": "Tercero Parking Lot",
]

struct MapTab: View {
    @ObservedObject var viewModel: AppViewModel
    @Binding var hideTabBar: Bool
    @State private var selectedLot: ParkingLot? = nil
    @State private var searchQuery = ""
    @FocusState private var searchFieldFocused: Bool
    @State private var cameraPosition: MapCameraPosition = .region(
        MKCoordinateRegion(
            center: ucDavisCenter,
            span: MKCoordinateSpan(latitudeDelta: 0.025, longitudeDelta: 0.025)
        )
    )

    private func displayName(for lot: ParkingLot) -> String {
        lotDisplayNames[lot.code] ?? lot.name
    }

    private func fuzzyScore(_ query: String, _ target: String) -> Int? {
        let q = query.lowercased()
        let t = target.lowercased()
        if t == q { return 200 }
        if t.hasPrefix(q) { return 150 }
        if t.contains(q) { return 100 }
        // Fuzzy: all query chars appear in order within target
        var qi = q.startIndex
        for ch in t {
            if qi == q.endIndex { break }
            if ch == q[qi] { qi = q.index(after: qi) }
        }
        return qi == q.endIndex ? 50 : nil
    }

    private var filteredLots: [ParkingLot] {
        if searchQuery.isEmpty { return viewModel.parkingLots }
        return viewModel.parkingLots.compactMap { lot -> (ParkingLot, Int)? in
            let best = [
                fuzzyScore(searchQuery, lot.name),
                fuzzyScore(searchQuery, lot.code),
                fuzzyScore(searchQuery, displayName(for: lot))
            ].compactMap { $0 }.max()
            return best.map { (lot, $0) }
        }
        .sorted { $0.1 > $1.1 }
        .map { $0.0 }
    }

    var body: some View {
        ZStack(alignment: .top) {
            // Map
            Map(position: $cameraPosition) {
                ForEach(filteredLots) { lot in
                    let coord = coordinateFor(lot)
                    let isSelected = selectedLot?.id == lot.id

                    Annotation("", coordinate: coord) {
                        VStack(spacing: 4) {
                            ZStack {
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(isSelected ? AppColors.darkBackground : Color(hex: "475569"))
                                    .frame(width: 32, height: 32)
                                    .shadow(color: .black.opacity(isSelected ? 0.3 : 0.15), radius: isSelected ? 8 : 4, y: 2)

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
                                        .stroke(isSelected ? AppColors.darkBackground.opacity(0.2) : Color.clear, lineWidth: 1)
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
            .onTapGesture {
                searchFieldFocused = false
            }

            // Search bar + dropdown
            VStack(spacing: 0) {
                let hasResults = !searchQuery.isEmpty && !filteredLots.isEmpty

                // Search bar
                HStack(spacing: 8) {
                    Image(systemName: "magnifyingglass")
                        .font(.system(size: 16))
                        .foregroundColor(AppColors.textMuted)

                    TextField("Search campus lots...", text: $searchQuery)
                        .appFont(size: 14, weight: .medium)
                        .foregroundColor(AppColors.textPrimary)
                        .autocorrectionDisabled()
                        .focused($searchFieldFocused)

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
                    UnevenRoundedRectangle(
                        topLeadingRadius: 16,
                        bottomLeadingRadius: hasResults ? 0 : 16,
                        bottomTrailingRadius: hasResults ? 0 : 16,
                        topTrailingRadius: 16
                    )
                    .fill(.ultraThinMaterial)
                )
                .overlay(
                    UnevenRoundedRectangle(
                        topLeadingRadius: 16,
                        bottomLeadingRadius: hasResults ? 0 : 16,
                        bottomTrailingRadius: hasResults ? 0 : 16,
                        topTrailingRadius: 16
                    )
                    .stroke(AppColors.border.opacity(0.5), lineWidth: 1)
                )

                // Dropdown results
                if hasResults {
                    let results = Array(filteredLots.prefix(5))
                    VStack(spacing: 0) {
                        ForEach(Array(results.enumerated()), id: \.element.id) { index, lot in
                            Button {
                                let coord = coordinateFor(lot)
                                withAnimation(.easeInOut(duration: 0.25)) {
                                    selectedLot = lot
                                    cameraPosition = .region(MKCoordinateRegion(
                                        center: coord,
                                        span: MKCoordinateSpan(latitudeDelta: 0.008, longitudeDelta: 0.008)
                                    ))
                                }
                                searchQuery = ""
                                searchFieldFocused = false
                            } label: {
                                HStack(spacing: 12) {
                                    Image(systemName: "mappin.circle.fill")
                                        .font(.system(size: 16))
                                        .foregroundColor(AppColors.textMuted)
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(lot.name)
                                            .appFont(size: 14, weight: .semibold)
                                            .foregroundColor(AppColors.textPrimary)
                                        Text(lot.code)
                                            .appFont(size: 11, weight: .medium)
                                            .foregroundColor(AppColors.textMuted)
                                    }
                                    Spacer()
                                    Image(systemName: "arrow.up.left")
                                        .font(.system(size: 11))
                                        .foregroundColor(AppColors.textMuted)
                                }
                                .padding(.horizontal, 12)
                                .padding(.vertical, 10)
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(PlainButtonStyle())

                            if index < results.count - 1 {
                                Divider().padding(.leading, 40)
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
                        .fill(.ultraThinMaterial)
                    )
                    .overlay(
                        UnevenRoundedRectangle(
                            topLeadingRadius: 0,
                            bottomLeadingRadius: 16,
                            bottomTrailingRadius: 16,
                            topTrailingRadius: 0
                        )
                        .stroke(AppColors.border.opacity(0.5), lineWidth: 1)
                    )
                }
            }
            .shadow(color: .black.opacity(0.1), radius: 10, y: 4)
            .padding(.horizontal, 17)
            .padding(.top, 8)

            // Map controls (right side)
            VStack(spacing: 8) {
                // My Location button
                Button {
                    withAnimation {
                        cameraPosition = .region(
                            MKCoordinateRegion(
                                center: ucDavisCenter,
                                span: MKCoordinateSpan(latitudeDelta: 0.025, longitudeDelta: 0.025)
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
            .padding(.top, 72)
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
                        UINotificationFeedbackGenerator().notificationOccurred(.success)
                        Task { await viewModel.checkInAtLot(lot.id) }
                    },
                    onCheckOut: {
                        Task { await viewModel.checkOut() }
                    },
                    onReportTaps: {
                        let gen = UIImpactFeedbackGenerator(style: .medium)
                        gen.impactOccurred()
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { gen.impactOccurred() }
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
        .onChange(of: searchFieldFocused) { _, focused in
            withAnimation(.easeInOut(duration: 0.2)) {
                hideTabBar = focused
            }
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
            UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            )
            .fill(Color.white)
            .shadow(color: .black.opacity(0.1), radius: 20, y: -10)
        )
        .overlay(alignment: .top) {
            UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            )
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
    MapTab(viewModel: AppViewModel(), hideTabBar: .constant(false))
}
