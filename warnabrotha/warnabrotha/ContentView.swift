//
//  ContentView.swift
//  TapOut
//
//  Main content view with TapOut design.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = AppViewModel()
    @State private var selectedTab = 0
    @State private var hideTabBar = false

    var body: some View {
        ZStack {
            AppColors.background
                .ignoresSafeArea()

            Group {
                if !viewModel.isAuthenticated {
                    WelcomeView(viewModel: viewModel)
                } else if viewModel.showEmailVerification && !viewModel.isEmailVerified {
                    EmailVerificationView(viewModel: viewModel)
                } else {
                    VStack(spacing: 0) {
                        Group {
                            switch selectedTab {
                            case 0:
                                ButtonsTab(viewModel: viewModel, selectedTab: $selectedTab)
                            case 1:
                                ProbabilityTab(viewModel: viewModel)
                            case 2:
                                ScanTab(viewModel: viewModel)
                            case 3:
                                MapTab(viewModel: viewModel, hideTabBar: $hideTabBar)
                            default:
                                ButtonsTab(viewModel: viewModel, selectedTab: $selectedTab)
                            }
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)

                        AppTabBar(
                            selectedTab: $selectedTab,
                            feedBadgeCount: viewModel.unreadNotificationCount
                        )
                        .opacity(hideTabBar ? 0 : 1)
                        .allowsHitTesting(!hideTabBar)
                    }
                    .onChange(of: selectedTab) { _, tab in
                        if tab == 1 {
                            Task { await viewModel.markAllNotificationsRead() }
                        }
                        if tab != 3 {
                            hideTabBar = false
                        }
                    }
                }
            }
            .overlay {
                if viewModel.isLoading {
                    LoadingOverlay()
                }
            }
        }
        .alert("Enable Time-Sensitive Notifications", isPresented: $viewModel.showTimeSensitivePrompt) {
            Button("Open Settings") {
                if let url = URL(string: UIApplication.openNotificationSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("Not Now", role: .cancel) {}
        } message: {
            Text("Allow warnabrotha to send time-sensitive alerts so TAPS warnings reach you even when Focus mode is on.")
        }
    }
}

// MARK: - Tab Bar

struct AppTabBar: View {
    @Binding var selectedTab: Int
    var feedBadgeCount: Int = 0

    var body: some View {
        HStack(spacing: 0) {
            TabBarItem(
                icon: "house",
                label: "Home",
                isSelected: selectedTab == 0
            ) {
                selectedTab = 0
            }

            TabBarItem(
                icon: "dot.radiowaves.left.and.right",
                label: "Feed",
                isSelected: selectedTab == 1,
                badgeCount: feedBadgeCount
            ) {
                selectedTab = 1
            }

            TabBarItem(
                icon: "doc.viewfinder",
                label: "Scan",
                isSelected: selectedTab == 2
            ) {
                selectedTab = 2
            }

            TabBarItem(
                icon: "map",
                label: "Map",
                isSelected: selectedTab == 3
            ) {
                selectedTab = 3
            }
        }
        .padding(.top, 12)
        .padding(.bottom, 8)
        .padding(.horizontal, 40)
        .background(
            AppColors.frosted
                .ignoresSafeArea(edges: .bottom)
        )
        .background(
            Rectangle()
                .fill(.ultraThinMaterial)
                .ignoresSafeArea(edges: .bottom)
        )
        .overlay(alignment: .top) {
            Rectangle()
                .fill(AppColors.border.opacity(0.5))
                .frame(height: 1)
        }
    }
}

struct TabBarItem: View {
    let icon: String
    let label: String
    let isSelected: Bool
    var badgeCount: Int = 0
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                ZStack(alignment: .topTrailing) {
                    Image(systemName: icon)
                        .font(.system(size: 24, weight: isSelected ? .bold : .regular))
                        .frame(width: 28, height: 28)

                    if badgeCount > 0 {
                        Text("\(badgeCount)")
                            .appFont(size: 10, weight: .bold)
                            .foregroundColor(.white)
                            .frame(minWidth: 16, minHeight: 16)
                            .background(Circle().fill(AppColors.dangerBright))
                            .offset(x: 8, y: -4)
                    }
                }
                .frame(width: 28, height: 28)

                Text(label)
                    .appFont(size: 10, weight: isSelected ? .bold : .medium)
                    .frame(height: 13)
            }
            .foregroundColor(isSelected ? AppColors.accent : AppColors.textMuted)
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Welcome View

struct WelcomeView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var isRegistering = false

    var body: some View {
        ZStack {
            Color.white
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Logo + branding
                VStack(spacing: 16) {
                    Image(systemName: "checkmark.shield.fill")
                        .font(.system(size: 48, weight: .light))
                        .foregroundColor(AppColors.accent)

                    VStack(spacing: 8) {
                        (Text("Tap")
                            .foregroundColor(AppColors.textPrimary)
                        + Text("Out")
                            .foregroundColor(AppColors.accent))
                            .displayFont(size: 36)
                            .tracking(-1)

                        Text("Tap out of parking")
                            .appFont(size: 16, weight: .medium)
                            .foregroundColor(AppColors.textSecondary)
                    }
                }

                Spacer()
                    .frame(height: 48)

                // Feature list
                VStack(spacing: 0) {
                    FeatureRow(
                        icon: "bell.badge.fill",
                        title: "Real-time alerts",
                        description: "Get notified when TAPS is spotted near your car"
                    )
                    FeatureRow(
                        icon: "person.2.fill",
                        title: "Community-powered",
                        description: "Reports from fellow UC Davis students"
                    )
                    FeatureRow(
                        icon: "timer",
                        title: "Check in/out tracking",
                        description: "Track your parking sessions easily"
                    )
                    FeatureRow(
                        icon: "map.fill",
                        title: "Campus-wide coverage",
                        description: "All major parking structures covered"
                    )
                }
                .padding(16)
                .background(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(AppColors.accent.opacity(0.05))
                )
                .padding(.horizontal, 24)

                Spacer()

                // CTA
                VStack(spacing: 16) {
                    Button {
                        Task {
                            isRegistering = true
                            await viewModel.register()
                            isRegistering = false
                        }
                    } label: {
                        Text(isRegistering ? "Please wait..." : "Get Started")
                            .appFont(size: 16, weight: .bold)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 56)
                            .background(
                                RoundedRectangle(cornerRadius: 9999)
                                    .fill(AppColors.accent)
                            )
                    }
                    .buttonStyle(PlainButtonStyle())
                    .disabled(isRegistering)
                    .opacity(isRegistering ? 0.7 : 1)
                    .padding(.horizontal, 24)

//                    Text("Already have an account? **Log In**")
//                        .appFont(size: 14)
//                        .foregroundColor(AppColors.textSecondary)
                }
                .padding(.bottom, 48)
            }
        }
        .alert("Registration Failed", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) { viewModel.showError = false }
        } message: {
            Text(viewModel.error ?? "Could not connect. Please check your connection and try again.")
        }
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(AppColors.accent)
                .frame(width: 40, height: 40)
                .background(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(AppColors.accentLight)
                )

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .appFont(size: 14, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)
                Text(description)
                    .appFont(size: 12)
                    .foregroundColor(AppColors.textSecondary)
            }

            Spacer()
        }
        .padding(.vertical, 12)
    }
}

// MARK: - Loading Overlay

struct LoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.2)
                .ignoresSafeArea()

            VStack(spacing: 16) {
                ProgressView()
                    .scaleEffect(1.2)
                    .tint(AppColors.accent)

                Text("Loading...")
                    .appFont(size: 14, weight: .medium)
                    .foregroundColor(AppColors.textSecondary)
            }
            .padding(32)
            .background(
                RoundedRectangle(cornerRadius: 20)
                    .fill(.ultraThinMaterial)
            )
        }
    }
}

#Preview {
    ContentView()
}
