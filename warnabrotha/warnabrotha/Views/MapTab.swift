//
//  MapTab.swift
//  TapOut
//
//  TapOut Map — stub view for campus parking map.
//

import SwiftUI

struct MapTab: View {
    var body: some View {
        VStack(spacing: 0) {
            // Top bar
            HStack {
                Text("Campus Map")
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

            // Placeholder content
            Spacer()

            VStack(spacing: 20) {
                Image(systemName: "map")
                    .font(.system(size: 48, weight: .light))
                    .foregroundColor(AppColors.accent)

                VStack(spacing: 8) {
                    Text("Coming Soon")
                        .displayFont(size: 24)
                        .foregroundColor(AppColors.textPrimary)

                    Text("Interactive campus parking map with real-time lot status and TAPS activity.")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                }
            }

            Spacer()
        }
        .background(AppColors.background)
    }
}

#Preview {
    MapTab()
}
