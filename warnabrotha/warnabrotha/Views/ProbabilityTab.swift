//
//  ProbabilityTab.swift
//  TapOut
//
//  TapOut Feed — recent TAPS sightings with lot filter pills.
//

import SwiftUI

struct ProbabilityTab: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var selectedFilter: Int? = nil // nil = ALL LOTS

    var body: some View {
        VStack(spacing: 0) {
            // Top bar
            HStack {
                Text("Recent Taps")
                    .displayFont(size: 24)
                    .foregroundColor(AppColors.textPrimary)
                    .tracking(-0.5)

                Spacer()

                Text("TapOut")
                    .appFont(size: 14, weight: .bold)
                    .foregroundColor(AppColors.accent)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)

            // Lot filter pills
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    PillView(
                        text: "ALL LOTS",
                        isSelected: selectedFilter == nil
                    ) {
                        selectedFilter = nil
                        // When ALL is selected, load the current lot's feed
                        Task { await viewModel.refresh() }
                    }

                    ForEach(viewModel.parkingLots) { lot in
                        PillView(
                            text: lot.code,
                            isSelected: selectedFilter == lot.id
                        ) {
                            selectedFilter = lot.id
                            viewModel.selectLot(lot.id)
                        }
                    }
                }
                .padding(.horizontal, 20)
            }
            .padding(.vertical, 8)

            // Feed content
            ScrollView {
                VStack(spacing: 0) {
                    // Feed header
                    HStack {
                        Text("Showing reports from last 3 hours")
                            .appFont(size: 12, weight: .semibold)
                            .textCase(.uppercase)
                            .tracking(-0.5)
                            .foregroundColor(AppColors.textMuted)

                        Spacer()

                        LiveBadge()
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)

                    // Feed items
                    if let feed = viewModel.feed {
                        if feed.sightings.isEmpty {
                            EmptyFeedView()
                                .padding(20)
                        } else {
                            VStack(spacing: 0) {
                                ForEach(feed.sightings) { sighting in
                                    FeedItemView(sighting: sighting) { voteType in
                                        Task {
                                            await viewModel.vote(sightingId: sighting.id, type: voteType)
                                        }
                                    }
                                }

                                // End of window marker
                                HStack(spacing: 8) {
                                    Rectangle()
                                        .fill(AppColors.border)
                                        .frame(height: 1)
                                    Text("End of 3-hour window")
                                        .appFont(size: 11, weight: .medium)
                                        .foregroundColor(AppColors.textMuted)
                                        .fixedSize()
                                    Rectangle()
                                        .fill(AppColors.border)
                                        .frame(height: 1)
                                }
                                .padding(.horizontal, 20)
                                .padding(.vertical, 24)
                            }
                        }
                    } else {
                        VStack(spacing: 12) {
                            ProgressView()
                                .tint(AppColors.accent)
                            Text("Loading feed...")
                                .appFont(size: 14)
                                .foregroundColor(AppColors.textMuted)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 48)
                    }
                }
            }
            .refreshable {
                await viewModel.refresh()
            }
        }
        .background(AppColors.background)
    }
}

// MARK: - Feed Item

struct FeedItemView: View {
    let sighting: FeedSighting
    let onVote: (VoteType) -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 12) {
                // Time indicator
                VStack(spacing: 4) {
                    Circle()
                        .fill(timeColor)
                        .frame(width: 10, height: 10)
                    Rectangle()
                        .fill(AppColors.border)
                        .frame(width: 2)
                }
                .frame(width: 10)

                // Content
                VStack(alignment: .leading, spacing: 8) {
                    // Header
                    HStack {
                        Text(timeText)
                            .appFont(size: 12, weight: .semibold)
                            .foregroundColor(AppColors.textSecondary)

                        Spacer()

                        Text(sighting.parkingLotCode)
                            .appFont(size: 11, weight: .bold)
                            .textCase(.uppercase)
                            .foregroundColor(AppColors.textMuted)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(
                                Capsule()
                                    .fill(AppColors.background)
                            )
                    }

                    // Vote buttons
                    HStack(spacing: 12) {
                        Spacer()

                        VoteButton(
                            count: sighting.upvotes,
                            icon: "hand.thumbsup.fill",
                            isSelected: sighting.userVote == .upvote,
                            color: AppColors.success
                        ) {
                            onVote(.upvote)
                        }

                        VoteButton(
                            count: sighting.downvotes,
                            icon: "hand.thumbsdown.fill",
                            isSelected: sighting.userVote == .downvote,
                            color: AppColors.danger
                        ) {
                            onVote(.downvote)
                        }
                    }
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)

            Divider()
                .padding(.leading, 42)
        }
    }

    private var timeColor: Color {
        if sighting.minutesAgo < 30 {
            return AppColors.dangerBright
        } else if sighting.minutesAgo < 90 {
            return AppColors.warning
        } else {
            return AppColors.textMuted
        }
    }

    private var timeText: String {
        if sighting.minutesAgo < 60 {
            return "\(sighting.minutesAgo) mins ago"
        } else {
            let hours = sighting.minutesAgo / 60
            return "\(hours) hour\(hours > 1 ? "s" : "") ago"
        }
    }
}

// MARK: - Vote Button

struct VoteButton: View {
    let count: Int
    let icon: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.system(size: 14))
                Text("\(count)")
                    .appFont(size: 12, weight: .bold)
            }
            .foregroundColor(isSelected ? color : AppColors.textMuted)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                Capsule()
                    .fill(isSelected ? color.opacity(0.1) : AppColors.cardBackground)
            )
            .overlay(
                Capsule()
                    .stroke(isSelected ? color.opacity(0.3) : AppColors.border, lineWidth: 1)
            )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Empty Feed

struct EmptyFeedView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 40, weight: .light))
                .foregroundColor(AppColors.textMuted)

            VStack(spacing: 6) {
                Text("No Reports")
                    .appFont(size: 18, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)

                Text("No TAPS sightings have been reported in the past 3 hours. Check back later or report a sighting if you spot one!")
                    .appFont(size: 14)
                    .foregroundColor(AppColors.textSecondary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(32)
        .cardStyle(cornerRadius: 16)
    }
}

// MARK: - Lot Selector (Feed)

struct FeedLotSelector: View {
    let lots: [ParkingLot]
    let selectedId: Int
    let onSelect: (Int) -> Void

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(lots) { lot in
                    PillView(
                        text: lot.code,
                        isSelected: lot.id == selectedId
                    ) {
                        onSelect(lot.id)
                    }
                }
            }
        }
    }
}

#Preview {
    ProbabilityTab(viewModel: AppViewModel())
}
