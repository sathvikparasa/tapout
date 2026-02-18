//
//  EmailVerificationView.swift
//  TapOut
//
//  TapOut email verification — two-step OTP flow.
//

import SwiftUI

struct EmailVerificationView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var email = ""
    @State private var otpCode = ""
    @State private var isValidating = false

    var body: some View {
        VStack(spacing: 0) {
            // Back button
            HStack {
                Button {
                    if viewModel.otpStep == .codeInput {
                        otpCode = ""
                        viewModel.changeEmail()
                    } else {
                        viewModel.isAuthenticated = false
                    }
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

            // Content
            ScrollView {
                VStack(spacing: 0) {
                    Spacer(minLength: 32)

                    switch viewModel.otpStep {
                    case .emailInput:
                        emailInputStep
                    case .codeInput:
                        otpInputStep
                    }

                    Spacer(minLength: 40)
                }
            }

            // Privacy notice
            HStack(spacing: 8) {
                Image(systemName: "lock.fill")
                    .font(.system(size: 12))
                Text("We don't store your email address")
                    .appFont(size: 11)
            }
            .foregroundColor(AppColors.textMuted)
            .padding(.bottom, 24)
        }
        .background(AppColors.background)
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(viewModel.error ?? "An error occurred")
        }
    }

    // MARK: - Step 1: Email Input

    private var emailInputStep: some View {
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

                    Text("Enter your UC Davis email to continue")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textSecondary)
                }
            }

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
                        Image(systemName: isValidEmail ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(isValidEmail ? AppColors.accent : AppColors.danger)
                    }
                }
                .padding(16)
                .background(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(AppColors.cardBackground)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
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

            // Send Code button
            Button {
                Task {
                    isValidating = true
                    await viewModel.sendOTP(email)
                    isValidating = false
                }
            } label: {
                HStack(spacing: 8) {
                    Text(isValidating ? "Sending..." : "Send Code")
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

            Text("Having trouble? **Contact Support**")
                .appFont(size: 14)
                .foregroundColor(AppColors.textMuted)
        }
    }

    // MARK: - Step 2: OTP Code Input

    private var otpInputStep: some View {
        VStack(spacing: 32) {
            // Icon + Header
            VStack(spacing: 16) {
                Image(systemName: "lock.shield.fill")
                    .font(.system(size: 48, weight: .light))
                    .foregroundColor(AppColors.accent)

                VStack(spacing: 8) {
                    Text("Enter Verification Code")
                        .displayFont(size: 24)
                        .foregroundColor(AppColors.textPrimary)
                        .tracking(-0.5)
                        .multilineTextAlignment(.center)

                    Text("Code sent to \(viewModel.otpEmail)")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textSecondary)
                }
            }

            // OTP input
            VStack(alignment: .leading, spacing: 12) {
                Text("6-DIGIT CODE")
                    .appFont(size: 10, weight: .bold)
                    .tracking(1)
                    .foregroundColor(AppColors.textMuted)

                TextField("000000", text: $otpCode)
                    .appFont(size: 28, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)
                    .multilineTextAlignment(.center)
                    .keyboardType(.numberPad)
                    .autocorrectionDisabled()
                    .padding(16)
                    .background(
                        RoundedRectangle(cornerRadius: 16)
                            .fill(AppColors.cardBackground)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(
                                otpCode.count == 6 ? AppColors.accent : AppColors.border,
                                lineWidth: 1
                            )
                    )
                    .onChange(of: otpCode) { _, newValue in
                        let filtered = String(newValue.filter { $0.isNumber }.prefix(6))
                        if filtered != newValue {
                            otpCode = filtered
                        }
                    }

                // Error display
                if let error = viewModel.error, viewModel.showError {
                    HStack(spacing: 6) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 12))
                        Text(error)
                            .appFont(size: 12)
                    }
                    .foregroundColor(AppColors.danger)
                }
            }
            .padding(.horizontal, 24)

            // Verify button
            Button {
                Task {
                    isValidating = true
                    await viewModel.verifyOTP(otpCode)
                    isValidating = false
                }
            } label: {
                HStack(spacing: 8) {
                    Text(isValidating ? "Verifying..." : "Verify")
                        .appFont(size: 16, weight: .bold)
                    if !isValidating {
                        Image(systemName: "checkmark")
                            .font(.system(size: 16, weight: .bold))
                    }
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .frame(height: 56)
                .background(
                    RoundedRectangle(cornerRadius: 9999)
                        .fill(otpCode.count == 6 ? AppColors.accent : AppColors.textMuted)
                )
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(otpCode.count != 6 || isValidating)
            .padding(.horizontal, 24)

            // Resend / Change email
            VStack(spacing: 12) {
                if viewModel.canResendOTP {
                    Button {
                        Task { await viewModel.resendOTP() }
                    } label: {
                        Text("Resend Code")
                            .appFont(size: 14, weight: .semibold)
                            .foregroundColor(AppColors.accent)
                    }
                    .buttonStyle(PlainButtonStyle())
                } else if viewModel.resendCooldown > 0 {
                    Text("Resend in \(viewModel.resendCooldown)s")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textMuted)
                }

                Button {
                    otpCode = ""
                    viewModel.changeEmail()
                } label: {
                    Text("Change Email")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textMuted)
                        .underline()
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
    }

    private var isValidEmail: Bool {
        email.lowercased().hasSuffix("@ucdavis.edu") && email.count > 12
    }
}

#Preview {
    EmailVerificationView(viewModel: AppViewModel())
}
