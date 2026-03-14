//
//  AppViewModel.swift
//  warnabrotha
//
//  Main view model managing app state and API interactions.
//

import Foundation
import SwiftUI
import UserNotifications

enum OTPStep {
    case emailInput
    case codeInput
}


@MainActor
class AppViewModel: ObservableObject {
    // MARK: - Published State

    // Auth state
    @Published var isAuthenticated = false
    @Published var isEmailVerified = false
    @Published var showEmailVerification = false

    // OTP state
    @Published var otpStep: OTPStep = .emailInput
    @Published var otpEmail: String = ""
    @Published var canResendOTP = false
    @Published var resendCooldown: Int = 0

    // Parking state
    @Published var parkingLots: [ParkingLot] = []
    @Published var selectedLot: ParkingLotWithStats?
    @Published var currentSession: ParkingSession?
    var isParked: Bool { currentSession != nil }

    // Feed state
    @Published var feed: FeedResponse?
    @Published var allFeeds: AllFeedsResponse?
    @Published var allFeedSightings: [FeedSighting] = []
    @Published var allFeedsLoaded = false

    // Chat state
    @Published var chatMessages: [ChatMessage] = []
    @Published var chatInputText: String = ""
    @Published var chatIsLoading = false
    @Published var chatIsSending = false
    @Published var chatError: String? = nil
    @Published var chatShowError = false

    // Map state
    @Published var lotStats: [Int: ParkingLotWithStats] = [:]
    @Published var globalStats: GlobalStatsResponse? = nil

    // Prediction state
    @Published var prediction: PredictionResponse?
    @Published var displayedProbability: Double = 0
    @Published var isAnimatingProbability = false

    // Notification state
    @Published var notificationPermissionGranted = false
    @Published var unreadNotificationCount = 0
    @Published var showTimeSensitivePrompt = false

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
    private var ownMessageIds: Set<Int> = []

    private var resendTimer: Timer?

    var hasCompletedOnboarding: Bool {
        get { UserDefaults.standard.bool(forKey: "hasCompletedOnboarding") }
        set { UserDefaults.standard.set(newValue, forKey: "hasCompletedOnboarding") }
    }

    // MARK: - Initialization

    init() {
        // Keychain persists across app deletions — clear it on a fresh install
        // UserDefaults is wiped on deletion, so this reliably detects reinstalls
        if !UserDefaults.standard.bool(forKey: "hasLaunchedBefore") {
            keychain.clearAll()
            UserDefaults.standard.set(true, forKey: "hasLaunchedBefore")
        }

        if keychain.getToken() != nil && hasCompletedOnboarding {
            isAuthenticated = true
            isEmailVerified = true
            Task {
                await silentRefresh()
            }
        } else if keychain.getToken() != nil {
            isAuthenticated = true
            Task {
                await silentRefresh()
            }
        }

    }

    private func silentRefresh() async {
        do {
            let response = try await api.register()
            if response.emailVerified {
                isEmailVerified = true
                hasCompletedOnboarding = true
                showEmailVerification = false
                await loadInitialData()
                await requestNotificationPermission()
            } else {
                isEmailVerified = false
                showEmailVerification = true
            }
        } catch {
            // Network error — use existing token optimistically
            if hasCompletedOnboarding {
                isEmailVerified = true
                showEmailVerification = false
                await loadInitialData()
            } else {
                // Token exists but email never verified — send back to verification
                showEmailVerification = true
            }
        }
    }

    // MARK: - Authentication

    func register() async {
        isLoading = true
        error = nil

        do {
            let response = try await api.register()
            isAuthenticated = true

            if response.emailVerified {
                isEmailVerified = true
                hasCompletedOnboarding = true
                showEmailVerification = false
                await loadInitialData()
                await requestNotificationPermission()
            } else {
                showEmailVerification = true
            }
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func sendOTP(_ email: String) async {
        isLoading = true
        error = nil
        otpEmail = email

        do {
            let response = try await api.sendOTP(email)
            if response.success {
                otpStep = .codeInput
                startResendCooldown()
            } else {
                self.error = response.message
                showError = true
            }
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func verifyOTP(_ code: String) async {
        isLoading = true
        error = nil

        do {
            let response = try await api.verifyOTP(email: otpEmail, code: code)
            if response.success && response.emailVerified {
                isEmailVerified = true
                hasCompletedOnboarding = true
                showEmailVerification = false
                otpStep = .emailInput
                await loadInitialData()
                await requestNotificationPermission()
            } else {
                self.error = response.message
                showError = true
            }
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func resendOTP() async {
        await sendOTP(otpEmail)
    }

    func changeEmail() {
        otpStep = .emailInput
        error = nil
    }

    private func startResendCooldown() {
        canResendOTP = false
        resendCooldown = 60
        resendTimer?.invalidate()
        resendTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] timer in
            Task { @MainActor in
                guard let self = self else { timer.invalidate(); return }
                self.resendCooldown -= 1
                if self.resendCooldown <= 0 {
                    self.canResendOTP = true
                    timer.invalidate()
                }
            }
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

            // Load all feeds and global stats
            await loadAllFeeds()
            await loadGlobalStats()
            await refreshAllLotStats()

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
        if granted {
            let settings = await UNUserNotificationCenter.current().notificationSettings()
            if settings.timeSensitiveSetting == .disabled {
                showTimeSensitivePrompt = true
            }
        }
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

    func markAllNotificationsRead() async {
        guard unreadNotificationCount > 0 else { return }
        do {
            try await api.markAllNotificationsRead()
            unreadNotificationCount = 0
            // Clear the iOS app badge
            try await UNUserNotificationCenter.current().setBadgeCount(0)
        } catch {
            print("Failed to mark all notifications read: \(error)")
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
            let parkersAtLot = selectedLot?.activeParkers ?? 0
            _ = try await api.reportSighting(lotId: selectedLotId, notes: notes)
            confirmationMessage = "TAPS reported! \(parkersAtLot) users notified."
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
        // Save originals for revert on error
        let originalSightings = allFeedSightings
        let currentVote = allFeedSightings.first(where: { $0.id == sightingId })?.userVote

        // Optimistic update — apply immediately before API call
        allFeedSightings = allFeedSightings.map { sighting in
            guard sighting.id == sightingId else { return sighting }
            let newVote: VoteType? = sighting.userVote == type ? nil : type
            var upvotes = sighting.upvotes
            var downvotes = sighting.downvotes
            if sighting.userVote == .upvote { upvotes -= 1 }
            if sighting.userVote == .downvote { downvotes -= 1 }
            if newVote == .upvote { upvotes += 1 }
            if newVote == .downvote { downvotes += 1 }
            return FeedSighting(
                id: sighting.id,
                parkingLotId: sighting.parkingLotId,
                parkingLotName: sighting.parkingLotName,
                parkingLotCode: sighting.parkingLotCode,
                reportedAt: sighting.reportedAt,
                notes: sighting.notes,
                upvotes: upvotes,
                downvotes: downvotes,
                netScore: upvotes - downvotes,
                userVote: newVote,
                minutesAgo: sighting.minutesAgo
            )
        }

        do {
            if currentVote == type {
                try await api.removeVote(sightingId: sightingId)
            } else {
                _ = try await api.vote(sightingId: sightingId, voteType: type)
            }
        } catch {
            // Revert on failure
            allFeedSightings = originalSightings
            self.error = error.localizedDescription
            showError = true
        }
    }

    // MARK: - Map Actions

    func checkInAtLot(_ lotId: Int) async {
        guard !isParked else {
            self.error = "You're already parked!"
            showError = true
            return
        }

        isLoading = true

        do {
            currentSession = try await api.checkIn(lotId: lotId)
            confirmationMessage = "Checked in at \(currentSession?.parkingLotName ?? "parking lot")!"
            showConfirmation = true
            await loadLotData()
            await refreshAllLotStats()
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func reportSightingAtLot(_ lotId: Int, notes: String? = nil) async {
        isLoading = true

        do {
            let parkersAtLot = lotStats[lotId]?.activeParkers ?? selectedLot?.activeParkers ?? 0
            _ = try await api.reportSighting(lotId: lotId, notes: notes)
            confirmationMessage = "TAPS reported! \(parkersAtLot) users notified."
            showConfirmation = true
            await loadLotData()
            await loadAllFeeds()
            await refreshAllLotStats()
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    // MARK: - All Feeds

    func loadAllFeeds() async {
        do {
            let response = try await api.getAllFeeds()
            allFeeds = response
            allFeedSightings = response.feeds
                .flatMap { $0.sightings }
                .sorted { $0.minutesAgo < $1.minutesAgo }
            allFeedsLoaded = true
        } catch {
            // Non-critical
            print("Failed to load all feeds: \(error)")
        }
    }

    // MARK: - Global Stats

    func loadGlobalStats() async {
        do {
            globalStats = try await api.getGlobalStats()
        } catch {
            // Non-critical
            print("Failed to load global stats: \(error)")
        }
    }

    // MARK: - Lot Stats

    func refreshAllLotStats() async {
        var statsMap: [Int: ParkingLotWithStats] = [:]
        for lot in parkingLots {
            do {
                let lotWithStats = try await api.getParkingLot(id: lot.id)
                statsMap[lot.id] = lotWithStats
            } catch {
                // Skip this lot
            }
        }
        lotStats = statsMap
    }

    // MARK: - Probability Animation

    private func animateProbability(to target: Double) {
        isAnimatingProbability = true
        let targetPercent = target * 100
        let steps = 30
        let stepDuration = 0.02
        let increment = targetPercent / Double(steps)

        displayedProbability = 0

        Task { @MainActor in
            for i in 1...steps {
                try? await Task.sleep(nanoseconds: UInt64(stepDuration * 1_000_000_000))
                self.displayedProbability = min(increment * Double(i), targetPercent)
            }
            self.isAnimatingProbability = false
        }
    }

    // MARK: - Global Chat

    func loadChatMessages() async {
        chatIsLoading = true
        do {
            let response = try await api.getChatMessages()
            chatMessages = response.messages
        } catch {
            print("Failed to load chat messages: \(error)")
        }
        chatIsLoading = false
    }

    func sendChatMessage() async {
        let content = chatInputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty else { return }

        chatIsSending = true
        let savedInput = chatInputText
        chatInputText = ""

        // Optimistic: show the message immediately while the POST is in flight
        let tempId = -(chatMessages.count + 1)
        let pending = ChatMessage(
            id: tempId,
            content: content,
            sentAt: ISO8601DateFormatter().string(from: Date()),
            minutesAgo: 0,
            isPending: true,
            isOwn: true
        )
        chatMessages.append(pending)

        do {
            let message = try await api.sendChatMessage(content: content)
            ownMessageIds.insert(message.id)
            chatMessages.removeAll { $0.id == tempId }
            if !chatMessages.contains(where: { $0.id == message.id }) {
                var msg = message
                msg.isOwn = true
                chatMessages.append(msg)
            }
        } catch APIClientError.serverError(_, let msg) {
            chatMessages.removeAll { $0.id == tempId }
            chatInputText = savedInput
            chatError = msg
            chatShowError = true
        } catch {
            chatMessages.removeAll { $0.id == tempId }
            chatInputText = savedInput
            chatError = error.localizedDescription
            chatShowError = true
        }

        chatIsSending = false
    }

    // MARK: - Helpers

    var probabilityColor: Color {
        guard let prediction = prediction else { return AppColors.textMuted }
        switch prediction.riskLevel {
        case "HIGH": return AppColors.dangerBright
        case "MEDIUM": return AppColors.warning
        case "LOW": return AppColors.success
        default: return AppColors.textMuted
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
