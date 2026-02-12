//
//  APIClient.swift
//  warnabrotha
//
//  HTTP client for communicating with the WarnABrotha backend API.
//

import Foundation

enum APIClientError: Error, LocalizedError {
    case invalidURL
    case noToken
    case networkError(Error)
    case decodingError(Error)
    case serverError(Int, String)
    case unknown

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .noToken:
            return "Not authenticated"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Failed to parse response: \(error.localizedDescription)"
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message)"
        case .unknown:
            return "An unknown error occurred"
        }
    }
}

class APIClient {
    static let shared = APIClient()

    // Change this to your backend URL
    #if DEBUG
    private let baseURL = "https://tapout-485821.wl.r.appspot.com/api/v1"
    #else
    private let baseURL = "https://api.warnabrotha.com/api/v1"
    #endif

    private let session: URLSession
    private let keychain = KeychainService.shared
    private let decoder: JSONDecoder

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
    }

    // MARK: - Authentication

    func register() async throws -> TokenResponse {
        let deviceId = keychain.getOrCreateDeviceId()
        let body = DeviceRegistration(deviceId: deviceId, pushToken: nil)

        let response: TokenResponse = try await post(
            endpoint: "/auth/register",
            body: body,
            authenticated: false
        )

        // Save token
        _ = keychain.saveToken(response.accessToken)

        return response
    }

    func verifyEmail(_ email: String) async throws -> EmailVerificationResponse {
        let deviceId = keychain.getOrCreateDeviceId()
        let body = EmailVerificationRequest(email: email, deviceId: deviceId)

        return try await post(
            endpoint: "/auth/verify-email",
            body: body,
            authenticated: false
        )
    }

    func getDeviceInfo() async throws -> DeviceResponse {
        return try await get(endpoint: "/auth/me")
    }

    func updateDevice(pushToken: String, isPushEnabled: Bool) async throws -> DeviceResponse {
        let body = DeviceUpdate(pushToken: pushToken, isPushEnabled: isPushEnabled)
        return try await patch(endpoint: "/auth/me", body: body)
    }

    // MARK: - Parking Lots

    func getParkingLots() async throws -> [ParkingLot] {
        return try await get(endpoint: "/lots")
    }

    func getParkingLot(id: Int) async throws -> ParkingLotWithStats {
        return try await get(endpoint: "/lots/\(id)")
    }

    // MARK: - Parking Sessions

    func checkIn(lotId: Int) async throws -> ParkingSession {
        let body = ParkingSessionCreate(parkingLotId: lotId)
        return try await post(endpoint: "/sessions/checkin", body: body)
    }

    func checkOut() async throws -> CheckoutResponse {
        return try await post(endpoint: "/sessions/checkout", body: EmptyBody())
    }

    func getCurrentSession() async throws -> ParkingSession? {
        // This endpoint returns null if no active session
        return try await getOptional(endpoint: "/sessions/current")
    }

    func getSessionHistory(limit: Int = 20) async throws -> [ParkingSession] {
        return try await get(endpoint: "/sessions/history?limit=\(limit)")
    }

    // MARK: - Sightings

    func reportSighting(lotId: Int, notes: String? = nil) async throws -> SightingResponse {
        let body = SightingCreate(parkingLotId: lotId, notes: notes)
        return try await post(endpoint: "/sightings", body: body)
    }

    func getSightings(hours: Int = 24, lotId: Int? = nil) async throws -> [SightingResponse] {
        var endpoint = "/sightings?hours=\(hours)"
        if let lotId = lotId {
            endpoint += "&lot_id=\(lotId)"
        }
        return try await get(endpoint: endpoint)
    }

    // MARK: - Feed & Voting

    func getAllFeeds() async throws -> AllFeedsResponse {
        return try await get(endpoint: "/feed")
    }

    func getFeed(lotId: Int) async throws -> FeedResponse {
        return try await get(endpoint: "/feed/\(lotId)")
    }

    func vote(sightingId: Int, voteType: VoteType) async throws -> VoteResult {
        let body = VoteCreate(voteType: voteType)
        return try await post(endpoint: "/feed/sightings/\(sightingId)/vote", body: body)
    }

    func removeVote(sightingId: Int) async throws {
        try await delete(endpoint: "/feed/sightings/\(sightingId)/vote")
    }

    // MARK: - Predictions

    func getPrediction(lotId: Int) async throws -> PredictionResponse {
        return try await get(endpoint: "/predictions/\(lotId)")
    }

    // MARK: - Notifications

    func getUnreadNotifications() async throws -> NotificationList {
        return try await get(endpoint: "/notifications/unread")
    }

    func markNotificationsRead(ids: [Int]) async throws {
        let body = MarkNotificationsReadRequest(notificationIds: ids)
        let _: EmptyResponse = try await post(endpoint: "/notifications/read", body: body)
    }

    // MARK: - HTTP Methods

    private func get<T: Decodable>(endpoint: String) async throws -> T {
        let request = try buildRequest(endpoint: endpoint, method: "GET")
        return try await execute(request)
    }

    private func getOptional<T: Decodable>(endpoint: String) async throws -> T? {
        let request = try buildRequest(endpoint: endpoint, method: "GET")
        return try await executeOptional(request)
    }

    private func post<T: Decodable, B: Encodable>(
        endpoint: String,
        body: B,
        authenticated: Bool = true
    ) async throws -> T {
        var request = try buildRequest(endpoint: endpoint, method: "POST", authenticated: authenticated)
        request.httpBody = try JSONEncoder().encode(body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await execute(request)
    }

    private func patch<T: Decodable, B: Encodable>(
        endpoint: String,
        body: B
    ) async throws -> T {
        var request = try buildRequest(endpoint: endpoint, method: "PATCH")
        request.httpBody = try JSONEncoder().encode(body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await execute(request)
    }

    private func delete(endpoint: String) async throws {
        let request = try buildRequest(endpoint: endpoint, method: "DELETE")
        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.unknown
        }

        if httpResponse.statusCode >= 400 {
            throw APIClientError.serverError(httpResponse.statusCode, "Delete failed")
        }
    }

    // MARK: - Helpers

    private func buildRequest(
        endpoint: String,
        method: String,
        authenticated: Bool = true
    ) throws -> URLRequest {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIClientError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method

        if authenticated {
            guard let token = keychain.getToken() else {
                throw APIClientError.noToken
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        return request
    }

    private func execute<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.unknown
        }

        if httpResponse.statusCode >= 400 {
            if let errorResponse = try? decoder.decode(APIError.self, from: data) {
                throw APIClientError.serverError(httpResponse.statusCode, errorResponse.detail)
            }
            throw APIClientError.serverError(httpResponse.statusCode, "Unknown error")
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIClientError.decodingError(error)
        }
    }

    private func executeOptional<T: Decodable>(_ request: URLRequest) async throws -> T? {
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIClientError.unknown
        }

        if httpResponse.statusCode >= 400 {
            if let errorResponse = try? decoder.decode(APIError.self, from: data) {
                throw APIClientError.serverError(httpResponse.statusCode, errorResponse.detail)
            }
            throw APIClientError.serverError(httpResponse.statusCode, "Unknown error")
        }

        // Check for null/empty response
        if data.isEmpty || String(data: data, encoding: .utf8) == "null" {
            return nil
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIClientError.decodingError(error)
        }
    }
}

// Helper for empty POST bodies
private struct EmptyBody: Encodable {}

// Helper for empty responses
private struct EmptyResponse: Decodable {}

// Helper struct for marking notifications read
private struct MarkNotificationsReadRequest: Encodable {
    let notificationIds: [Int]

    enum CodingKeys: String, CodingKey {
        case notificationIds = "notification_ids"
    }
}
