//
//  EmailVerificationView.swift
//  TapOut
//
//  TapOut email verification — clean form with green accent.
//

import SwiftUI

struct EmailVerificationView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var email = ""
    @State private var isValidating = false

    var body: some View {
        VStack(spacing: 0) {
            // Back button area
            HStack {
                Button {
                    viewModel.isAuthenticated = false
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(AppColors.textPrimary)
                        .frame(width: 44, height: 44)
                }
                .buttonStyle(PlainButtonStyle())

                Spacer()
            }
            .padding(.horizontal, 12)

            ScrollView {
                VStack(spacing: 32) {
                    // Icon + Header
                    VStack(spacing: 16) {
                        Image(systemName: "p.circle.fill")
                            .font(.system(size: 48, weight: .light))
                            .foregroundColor(AppColors.accent)

                        VStack(spacing: 8) {
                            Text("Verify Your Student Email")
                                .displayFont(size: 24)
                                .foregroundColor(AppColors.textPrimary)
                                .tracking(-0.5)
                                .multilineTextAlignment(.center)
                        }
                    }
                    .padding(.top, 24)

                    // Email input
                    VStack(alignment: .leading, spacing: 12) {
                        Text("UNIVERSITY EMAIL")
                            .appFont(size: 10, weight: .bold)
                            .tracking(1)
                            .foregroundColor(AppColors.textMuted)

                        HStack(spacing: 12) {
                            TextField("yourname@ucdavis.edu", text: $email)
                                .appFont(size: 16, weight: .medium)
                                .foregroundColor(AppColors.textPrimary)
                                .textInputAutocapitalization(.never)
                                .keyboardType(.emailAddress)
                                .autocorrectionDisabled()

                            if !email.isEmpty {
                                Image(systemName: "envelope.fill")
                                    .font(.system(size: 16))
                                    .foregroundColor(isValidEmail ? AppColors.accent : AppColors.textMuted)
                            }
                        }
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(AppColors.cardBackground)
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(
                                    email.isEmpty
                                        ? AppColors.border
                                        : (isValidEmail ? AppColors.accent : AppColors.danger),
                                    lineWidth: 1
                                )
                        )

                        // Validation hint
                        HStack(spacing: 6) {
                            Image(systemName: "info.circle")
                                .font(.system(size: 12))
                            Text("Must use UC Davis email address")
                                .appFont(size: 12)
                        }
                        .foregroundColor(AppColors.textMuted)
                    }
                    .padding(.horizontal, 24)

                    // Submit button
                    Button {
                        Task {
                            isValidating = true
                            _ = await viewModel.verifyEmail(email)
                            isValidating = false
                        }
                    } label: {
                        HStack(spacing: 8) {
                            Text(isValidating ? "Verifying..." : "Submit")
                                .appFont(size: 16, weight: .bold)

                            if !isValidating {
                                Image(systemName: "arrow.right")
                                    .font(.system(size: 16, weight: .bold))
                            }
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(
                            RoundedRectangle(cornerRadius: 9999)
                                .fill(isValidEmail ? AppColors.accent : AppColors.textMuted)
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                    .disabled(!isValidEmail || isValidating)
                    .padding(.horizontal, 24)

                    // Support link
                    Text("Having trouble? **Contact Support**")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textMuted)

                    Spacer(minLength: 40)
                }
            }
        }
        .background(AppColors.background)
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.error ?? "An error occurred")
        }
    }

    private var isValidEmail: Bool {
        email.lowercased().hasSuffix("@ucdavis.edu") && email.count > 12
    }
}

#Preview {
    EmailVerificationView(viewModel: AppViewModel())
}
