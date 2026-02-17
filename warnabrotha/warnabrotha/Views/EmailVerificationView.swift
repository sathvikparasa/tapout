//
//  EmailVerificationView.swift
//  TapOut
//
//  Windows 95 style email verification - two-step OTP flow.
//

import SwiftUI

struct EmailVerificationView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var email = ""
    @State private var otpCode = ""
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
            .padding(.horizontal, 8)
            .padding(.vertical, 6)
            .background(
                LinearGradient(
                    colors: [Win95Colors.titleBarActive, Win95Colors.titleBarActive.opacity(0.85)],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )

            // Content
            VStack(spacing: 0) {
                Spacer()

                switch viewModel.otpStep {
                case .emailInput:
                    emailInputStep
                case .codeInput:
                    otpInputStep
                }

                Spacer()

                // Privacy notice
                HStack(spacing: 8) {
                    Image(systemName: "lock.fill")
                        .font(.system(size: 12))
                    Text("We don't store your email address")
                        .win95Font(size: 11)
                }
                .foregroundColor(Win95Colors.textDisabled)
                .padding(.bottom, 24)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Win95Colors.windowBackground)
        }
    }

    // MARK: - Step 1: Email Input

    private var emailInputStep: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "envelope.fill")
                    .font(.system(size: 40))
                    .foregroundColor(Win95Colors.titleBarActive)

                Text("Email Verification")
                    .win95Font(size: 18)
                    .foregroundColor(Win95Colors.textPrimary)

                Text("Enter your UC Davis email to continue")
                    .win95Font(size: 13)
                    .foregroundColor(Win95Colors.textDisabled)
            }

            // Email input
            VStack(alignment: .leading, spacing: 8) {
                Text("UC Davis Email:")
                    .win95Font(size: 13)
                    .foregroundColor(Win95Colors.textPrimary)

                TextField("you@ucdavis.edu", text: $email)
                    .win95Font(size: 15)
                    .foregroundColor(Win95Colors.textPrimary)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .autocorrectionDisabled()
                    .padding(12)
                    .background(Win95Colors.inputBackground)
                    .beveledBorder(raised: false, width: 1)

                // Validation
                if !email.isEmpty {
                    HStack(spacing: 6) {
                        Image(systemName: isValidEmail ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .font(.system(size: 12))
                        Text(isValidEmail ? "Valid email" : "Must end with @ucdavis.edu")
                            .win95Font(size: 12)
                    }
                    .foregroundColor(isValidEmail ? Win95Colors.safeGreen : Win95Colors.dangerRed)
                }
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
                Text(isValidating ? "Sending..." : "Send Code")
                    .win95Font(size: 16)
                    .foregroundColor(.white)
                    .frame(width: 200, height: 48)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(isValidEmail ? Win95Colors.titleBarActive : Win95Colors.buttonShadow)
                    )
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(!isValidEmail || isValidating)
        }
    }

    // MARK: - Step 2: OTP Code Input

    private var otpInputStep: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 8) {
                Image(systemName: "lock.shield.fill")
                    .font(.system(size: 40))
                    .foregroundColor(Win95Colors.titleBarActive)

                Text("Enter Verification Code")
                    .win95Font(size: 18)
                    .foregroundColor(Win95Colors.textPrimary)

                Text("Code sent to \(viewModel.otpEmail)")
                    .win95Font(size: 13)
                    .foregroundColor(Win95Colors.textDisabled)
            }

            // OTP input
            VStack(alignment: .leading, spacing: 8) {
                Text("6-Digit Code:")
                    .win95Font(size: 13)
                    .foregroundColor(Win95Colors.textPrimary)

                TextField("000000", text: $otpCode)
                    .win95Font(size: 24)
                    .foregroundColor(Win95Colors.textPrimary)
                    .multilineTextAlignment(.center)
                    .keyboardType(.numberPad)
                    .autocorrectionDisabled()
                    .padding(12)
                    .background(Win95Colors.inputBackground)
                    .beveledBorder(raised: false, width: 1)
                    .onChange(of: otpCode) { _, newValue in
                        // Limit to 6 digits
                        let filtered = String(newValue.filter { $0.isNumber }.prefix(6))
                        if filtered != newValue {
                            otpCode = filtered
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

                // Error display
                if let error = viewModel.error, viewModel.showError {
                    HStack(spacing: 6) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 12))
                        Text(error)
                            .win95Font(size: 12)
                    }
                    .foregroundColor(Win95Colors.dangerRed)
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
                Text(isValidating ? "Verifying..." : "Verify")
                    .win95Font(size: 16)
                    .foregroundColor(.white)
                    .frame(width: 200, height: 48)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(otpCode.count == 6 ? Win95Colors.titleBarActive : Win95Colors.buttonShadow)
                    )
            }
            .buttonStyle(PlainButtonStyle())
            .disabled(otpCode.count != 6 || isValidating)

            // Resend / Change email
            VStack(spacing: 12) {
                if viewModel.canResendOTP {
                    Button {
                        Task {
                            await viewModel.resendOTP()
                        }
                    } label: {
                        Text("Resend Code")
                            .win95Font(size: 13)
                            .foregroundColor(Win95Colors.titleBarActive)
                    }
                    .buttonStyle(PlainButtonStyle())
                } else if viewModel.resendCooldown > 0 {
                    Text("Resend in \(viewModel.resendCooldown)s")
                        .win95Font(size: 13)
                        .foregroundColor(Win95Colors.textDisabled)
                }

                Button {
                    otpCode = ""
                    viewModel.changeEmail()
                } label: {
                    Text("Change Email")
                        .win95Font(size: 13)
                        .foregroundColor(Win95Colors.textDisabled)
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
