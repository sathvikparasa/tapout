//
//  KeychainService.swift
//  warnabrotha
//
//  Secure storage for authentication tokens using Keychain.
//

import Foundation
import Security

class KeychainService {
    static let shared = KeychainService()

    private let serviceName = "com.warnabrotha.app"
    private let tokenKey = "auth_token"
    private let deviceIdKey = "device_id"
    private let pushTokenKey = "push_token"

    private init() {}

    // MARK: - Auth Token

    func saveToken(_ token: String) -> Bool {
        return save(key: tokenKey, value: token)
    }

    func getToken() -> String? {
        return get(key: tokenKey)
    }

    func deleteToken() -> Bool {
        return delete(key: tokenKey)
    }

    // MARK: - Push Token

    @discardableResult
    func savePushToken(_ token: String) -> Bool {
        return save(key: pushTokenKey, value: token)
    }

    func getPushToken() -> String? {
        return get(key: pushTokenKey)
    }

    // MARK: - Device ID

    func getOrCreateDeviceId() -> String {
        if let existingId = get(key: deviceIdKey) {
            return existingId
        }

        let newId = UUID().uuidString
        _ = save(key: deviceIdKey, value: newId)
        return newId
    }

    // MARK: - Generic Keychain Operations

    private func save(key: String, value: String) -> Bool {
        guard let data = value.data(using: .utf8) else { return false }

        // Delete existing item first
        _ = delete(key: key)

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]

        let status = SecItemAdd(query as CFDictionary, nil)
        return status == errSecSuccess
    }

    private func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let string = String(data: data, encoding: .utf8) else {
            return nil
        }

        return string
    }

    private func delete(key: String) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key
        ]

        let status = SecItemDelete(query as CFDictionary)
        return status == errSecSuccess || status == errSecItemNotFound
    }

    // MARK: - Clear All

    func clearAll() {
        _ = delete(key: tokenKey)
        _ = delete(key: deviceIdKey)
        _ = delete(key: pushTokenKey)
    }
}
