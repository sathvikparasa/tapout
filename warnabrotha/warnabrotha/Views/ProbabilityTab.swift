//
//  ProbabilityTab.swift
//  warnabrotha
//
//  Windows 95 style probability display with loading bar and popup-style feed.
//

import SwiftUI

struct ProbabilityTab: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Location selector (if multiple lots)
                if viewModel.parkingLots.count > 1 {
                    Win95LotSelector(
                        lots: viewModel.parkingLots,
                        selectedId: viewModel.selectedLotId
                    ) { lotId in
                        viewModel.selectLot(lotId)
                    }
                    .padding(16)

                    Rectangle()
                        .fill(Win95Colors.buttonShadow.opacity(0.5))
                        .frame(height: 1)
                }

                // Feed section
                VStack(alignment: .leading, spacing: 12) {
                    // Header
                    HStack(spacing: 8) {
                        Image(systemName: "list.bullet")
                            .font(.system(size: 14))
                            .foregroundColor(Win95Colors.titleBarActive)
                        Text("Recent Reports")
                            .win95Font(size: 14)
                            .foregroundColor(Win95Colors.textPrimary)
                        Spacer()

                        Button {
                            Task { await viewModel.refresh() }
                        } label: {
                            HStack(spacing: 4) {
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 12))
                                Text("Refresh")
                                    .win95Font(size: 12)
                            }
                            .foregroundColor(Win95Colors.textPrimary)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(Win95Colors.buttonFace)
                            .beveledBorder(raised: true, width: 1)
                        }
                        .buttonStyle(PlainButtonStyle())
                    }

                    // Feed content
                    if let feed = viewModel.feed {
                        if feed.sightings.isEmpty {
                            Win95EmptyFeed()
                        } else {
                            VStack(spacing: 10) {
                                ForEach(feed.sightings) { sighting in
                                    Win95FeedItem(sighting: sighting) { voteType in
                                        Task {
                                            await viewModel.vote(sightingId: sighting.id, type: voteType)
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        HStack(spacing: 8) {
                            Image(systemName: "hourglass")
                                .font(.system(size: 14))
                            Text("Loading...")
                                .win95Font(size: 14)
                        }
                        .foregroundColor(Win95Colors.textDisabled)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 24)
                    }
                }
                .padding(16)
            }
        }
        .background(Win95Colors.windowBackground)
        .refreshable {
            await viewModel.refresh()
        }
    }
}

// MARK: - Windows 95 Risk Card (Horizontal Card)

struct Win95RiskCard: View {
    let riskLevel: String
    let riskMessage: String

    private var riskColor: Color {
        switch riskLevel {
        case "HIGH": return Win95Colors.dangerRed
        case "MEDIUM": return Win95Colors.warningYellow
        case "LOW": return Win95Colors.safeGreen
        default: return Win95Colors.textDisabled
        }
    }

    private var riskBars: Int {
        switch riskLevel {
        case "HIGH": return 3
        case "MEDIUM": return 2
        case "LOW": return 1
        default: return 2
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            // Risk bars (3 bars of increasing height)
            HStack(alignment: .bottom, spacing: 3) {
                ForEach(1...3, id: \.self) { i in
                    Rectangle()
                        .fill(i <= riskBars ? riskColor : Win95Colors.buttonShadow.opacity(0.3))
                        .frame(width: 8, height: CGFloat(i) * 10)
                }
            }
            .frame(height: 30)

            VStack(alignment: .leading, spacing: 4) {
                Text("\(riskLevel) RISK")
                    .win95Font(size: 14)
                    .foregroundColor(riskColor)

                Text(riskMessage)
                    .win95Font(size: 12)
                    .foregroundColor(Win95Colors.textPrimary)
                    .lineLimit(2)
            }

            Spacer()
        }
        .padding(12)
        .background(Win95Colors.inputBackground)
        .beveledBorder(raised: false, width: 1)
    }
}

// MARK: - Windows 95 Lot Selector

struct Win95LotSelector: View {
    let lots: [ParkingLot]
    let selectedId: Int
    let onSelect: (Int) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Location:")
                .win95Font(size: 13)
                .foregroundColor(Win95Colors.textPrimary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(lots) { lot in
                        Button {
                            onSelect(lot.id)
                        } label: {
                            Text(lot.code)
                                .win95Font(size: 13)
                                .foregroundColor(
                                    lot.id == selectedId
                                        ? .white
                                        : Win95Colors.textPrimary
                                )
                                .padding(.horizontal, 14)
                                .padding(.vertical, 8)
                                .background(
                                    RoundedRectangle(cornerRadius: 4)
                                        .fill(lot.id == selectedId
                                              ? Win95Colors.titleBarActive
                                              : Win95Colors.buttonFace)
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 4)
                                        .strokeBorder(
                                            lot.id == selectedId
                                                ? Color.clear
                                                : Win95Colors.buttonShadow.opacity(0.5),
                                            lineWidth: 1
                                        )
                                )
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
        }
    }
}

// MARK: - Empty Feed (Windows 95 Style)

struct Win95EmptyFeed: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(Win95Colors.textDisabled)

            VStack(spacing: 6) {
                Text("No Reports Today")
                    .win95Font(size: 16)
                    .foregroundColor(Win95Colors.textPrimary)

                Text("No TAPS sightings have been reported in the past 24 hours. Check back later or report a sighting if you spot one!")
                    .win95Font(size: 13)
                    .foregroundColor(Win95Colors.textDisabled)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(24)
        .background(Win95Colors.inputBackground)
        .beveledBorder(raised: false, width: 1)
    }
}

// MARK: - Windows 95 Feed Item (Compact Card Style)

struct Win95FeedItem: View {
    let sighting: FeedSighting
    let onVote: (VoteType) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header row - time and location
            HStack {
                HStack(spacing: 6) {
                    Circle()
                        .fill(timeColor)
                        .frame(width: 8, height: 8)

                    Text("\(sighting.minutesAgo)m ago")
                        .win95Font(size: 12)
                        .foregroundColor(Win95Colors.textPrimary)
                }

                Text("•")
                    .foregroundColor(Win95Colors.textDisabled)

                Text(sighting.parkingLotCode)
                    .win95Font(size: 12)
                    .foregroundColor(Win95Colors.textDisabled)

                Spacer()
            }

            // Message
            if let notes = sighting.notes, !notes.isEmpty {
                Text(notes)
                    .win95Font(size: 14)
                    .foregroundColor(Win95Colors.textPrimary)
                    .lineLimit(2)
            } else {
                Text("TAPS spotted!")
                    .win95Font(size: 14)
                    .foregroundColor(Win95Colors.textPrimary)
            }

            // Voting row
            HStack(spacing: 10) {
                Text("Accurate?")
                    .win95Font(size: 11)
                    .foregroundColor(Win95Colors.textDisabled)

                Spacer()

                Win95VoteButton(
                    title: "Yes (\(sighting.upvotes))",
                    isSelected: sighting.userVote == .upvote,
                    color: Win95Colors.safeGreen
                ) {
                    onVote(.upvote)
                }

                Win95VoteButton(
                    title: "No (\(sighting.downvotes))",
                    isSelected: sighting.userVote == .downvote,
                    color: Win95Colors.dangerRed
                ) {
                    onVote(.downvote)
                }
            }
        }
        .padding(12)
        .background(Win95Colors.inputBackground)
        .beveledBorder(raised: false, width: 1)
    }

    private var timeColor: Color {
        if sighting.minutesAgo < 30 {
            return Win95Colors.dangerRed
        } else if sighting.minutesAgo < 90 {
            return Win95Colors.warningYellow
        } else {
            return Win95Colors.textDisabled
        }
    }
}

struct Win95VoteButton: View {
    let title: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .win95Font(size: 11, weight: isSelected ? .bold : .regular)
                .foregroundColor(isSelected ? Win95Colors.selectionText : Win95Colors.textPrimary)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(isSelected ? color : Win95Colors.buttonFace)
                .beveledBorder(raised: !isSelected, width: 1)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    VStack(spacing: 0) {
        Win95TitleBar(title: "WarnABrotha", icon: "car.fill")
        ProbabilityTab(viewModel: AppViewModel())
    }
    .background(Win95Colors.windowBackground)
}
