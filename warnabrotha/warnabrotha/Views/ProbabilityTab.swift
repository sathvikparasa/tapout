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
            // Header
            VStack(alignment: .leading, spacing: 4) {
                (Text("Tap")
                    .foregroundColor(AppColors.textPrimary)
                + Text("Out")
                    .foregroundColor(AppColors.accent))
                    .appFont(size: 11, weight: .bold)

                Text("Recent Reports")
                    .appFont(size: 30, weight: .heavy)
                    .foregroundColor(AppColors.textPrimary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 24)
            .padding(.top, 12)
            .padding(.bottom, 8)

            // Lot filter pills
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    FeedPill(
                        text: "ALL LOTS",
                        isSelected: selectedFilter == nil
                    ) {
                        selectedFilter = nil
                        Task { await viewModel.refresh() }
                    }

                    ForEach(viewModel.parkingLots) { lot in
                        FeedPill(
                            text: lot.code,
                            isSelected: selectedFilter == lot.id
                        ) {
                            selectedFilter = lot.id
                            viewModel.selectLot(lot.id)
                        }
                    }
                }
                .padding(.horizontal, 16)
            }
            .padding(.vertical, 8)

            // Feed content
            ScrollView {
                VStack(spacing: 0) {
                    // Sub-header
                    HStack {
                        Text("Showing reports from last 3 hours")
                            .appFont(size: 12, weight: .semibold)
                            .foregroundColor(AppColors.textMuted)

                        Spacer()

                        HStack(spacing: 4) {
                            Circle()
                                .fill(AppColors.live)
                                .frame(width: 6, height: 6)
                            Text("LIVE")
                                .appFont(size: 10, weight: .bold)
                                .foregroundColor(AppColors.live)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)

                    // Feed items
                    if let feed = viewModel.feed {
                        if feed.sightings.isEmpty {
                            EmptyFeedView()
                                .padding(16)
                        } else {
                            VStack(spacing: 12) {
                                ForEach(Array(feed.sightings.enumerated()), id: \.element.id) { index, sighting in
                                    FeedCardView(
                                        sighting: sighting,
                                        isNewest: index == 0
                                    ) { voteType in
                                        Task {
                                            await viewModel.vote(sightingId: sighting.id, type: voteType)
                                        }
                                    }
                                }

                                // End of window marker
                                HStack(spacing: 12) {
                                    Circle()
                                        .fill(AppColors.border)
                                        .frame(width: 6, height: 6)
                                    Text("End of 3-hour window")
                                        .appFont(size: 12, weight: .bold)
                                        .foregroundColor(AppColors.pillBorder)
                                    Circle()
                                        .fill(AppColors.border)
                                        .frame(width: 6, height: 6)
                                }
                                .padding(.vertical, 24)
                            }
                            .padding(.horizontal, 16)
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

// MARK: - Feed Card

struct FeedCardView: View {
    let sighting: FeedSighting
    let isNewest: Bool
    let onVote: (VoteType) -> Void

    private var isOld: Bool {
        sighting.minutesAgo >= 120
    }

    var body: some View {
        HStack(spacing: 0) {
            // Left accent bar
            if isNewest {
                RoundedRectangle(cornerRadius: 2)
                    .fill(AppColors.accent)
                    .frame(width: 4)
                    .padding(.vertical, 12)
            }

            HStack(alignment: .center, spacing: 16) {
                // Text content
                VStack(alignment: .leading, spacing: 4) {
                    Text(timeText)
                        .appFont(size: 11, weight: .bold)
                        .foregroundColor(isNewest ? AppColors.accent : AppColors.textMuted)

                    Text(sighting.parkingLotCode)
                        .appFont(size: 22, weight: .bold)
                        .foregroundColor(isOld ? AppColors.textSecondary : AppColors.textPrimary)
                        .textCase(.uppercase)
                }

                Spacer()

                // Vote buttons (no container)
                HStack(spacing: 10) {
                    Button {
                        onVote(.upvote)
                    } label: {
                        Image(systemName: "hand.thumbsup.fill")
                            .font(.system(size: 18))
                            .foregroundColor(userVote == .upvote ? AppColors.accent : AppColors.textMuted)
                    }
                    .buttonStyle(PlainButtonStyle())

                    Text("\(sighting.netScore)")
                        .appFont(size: 16, weight: .heavy)
                        .foregroundColor(isOld ? AppColors.textMuted : Color(hex: "334155"))

                    Button {
                        onVote(.downvote)
                    } label: {
                        Image(systemName: "hand.thumbsdown.fill")
                            .font(.system(size: 18))
                            .foregroundColor(userVote == .downvote ? Color(hex: "FCA5A5") : AppColors.pillBorder)
                    }
                    .buttonStyle(PlainButtonStyle())
                }
            }
            .padding(.horizontal, isNewest ? 16 : 20)
            .padding(.vertical, 20)
        }
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(AppColors.cardBackground)
        )
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
    }

    private var timeText: String {
        if sighting.minutesAgo < 60 {
            return "\(sighting.minutesAgo) mins ago"
        } else {
            let hours = sighting.minutesAgo / 60
            return "\(hours) hour\(hours > 1 ? "s" : "") ago"
        }
    }

    private var userVote: VoteType? {
        sighting.userVote
    }
}

// MARK: - Feed Pill (larger, matching Figma)

struct FeedPill: View {
    let text: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(text)
                .appFont(size: 14, weight: .bold)
                .foregroundColor(isSelected ? .white : AppColors.textSecondary)
                .padding(.horizontal, 20)
                .padding(.vertical, 11)
                .background(
                    Capsule()
                        .fill(isSelected ? AppColors.accent : AppColors.cardBackground)
                )
                .overlay(
                    Capsule()
                        .stroke(isSelected ? Color.clear : AppColors.border, lineWidth: 1)
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
                    FeedPill(
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
