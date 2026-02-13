//
//  APIModels.swift
//  warnabrotha
//
//  Data models matching the backend API responses.
//

import Foundation

// MARK: - Authentication

struct DeviceRegistration: Codable {
    let deviceId: String
    let pushToken: String?

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case pushToken = "push_token"
    }
}

struct TokenResponse: Codable {
    let accessToken: String
    let tokenType: String
    let expiresIn: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
        case expiresIn = "expires_in"
    }
}

struct EmailVerificationRequest: Codable {
    let email: String
    let deviceId: String

    enum CodingKeys: String, CodingKey {
        case email
        case deviceId = "device_id"
    }
}

struct EmailVerificationResponse: Codable {
    let success: Bool
    let message: String
    let emailVerified: Bool

    enum CodingKeys: String, CodingKey {
        case success
        case message
        case emailVerified = "email_verified"
    }
}

struct DeviceUpdate: Codable {
    let pushToken: String?
    let isPushEnabled: Bool?

    enum CodingKeys: String, CodingKey {
        case pushToken = "push_token"
        case isPushEnabled = "is_push_enabled"
    }
}

struct DeviceResponse: Codable {
    let id: Int
    let deviceId: String
    let emailVerified: Bool
    let isPushEnabled: Bool
    let createdAt: String
    let lastSeenAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case deviceId = "device_id"
        case emailVerified = "email_verified"
        case isPushEnabled = "is_push_enabled"
        case createdAt = "created_at"
        case lastSeenAt = "last_seen_at"
    }
}

// MARK: - Parking Lots

struct ParkingLot: Codable, Identifiable {
    let id: Int
    let name: String
    let code: String
    let latitude: Double?
    let longitude: Double?
    let isActive: Bool

    enum CodingKeys: String, CodingKey {
        case id, name, code, latitude, longitude
        case isActive = "is_active"
    }
}

struct ParkingLotWithStats: Codable, Identifiable {
    let id: Int
    let name: String
    let code: String
    let latitude: Double?
    let longitude: Double?
    let isActive: Bool
    let activeParkers: Int
    let recentSightings: Int
    let tapsProbability: Double

    enum CodingKeys: String, CodingKey {
        case id, name, code, latitude, longitude
        case isActive = "is_active"
        case activeParkers = "active_parkers"
        case recentSightings = "recent_sightings"
        case tapsProbability = "taps_probability"
    }
}

// MARK: - Parking Sessions

struct ParkingSessionCreate: Codable {
    let parkingLotId: Int

    enum CodingKeys: String, CodingKey {
        case parkingLotId = "parking_lot_id"
    }
}

struct ParkingSession: Codable, Identifiable {
    let id: Int
    let parkingLotId: Int
    let parkingLotName: String
    let parkingLotCode: String
    let checkedInAt: String
    let checkedOutAt: String?
    let isActive: Bool
    let reminderSent: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case parkingLotId = "parking_lot_id"
        case parkingLotName = "parking_lot_name"
        case parkingLotCode = "parking_lot_code"
        case checkedInAt = "checked_in_at"
        case checkedOutAt = "checked_out_at"
        case isActive = "is_active"
        case reminderSent = "reminder_sent"
    }
}

struct CheckoutResponse: Codable {
    let success: Bool
    let message: String
    let sessionId: Int
    let checkedOutAt: String

    enum CodingKeys: String, CodingKey {
        case success, message
        case sessionId = "session_id"
        case checkedOutAt = "checked_out_at"
    }
}

// MARK: - TAPS Sightings

struct SightingCreate: Codable {
    let parkingLotId: Int
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case parkingLotId = "parking_lot_id"
        case notes
    }
}

struct SightingResponse: Codable, Identifiable {
    let id: Int
    let parkingLotId: Int
    let parkingLotName: String
    let parkingLotCode: String
    let reportedAt: String
    let notes: String?
    let usersNotified: Int?

    enum CodingKeys: String, CodingKey {
        case id
        case parkingLotId = "parking_lot_id"
        case parkingLotName = "parking_lot_name"
        case parkingLotCode = "parking_lot_code"
        case reportedAt = "reported_at"
        case notes
        case usersNotified = "users_notified"
    }
}

// MARK: - Feed & Voting

enum VoteType: String, Codable {
    case upvote
    case downvote
}

struct VoteCreate: Codable {
    let voteType: VoteType

    enum CodingKeys: String, CodingKey {
        case voteType = "vote_type"
    }
}

struct VoteResult: Codable {
    let success: Bool
    let action: String
    let voteType: VoteType?

    enum CodingKeys: String, CodingKey {
        case success, action
        case voteType = "vote_type"
    }
}

struct FeedSighting: Codable, Identifiable {
    let id: Int
    let parkingLotId: Int
    let parkingLotName: String
    let parkingLotCode: String
    let reportedAt: String
    let notes: String?
    let upvotes: Int
    let downvotes: Int
    let netScore: Int
    let userVote: VoteType?
    let minutesAgo: Int

    enum CodingKeys: String, CodingKey {
        case id
        case parkingLotId = "parking_lot_id"
        case parkingLotName = "parking_lot_name"
        case parkingLotCode = "parking_lot_code"
        case reportedAt = "reported_at"
        case notes, upvotes, downvotes
        case netScore = "net_score"
        case userVote = "user_vote"
        case minutesAgo = "minutes_ago"
    }
}

struct FeedResponse: Codable, Identifiable {
    var id: Int { parkingLotId }
    let parkingLotId: Int
    let parkingLotName: String
    let parkingLotCode: String
    let sightings: [FeedSighting]
    let totalSightings: Int

    enum CodingKeys: String, CodingKey {
        case parkingLotId = "parking_lot_id"
        case parkingLotName = "parking_lot_name"
        case parkingLotCode = "parking_lot_code"
        case sightings
        case totalSightings = "total_sightings"
    }
}

struct AllFeedsResponse: Codable {
    let feeds: [FeedResponse]
    let totalSightings: Int

    enum CodingKeys: String, CodingKey {
        case feeds
        case totalSightings = "total_sightings"
    }
}

// MARK: - Predictions

struct PredictionFactors: Codable {
    let timeOfDayFactor: Double
    let dayOfWeekFactor: Double
    let historicalFactor: Double
    let recentSightingsFactor: Double
    let academicCalendarFactor: Double
    let weatherFactor: Double?

    enum CodingKeys: String, CodingKey {
        case timeOfDayFactor = "time_of_day_factor"
        case dayOfWeekFactor = "day_of_week_factor"
        case historicalFactor = "historical_factor"
        case recentSightingsFactor = "recent_sightings_factor"
        case academicCalendarFactor = "academic_calendar_factor"
        case weatherFactor = "weather_factor"
    }
}

struct PredictionResponse: Codable {
    // New fields
    let riskLevel: String
    let riskMessage: String
    let lastSightingLotName: String?
    let lastSightingLotCode: String?
    let lastSightingAt: String?
    let hoursSinceLastSighting: Double?

    // Backward-compatible fields
    let parkingLotId: Int?
    let parkingLotName: String?
    let parkingLotCode: String?
    let probability: Double
    let predictedFor: String
    let factors: PredictionFactors?
    let confidence: Double?

    enum CodingKeys: String, CodingKey {
        case riskLevel = "risk_level"
        case riskMessage = "risk_message"
        case lastSightingLotName = "last_sighting_lot_name"
        case lastSightingLotCode = "last_sighting_lot_code"
        case lastSightingAt = "last_sighting_at"
        case hoursSinceLastSighting = "hours_since_last_sighting"
        case parkingLotId = "parking_lot_id"
        case parkingLotName = "parking_lot_name"
        case parkingLotCode = "parking_lot_code"
        case probability
        case predictedFor = "predicted_for"
        case factors, confidence
    }
}

// MARK: - Notifications

struct NotificationItem: Codable, Identifiable {
    let id: Int
    let notificationType: String
    let title: String
    let message: String
    let parkingLotId: Int?
    let createdAt: String
    let readAt: String?
    let isRead: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case notificationType = "notification_type"
        case title, message
        case parkingLotId = "parking_lot_id"
        case createdAt = "created_at"
        case readAt = "read_at"
        case isRead = "is_read"
    }
}

struct NotificationList: Codable {
    let notifications: [NotificationItem]
    let unreadCount: Int
    let total: Int

    enum CodingKeys: String, CodingKey {
        case notifications
        case unreadCount = "unread_count"
        case total
    }
}

// MARK: - Error Response

struct APIError: Codable {
    let detail: String
}
