//
//  ScanTab.swift
//  TapOut
//
//  Ticket scanning — Records history list + camera/gallery capture → OCR upload → result display.
//

import SwiftUI
import PhotosUI

struct ScanTab: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        VStack(spacing: 0) {
            ScanHeader(viewModel: viewModel)

            switch viewModel.scanSubTab {
            case .records:
                TicketHistoryView(viewModel: viewModel)
            case .scanner:
                scannerContent
            }
        }
        .background(AppColors.background)
    }

    @ViewBuilder
    private var scannerContent: some View {
        switch viewModel.scanState {
        case .idle:
            ScanIdleView(viewModel: viewModel)
        case .preview:
            ScanPreviewView(viewModel: viewModel)
        case .processing:
            ScanProcessingView()
        case .success:
            ScanSuccessView(viewModel: viewModel)
        case .error:
            ScanErrorView(viewModel: viewModel)
        }
    }
}

// MARK: - Shared Header

private struct ScanHeader: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Branding + title
            VStack(alignment: .leading, spacing: 4) {
                (Text("Tap")
                    .foregroundColor(AppColors.textPrimary)
                + Text("Out")
                    .foregroundColor(AppColors.accent))
                    .appFont(size: 11, weight: .bold)

                Text("Scan Ticket")
                    .appFont(size: 30, weight: .heavy)
                    .foregroundColor(AppColors.textPrimary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 24)
            .padding(.top, 12)
            .padding(.bottom, 12)

            // Underline tab bar
            HStack(spacing: 0) {
                ScanTabButton(label: "Scanner", isActive: viewModel.scanSubTab == .scanner) {
                    viewModel.scanSubTab = .scanner
                }
                ScanTabButton(label: "Records", isActive: viewModel.scanSubTab == .records) {
                    viewModel.scanSubTab = .records
                }
            }
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(AppColors.border)
                    .frame(height: 1)
            }
        }
    }
}

private struct ScanTabButton: View {
    let label: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 0) {
                Text(label)
                    .appFont(size: 15, weight: .bold)
                    .foregroundColor(isActive ? AppColors.accent : AppColors.textMuted)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 10)

                Rectangle()
                    .fill(isActive ? AppColors.accent : Color.clear)
                    .frame(height: 2)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

// MARK: - Ticket History (Records Tab)

private struct TicketHistoryView: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        if viewModel.ticketHistory.isEmpty {
            VStack(spacing: 12) {
                Image(systemName: "doc.text.magnifyingglass")
                    .font(.system(size: 40, weight: .light))
                    .foregroundColor(AppColors.textMuted)

                Text("No tickets scanned yet")
                    .appFont(size: 16, weight: .medium)
                    .foregroundColor(AppColors.textSecondary)

                Text("Scan a parking ticket to see it here.")
                    .appFont(size: 13)
                    .foregroundColor(AppColors.textMuted)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .padding(.top, 80)
        } else {
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(viewModel.ticketHistory) { entry in
                        TicketHistoryRow(entry: entry)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.top, 16)
                .padding(.bottom, 32)
            }
        }
    }
}

private struct TicketHistoryRow: View {
    let entry: TicketHistoryEntry

    private var displayLot: String {
        (entry.lotCode ?? entry.lotName ?? entry.ticketLocation ?? "Unknown").uppercased()
    }

    private var displayDate: String {
        if let d = entry.ticketDate { return d }
        let f = DateFormatter(); f.dateStyle = .short; f.timeStyle = .none
        return f.string(from: entry.scannedAt)
    }

    private var displayTime: String {
        if let t = entry.ticketTime { return t }
        let f = DateFormatter(); f.dateStyle = .none; f.timeStyle = .short
        return f.string(from: entry.scannedAt)
    }

    var body: some View {
        HStack(alignment: .center, spacing: 16) {
            // Left: time above, lot code below — mirrors FeedCardView
            VStack(alignment: .leading, spacing: 4) {
                Text(displayTime)
                    .appFont(size: 11, weight: .bold)
                    .foregroundColor(AppColors.accent)

                Text(displayLot)
                    .appFont(size: 22, weight: .bold)
                    .foregroundColor(AppColors.textPrimary)
                    .lineLimit(1)
            }

            Spacer()

            // Right: date, then price below
            VStack(alignment: .trailing, spacing: 4) {
                Text(displayDate)
                    .appFont(size: 14, weight: .bold)
                    .foregroundColor(AppColors.textMuted)
                if let amount = entry.ticketAmount {
                    Text(amount)
                        .appFont(size: 14, weight: .bold)
                        .foregroundColor(AppColors.textMuted)
                }
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 20)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(AppColors.cardBackground)
        )
        .shadow(color: .black.opacity(0.04), radius: 4, y: 2)
    }
}

// MARK: - Idle State

private struct ScanIdleView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var showCamera = false
    @State private var showPhotoPicker = false
    @State private var selectedPhotoItem: PhotosPickerItem? = nil

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            VStack(spacing: 32) {
                // Camera icon
                ZStack {
                    Circle()
                        .stroke(AppColors.border, lineWidth: 2)
                        .frame(width: 120, height: 120)

                    Image(systemName: "doc.viewfinder")
                        .font(.system(size: 48, weight: .light))
                        .foregroundColor(AppColors.accent)
                }

                VStack(spacing: 8) {
                    Text("Scan a Ticket")
                        .displayFont(size: 24)
                        .foregroundColor(AppColors.textPrimary)

                    Text("Take a photo of your parking ticket to auto-report TAPS")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 40)
                }

                VStack(spacing: 12) {
                    // Take Photo button
                    Button {
                        showCamera = true
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: "camera.fill")
                                .font(.system(size: 18, weight: .semibold))
                            Text("Take Photo")
                                .appFont(size: 16, weight: .bold)
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(AppColors.accent)
                        )
                    }
                    .buttonStyle(PlainButtonStyle())

                    // Choose from Library button
                    PhotosPicker(
                        selection: $selectedPhotoItem,
                        matching: .images,
                        photoLibrary: .shared()
                    ) {
                        HStack(spacing: 8) {
                            Image(systemName: "photo.on.rectangle")
                                .font(.system(size: 18, weight: .semibold))
                            Text("Choose from Library")
                                .appFont(size: 16, weight: .bold)
                        }
                        .foregroundColor(AppColors.accent)
                        .frame(maxWidth: .infinity)
                        .frame(height: 56)
                        .background(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(AppColors.accent, lineWidth: 2)
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                    .onChange(of: selectedPhotoItem) { _, newItem in
                        guard let newItem else { return }
                        Task {
                            if let data = try? await newItem.loadTransferable(type: Data.self) {
                                viewModel.selectScanImage(data)
                            }
                        }
                    }
                }
                .padding(.horizontal, 24)
            }

            Spacer()
        }
        .fullScreenCover(isPresented: $showCamera) {
            CameraView { imageData in
                viewModel.selectScanImage(imageData)
            }
            .ignoresSafeArea()
        }
    }
}

// MARK: - Preview State

private struct ScanPreviewView: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            if let data = viewModel.scanImageData, let uiImage = UIImage(data: data) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 300)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .shadow(color: .black.opacity(0.1), radius: 8, y: 4)
                    .padding(.horizontal, 24)
            }

            Spacer()

            VStack(spacing: 12) {
                PrimaryButton(
                    title: "Submit Ticket",
                    icon: "arrow.up.circle.fill",
                    action: {
                        Task { await viewModel.submitTicketScan() }
                    }
                )

                Button {
                    viewModel.resetScan()
                } label: {
                    Text("Retake")
                        .appFont(size: 16, weight: .semibold)
                        .foregroundColor(AppColors.textSecondary)
                }
                .buttonStyle(PlainButtonStyle())
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 32)
        }
    }
}

// MARK: - Processing State

private struct ScanProcessingView: View {
    var body: some View {
        VStack(spacing: 16) {
            Spacer()

            ProgressView()
                .scaleEffect(1.5)
                .tint(AppColors.accent)

            Text("Reading ticket...")
                .displayFont(size: 20)
                .foregroundColor(AppColors.textPrimary)

            Text("Extracting date, time, and location")
                .appFont(size: 14)
                .foregroundColor(AppColors.textSecondary)

            Spacer()
        }
    }
}

// MARK: - Success State

private struct ScanSuccessView: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                Spacer(minLength: 32)

                // Success icon
                ZStack {
                    Circle()
                        .fill(AppColors.accent.opacity(0.1))
                        .frame(width: 80, height: 80)

                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 40))
                        .foregroundColor(AppColors.accent)
                }

                if let result = viewModel.scanResult {
                    // Ticket Details card
                    VStack(alignment: .leading, spacing: 16) {
                        Text("TICKET DETAILS")
                            .appFont(size: 10, weight: .bold)
                            .tracking(1)
                            .foregroundColor(AppColors.textMuted)

                        VStack(spacing: 12) {
                            if let date = result.ticketDate {
                                DetailRow(label: "Date", value: date, icon: "calendar")
                            }
                            if let time = result.ticketTime {
                                DetailRow(label: "Time", value: time, icon: "clock")
                            }
                            if let location = result.ticketLocation {
                                DetailRow(label: "Location", value: location, icon: "mappin.circle")
                            }
                            if let lotName = result.mappedLotName {
                                DetailRow(label: "Mapped Lot", value: lotName, icon: "car.fill")
                            }
                        }
                    }
                    .padding(20)
                    .cardStyle(cornerRadius: 16)
                    .padding(.horizontal, 24)

                    // Result message
                    resultMessageView(result: result)
                        .padding(.horizontal, 24)
                }

                PrimaryButton(
                    title: "Scan Another",
                    icon: "doc.viewfinder",
                    action: { viewModel.resetScan() }
                )
                .padding(.horizontal, 24)

                Button {
                    viewModel.resetScan()
                    viewModel.scanSubTab = .records
                } label: {
                    Text("View History")
                        .appFont(size: 14, weight: .semibold)
                        .foregroundColor(AppColors.accent)
                }
                .buttonStyle(PlainButtonStyle())

                Spacer(minLength: 32)
            }
        }
    }

    @ViewBuilder
    private func resultMessageView(result: TicketScanResponse) -> some View {
        if result.isRecent && result.sightingId != nil {
            HStack(spacing: 8) {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(AppColors.accent)
                Text("TAPS report created! \(result.usersNotified) users notified.")
                    .appFont(size: 14, weight: .medium)
                    .foregroundColor(AppColors.accent)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(AppColors.accent.opacity(0.1))
            )
        } else if !result.isRecent {
            HStack(spacing: 8) {
                Image(systemName: "clock.fill")
                    .foregroundColor(AppColors.textMuted)
                Text("Ticket recorded — Too old for a live report")
                    .appFont(size: 14, weight: .medium)
                    .foregroundColor(AppColors.textMuted)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(AppColors.background)
            )
        } else if result.mappedLotId == nil {
            HStack(spacing: 8) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(AppColors.danger)
                Text("Location not recognized")
                    .appFont(size: 14, weight: .medium)
                    .foregroundColor(AppColors.danger)
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(AppColors.dangerLight)
            )
        }
    }
}

// MARK: - Error State

private struct ScanErrorView: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            ZStack {
                Circle()
                    .fill(AppColors.dangerLight)
                    .frame(width: 80, height: 80)

                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 40))
                    .foregroundColor(AppColors.danger)
            }

            VStack(spacing: 8) {
                Text("Could not read ticket")
                    .displayFont(size: 20)
                    .foregroundColor(AppColors.textPrimary)

                Text(viewModel.scanError ?? "Make sure the photo is clear and shows a UC Davis parking ticket.")
                    .appFont(size: 14)
                    .foregroundColor(AppColors.textSecondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
            }

            PrimaryButton(
                title: "Try Again",
                icon: "arrow.counterclockwise",
                action: { viewModel.resetScan() }
            )
            .padding(.horizontal, 24)

            Spacer()
        }
    }
}

// MARK: - Detail Row

private struct DetailRow: View {
    let label: String
    let value: String
    let icon: String

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(AppColors.accent)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .appFont(size: 10, weight: .bold)
                    .foregroundColor(AppColors.textMuted)
                    .textCase(.uppercase)
                Text(value)
                    .appFont(size: 14, weight: .medium)
                    .foregroundColor(AppColors.textPrimary)
            }

            Spacer()
        }
    }
}

// MARK: - Camera View (UIImagePickerController wrapper)

struct CameraView: UIViewControllerRepresentable {
    let onCapture: (Data) -> Void
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = .camera
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(onCapture: onCapture, dismiss: dismiss)
    }

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let onCapture: (Data) -> Void
        let dismiss: DismissAction

        init(onCapture: @escaping (Data) -> Void, dismiss: DismissAction) {
            self.onCapture = onCapture
            self.dismiss = dismiss
        }

        func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]) {
            if let image = info[.originalImage] as? UIImage,
               let data = image.jpegData(compressionQuality: 0.8) {
                onCapture(data)
            }
            dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            dismiss()
        }
    }
}

#Preview {
    ScanTab(viewModel: AppViewModel())
}
