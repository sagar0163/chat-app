import SwiftUI

// MARK: - Chat View

struct ChatView: View {
    let chatId: Int
    let chatName: String
    
    @StateObject private var viewModel: ChatViewModel
    @State private var messageText = ""
    @FocusState private var isInputFocused: Bool
    
    init(chatId: Int, chatName: String) {
        self.chatId = chatId
        self.chatName = chatName
        self._viewModel = StateObject(wrappedValue: ChatViewModel(chatId: chatId))
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 8) {
                        ForEach(viewModel.messages) { message in
                            MessageBubble(message: message, isOwn: message.senderId == 1)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
            }
            
            // Input
            HStack(spacing: 12) {
                TextField("Type a message...", text: $messageText)
                    .textFieldStyle(.roundedBorder)
                    .focused($isInputFocused)
                    .onSubmit {
                        sendMessage()
                    }
                
                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title)
                }
                .disabled(messageText.isEmpty)
            }
            .padding()
        }
        .navigationTitle(chatName)
        .task {
            viewModel.loadMessages()
            WebSocketManager.shared.sendRead(chatId: chatId)
        }
        .onReceive(WebSocketManager.shared.$messages) { messages in
            let chatMessages = messages.filter { $0.chatId == chatId }
            if !chatMessages.isEmpty {
                viewModel.messages = chatMessages + viewModel.messages
            }
        }
    }
    
    private func sendMessage() {
        guard !messageText.isEmpty else { return }
        
        viewModel.sendMessage(content: messageText)
        messageText = ""
    }
}

// MARK: - Message Bubble

struct MessageBubble: View {
    let message: Message
    let isOwn: Bool
    
    var body: some View {
        HStack {
            if isOwn { Spacer() }
            
            VStack(alignment: isOwn ? .trailing : .leading, spacing: 2) {
                if !isOwn, let sender = message.sender {
                    Text(sender.displayName ?? sender.username)
                        .font(.caption)
                        .foregroundColor(.accentColor)
                }
                
                Text(message.content)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(isOwn ? Color.accentColor : Color.secondary.opacity(0.2))
                    .foregroundColor(isOwn ? .white : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                
                Text(formatTime(message.createdAt))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            if !isOwn { Spacer() }
        }
    }
    
    private func formatTime(_ timestamp: String) -> String {
        if let index = timestamp.firstIndex(of: "T") {
            let timePart = timestamp[timestamp.index(after: index)...]
            if timePart.count >= 5 {
                return String(timePart.prefix(5))
            }
        }
        return ""
    }
}

// MARK: - View Model

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isLoading = false
    
    let chatId: Int
    private let api = APIService.shared
    
    init(chatId: Int) {
        self.chatId = chatId
    }
    
    func loadMessages() {
        Task {
            isLoading = true
            do {
                messages = try await api.getMessages(chatId: chatId)
            } catch {
                print("Failed to load messages: \(error)")
            }
            isLoading = false
        }
    }
    
    func sendMessage(content: String) {
        WebSocketManager.shared.sendMessage(chatId: chatId, content: content)
    }
}
