import Foundation

// MARK: - Models

struct User: Codable, Identifiable {
    let id: Int
    let username: String
    let email: String
    let displayName: String?
    let avatarUrl: String?
    let isOnline: Bool
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, username, email
        case displayName = "display_name"
        case avatarUrl = "avatar_url"
        case isOnline = "is_online"
        case createdAt = "created_at"
    }
}

struct UserCreate: Codable {
    let username: String
    let email: String
    let password: String
    let displayName: String?
    
    enum CodingKeys: String, CodingKey {
        case username, email, password
        case displayName = "display_name"
    }
}

struct LoginRequest: Codable {
    let username: String
    let password: String
}

struct Token: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

struct Chat: Codable, Identifiable {
    let id: Int
    let name: String?
    let isGroup: Bool
    let members: [User]
    let lastMessage: Message?
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, name
        case isGroup = "is_group"
        case members
        case lastMessage = "last_message"
        case createdAt = "created_at"
    }
}

struct ChatCreate: Codable {
    let name: String?
    let isGroup: Bool
    let memberIds: [Int]
    
    enum CodingKeys: String, CodingKey {
        case name
        case isGroup = "is_group"
        case memberIds = "member_ids"
    }
}

struct Message: Codable, Identifiable {
    let id: Int
    let chatId: Int
    let senderId: Int
    let sender: User?
    let content: String
    let messageType: String
    let isRead: Bool
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case chatId = "chat_id"
        case senderId = "sender_id"
        case sender, content
        case messageType = "message_type"
        case isRead = "is_read"
        case createdAt = "created_at"
    }
}

struct WebSocketMessage: Codable {
    let type: String
    let id: Int?
    let chatId: Int?
    let senderId: Int?
    let senderName: String?
    let content: String?
    let messageType: String?
    let createdAt: String?
    let userId: Int?
    let userName: String?
    
    enum CodingKeys: String, CodingKey {
        case type, id
        case chatId = "chat_id"
        case senderId = "sender_id"
        case senderName = "sender_name"
        case content
        case messageType = "message_type"
        case createdAt = "created_at"
        case userId = "user_id"
        case userName = "user_name"
    }
}
