import Foundation

// MARK: - API Service

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case decodingError
    case networkError(Error)
    case serverError(Int)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .invalidResponse: return "Invalid response"
        case .decodingError: return "Failed to decode response"
        case .networkError(let error): return error.localizedDescription
        case .serverError(let code): return "Server error: \(code)"
        }
    }
}

class APIService: ObservableObject {
    static let shared = APIService()
    
    // Configure base URL - change for production
    // Use http://10.0.2.2:8000 for Android emulator
    // Use http://localhost:8000 for iOS simulator
    private var baseURL: String {
        #if DEBUG
        return UserDefaults.standard.string(forKey: "base_url") ?? "http://10.0.2.2:8000"
        #else
        return "https://your-api-domain.com"
        #endif
    }
    
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()
    
    var authToken: String? {
        get { UserDefaults.standard.string(forKey: "auth_token") }
        set { UserDefaults.standard.set(newValue, forKey: "auth_token") }
    }
    
    private func makeRequest<T: Decodable>(
        endpoint: String,
        method: String = "GET",
        body: Data? = nil
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = body {
            request.httpBody = body
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            guard (200...299).contains(httpResponse.statusCode) else {
                throw APIError.serverError(httpResponse.statusCode)
            }
            
            return try decoder.decode(T.self, from: data)
        } catch let error as DecodingError {
            print("Decoding error: \(error)")
            throw APIError.decodingError
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
    
    // MARK: - Auth
    
    func login(username: String, password: String) async throws -> Token {
        let body = try encoder.encode(LoginRequest(username: username, password: password))
        let token: Token = try await makeRequest(endpoint: "/auth/login", method: "POST", body: body)
        authToken = token.accessToken
        return token
    }
    
    func register(username: String, email: String, password: String, displayName: String?) async throws -> User {
        let body = try encoder.encode(UserCreate(
            username: username,
            email: email,
            password: password,
            displayName: displayName
        ))
        return try await makeRequest(endpoint: "/auth/register", method: "POST", body: body)
    }
    
    func getCurrentUser() async throws -> User {
        return try await makeRequest(endpoint: "/auth/me")
    }
    
    // MARK: - Users
    
    func getUsers() async throws -> [User] {
        return try await makeRequest(endpoint: "/users")
    }
    
    // MARK: - Chats
    
    func getChats() async throws -> [Chat] {
        return try await makeRequest(endpoint: "/chats")
    }
    
    func createChat(name: String?, isGroup: Bool, memberIds: [Int]) async throws -> Chat {
        let body = try encoder.encode(ChatCreate(name: name, isGroup: isGroup, memberIds: memberIds))
        return try await makeRequest(endpoint: "/chats", method: "POST", body: body)
    }
    
    func getMessages(chatId: Int) async throws -> [Message] {
        return try await makeRequest(endpoint: "/chats/\(chatId)/messages")
    }
}
