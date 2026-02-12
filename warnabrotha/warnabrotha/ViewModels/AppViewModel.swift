//
//  AppViewModel.swift
//  warnabrotha
//
//  Main view model managing app state and API interactions.
//

import Foundation
import SwiftUI

@MainActor
class AppViewModel: ObservableObject {
    // MARK: - Published State

    // Auth state
    @Published var isAuthenticated = false
    @Published var isEmailVerified = false
    @Published var showEmailVerification = false

    // Parking state
    @Published var parkingLots: [ParkingLot] = []
    @Published var selectedLot: ParkingLotWithStats?
    @Published var currentSession: ParkingSession?
    var isParked: Bool { currentSession != nil }

    // Feed state
    @Published var feed: FeedResponse?
    @Published var allFeeds: AllFeedsResponse?

    // Prediction state
    @Published var prediction: PredictionResponse?
    @Published var displayedProbability: Double = 0
    @Published var isAnimatingProbability = false

    // Notification state
    @Published var notificationPermissionGranted = false
    @Published var unreadNotificationCount = 0

    // UI state
    @Published var isLoading = false
    @Published var error: String?
    @Published var showError = false
    @Published var showConfirmation = false
    @Published var confirmationMessage = ""

    // Currently selected lot ID (default to first lot)
    @Published var selectedLotId: Int = 1 {
        didSet {
            UserDefaults.standard.set(selectedLotId, forKey: "selectedParkingLotId")
        }
    }

    private let api = APIClient.shared
    private let keychain = KeychainService.shared

    // MARK: - Initialization

    init() {
        // Check if we have a token
        if keychain.getToken() != nil {
            isAuthenticated = true
            Task {
                await checkAuthAndLoad()
            }
        }
    }

    private func checkAuthAndLoad() async {
        do {
            _ = try await api.getDeviceInfo()
            await loadInitialData()
        } catch {
            // Token is stale or device no longer exists — force re-registration
            isAuthenticated = false
            keychain.clearAll()
        }
    }

    // MARK: - Authentication

    func register() async {
        isLoading = true
        error = nil

        do {
            _ = try await api.register()
            isAuthenticated = true
            showEmailVerification = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func verifyEmail(_ email: String) async -> Bool {
        isLoading = true
        error = nil

        do {
            let response = try await api.verifyEmail(email)
            if response.emailVerified {
                isEmailVerified = true
                showEmailVerification = false
                await loadInitialData()
                await requestNotificationPermission()
                return true
            } else {
                self.error = response.message
                showError = true
                return false
            }
        } catch {
            self.error = error.localizedDescription
            showError = true
            return false
        }
    }

    func checkAuthStatus() async {
        guard keychain.getToken() != nil else {
            isAuthenticated = false
            return
        }

        do {
            let device = try await api.getDeviceInfo()
            isAuthenticated = true
            isEmailVerified = device.emailVerified

            if !isEmailVerified {
                showEmailVerification = true
            }
        } catch {
            // Token might be invalid
            isAuthenticated = false
            keychain.clearAll()
        }
    }

    // MARK: - Data Loading

    func loadInitialData() async {
        isLoading = true

        do {
            // Load parking lots
            parkingLots = try await api.getParkingLots()

            // Restore persisted lot selection, or default to first lot
            let savedLotId = UserDefaults.standard.integer(forKey: "selectedParkingLotId")
            if savedLotId != 0, parkingLots.contains(where: { $0.id == savedLotId }) {
                selectedLotId = savedLotId
            } else if let firstLot = parkingLots.first {
                selectedLotId = firstLot.id
            }

            // Check if user is currently parked
            currentSession = try await api.getCurrentSession()

            // Load lot details and prediction
            await loadLotData()

            // Fetch unread notification count
            await fetchUnreadNotificationCount()

        } catch let apiError as APIClientError {
            if case .noToken = apiError {
                isAuthenticated = false
            } else {
                self.error = apiError.localizedDescription
            }
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func loadLotData() async {
        do {
            // Load lot details with stats
            selectedLot = try await api.getParkingLot(id: selectedLotId)

            // Load prediction
            prediction = try await api.getPrediction(lotId: selectedLotId)

            // Animate probability
            animateProbability(to: prediction?.probability ?? 0)

            // Load feed
            feed = try await api.getFeed(lotId: selectedLotId)

        } catch {
            self.error = error.localizedDescription
        }
    }

    func refresh() async {
        await loadLotData()
        await fetchUnreadNotificationCount()
    }

    // MARK: - Notifications

    func requestNotificationPermission() async {
        let granted = await PushNotificationService.shared.requestPermissionAndRegister()
        notificationPermissionGranted = granted
    }

    func fetchUnreadNotificationCount() async {
        do {
            let list = try await api.getUnreadNotifications()
            unreadNotificationCount = list.unreadCount
        } catch {
            // Non-critical — don't surface to UI
            print("Failed to fetch unread notifications: \(error)")
        }
    }

    // MARK: - Parking Actions

    func checkIn() async {
        guard !isParked else {
            self.error = "You're already parked!"
            showError = true
            return
        }

        isLoading = true

        do {
            currentSession = try await api.checkIn(lotId: selectedLotId)
            confirmationMessage = "Checked in at \(currentSession?.parkingLotName ?? "parking lot")!"
            showConfirmation = true
            await loadLotData()
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func checkOut() async {
        guard isParked else {
            self.error = "You're not parked!"
            showError = true
            return
        }

        isLoading = true

        do {
            _ = try await api.checkOut()
            let lotName = currentSession?.parkingLotName ?? "parking lot"
            currentSession = nil
            confirmationMessage = "Checked out from \(lotName)!"
            showConfirmation = true
            await loadLotData()
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    // MARK: - Sighting Actions

    func reportSighting(notes: String? = nil) async {
        isLoading = true

        do {
            let response = try await api.reportSighting(lotId: selectedLotId, notes: notes)
            confirmationMessage = "TAPS reported! \(response.usersNotified ?? 0) users notified."
            showConfirmation = true
            await loadLotData()
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    // MARK: - Voting

    func vote(sightingId: Int, type: VoteType) async {
        do {
            _ = try await api.vote(sightingId: sightingId, voteType: type)
            // Reload feed to show updated votes
            feed = try await api.getFeed(lotId: selectedLotId)
        } catch {
            self.error = error.localizedDescription
            showError = true
        }
    }

    // MARK: - Probability Animation

    private func animateProbability(to target: Double) {
        isAnimatingProbability = true
        let targetPercent = target * 100
        let steps = 30
        let stepDuration = 0.02
        let increment = targetPercent / Double(steps)

        displayedProbability = 0

        for i in 1...steps {
            DispatchQueue.main.asyncAfter(deadline: .now() + stepDuration * Double(i)) {
                self.displayedProbability = min(increment * Double(i), targetPercent)
                if i == steps {
                    self.isAnimatingProbability = false
                }
            }
        }
    }

    // MARK: - Helpers

    var probabilityColor: Color {
        guard let prediction = prediction else { return .gray }
        switch prediction.riskLevel {
        case "HIGH": return .red
        case "MEDIUM": return .yellow
        case "LOW": return .green
        default: return .gray
        }
    }

    var riskLevelText: String {
        guard let prediction = prediction else { return "UNKNOWN" }
        return "\(prediction.riskLevel) RISK"
    }

    var riskMessage: String {
        prediction?.riskMessage ?? "Loading..."
    }

    var riskBars: Int {
        guard let prediction = prediction else { return 2 }
        switch prediction.riskLevel {
        case "HIGH": return 3
        case "MEDIUM": return 2
        case "LOW": return 1
        default: return 2
        }
    }

    func selectLot(_ lotId: Int) {
        selectedLotId = lotId
        Task {
            await loadLotData()
        }
    }
}
