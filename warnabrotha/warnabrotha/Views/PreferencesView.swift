//
//  PreferencesView.swift
//  TapOut
//
//  Preferences sheet — lets user choose their parking payment app.
//

import SwiftUI

struct PreferencesView: View {
    @State private var selected: ParkingPaymentApp = ParkingPaymentApp.preferred
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {

            // Header
            HStack(alignment: .center) {
                Text("Preferences")
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

            // Section
            VStack(alignment: .leading, spacing: 12) {
                Text("What Parking app do you use?")
                    .appFont(size: 16, weight: .bold)
                    .foregroundColor(AppColors.accent)
                    .padding(.horizontal, 4)

                appCard(name: "AMP Parking",  imageName: "amp_parking_logo",  app: .ampPark)
                appCard(name: "Honk Mobile",  imageName: "honk_mobile_logo",  app: .honkMobile)
            }

            tipCard
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

    // MARK: - App Selection Card

    private func appCard(name: String, imageName: String, app: ParkingPaymentApp) -> some View {
        let isSelected = selected == app

        return Button {
            selected = app
            ParkingPaymentApp.setPreferred(app)
            UIImpactFeedbackGenerator(style: .light).impactOccurred()
        } label: {
            ZStack {
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.white)
                    .shadow(color: Color.black.opacity(0.05), radius: 1, x: 0, y: 1)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(
                                isSelected ? AppColors.accent.opacity(0.4) : AppColors.borderLight,
                                lineWidth: isSelected ? 1.5 : 1
                            )
                    )

                HStack(spacing: 0) {
                    Image(imageName)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 55, height: 55)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .padding(.leading, 24)

                    Spacer().frame(width: 23)

                    Text(name)
                        .appFont(size: 18, weight: .bold)
                        .foregroundColor(AppColors.textPrimary)
                        .lineLimit(1)

                    Spacer()

                    ZStack {
                        Circle()
                            .fill(isSelected ? AppColors.accent : AppColors.border)
                            .frame(width: 36, height: 36)
                        if isSelected {
                            Image(systemName: "checkmark")
                                .font(.system(size: 13, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    .padding(.trailing, 18)
                }
            }
            .frame(height: 85)
        }
        .buttonStyle(PlainButtonStyle())
        .animation(.easeInOut(duration: 0.15), value: isSelected)
    }

    // MARK: - Tip Card

    private var tipCard: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle()
                    .fill(AppColors.accent)
                    .frame(width: 22, height: 22)
                Text("i")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.white)
            }
            .padding(.top, 1)

            Text("Selecting your parking app allows our app to take you directly to your desired parking app, decreasing the time it takes you to pay for parking after a report.")
                .appFont(size: 14)
                .foregroundColor(AppColors.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(AppColors.accent.opacity(0.12))
        )
    }
}

#Preview {
    PreferencesView(onDismiss: {})
}
