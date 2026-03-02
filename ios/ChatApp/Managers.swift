import Foundation
import Combine

// MARK: - Auth Manager

class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool = false
    @Published var currentUser: User?
    
    private let api = APIService.shared
    
    init() {
        isLoggedIn = api.authToken != nil
    }
    
    func login(username: String, password: String) async throws {
        _ = try await api.login(username: username, password: password)
        await MainActor.run {
            isLoggedIn = true
        }
    }
    
    func register(username: String, email: String, password: String, displayName: String?) async throws {
        _ = try await api.register(username: username, email: email, password: password, displayName: displayName)
    }
    
    func logout() {
        api.authToken = nil
        WebSocketManager.shared.disconnect()
        isLoggedIn = false
    }
}

// MARK: - WebSocket Manager

class WebSocketManager: ObservableObject {
    static let shared = WebSocketManager()
    
    @Published var isConnected = false
    @Published var messages: [Message] = []
    @Published var typingUsers: [Int: String] = [:]
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var authToken: String? {
        APIService.shared.authToken
    }
    
    func connect() {
        guard let token = authToken else { return }
        
        let urlString = "ws://10.0.2.2:8000/ws/\(token)"
        guard let url = URL(string: urlString) else { return }
        
        let configuration = URLSessionConfiguration.default
        let session = URLSession(configuration: configuration)
        
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        
        isConnected = true
        receiveMessage()
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self?.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                self?.receiveMessage()
                
            case .failure(let error):
                print("WebSocket error: \(error)")
                self?.isConnected = false
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }
        
        do {
            let wsMessage = try JSONDecoder().decode(WebSocketMessage.self, from: data)
            
            DispatchQueue.main.async { [weak self] in
                switch wsMessage.type {
                case "message":
                    if let chatId = wsMessage.chatId,
                       let content = wsMessage.content,
                       let createdAt = wsMessage.createdAt {
                        let message = Message(
                            id: wsMessage.id ?? 0,
                            chatId: chatId,
                            senderId: wsMessage.senderId ?? 0,
                            sender: nil,
                            content: content,
                            messageType: wsMessage.messageType ?? "text",
                            isRead: false,
                            createdAt: createdAt
                        )
                        self?.messages.insert(message, at: 0)
                    }
                case "typing":
                    if let userId = wsMessage.userId, let userName = wsMessage.userName {
                        self?.typingUsers[userId] = userName
                    }
                default:
                    break
                }
            }
        } catch {
            print("Failed to decode WebSocket message: \(error)")
        }
    }
    
    func sendMessage(chatId: Int, content: String) {
        let message: [String: Any] = [
            "type": "message",
            "chat_id": chatId,
            "content": content,
            "message_type": "text"
        ]
        
        if let data = try? JSONSerialization.data(withJSONObject: message),
           let string = String(data: data, encoding: .utf8) {
            webSocketTask?.send(.string(string)) { error in
                if let error = error {
                    print("Send error: \(error)")
                }
            }
        }
    }
    
    func sendTyping(chatId: Int) {
        let message: [String: Any] = [
            "type": "typing",
            "chat_id": chatId
        ]
        
        if let data = try? JSONSerialization.data(withJSONObject: message),
           let string = String(data: data, encoding: .utf8) {
            webSocketTask?.send(.string(string))
        }
    }
    
    func sendRead(chatId: Int) {
        let message: [String: Any] = [
            "type": "read",
            "chat_id": chatId
        ]
        
        if let data = try? JSONSerialization.data(withJSONObject: message),
           let string = String(data: data, encoding: .utf8) {
            webSocketTask?.send(.string(string))
        }
    }
}
