import SwiftUI

// MARK: - Chat List View

struct ChatListView: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = ChatListViewModel()
    @State private var showNewChat = false
    
    var body: some View {
        List {
            ForEach(viewModel.chats) { chat in
                NavigationLink(destination: ChatView(chatId: chat.id, chatName: chat.name ?? "Chat")) {
                    ChatRow(chat: chat)
                }
            }
        }
        .navigationTitle("Chats")
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("Logout") {
                    authManager.logout()
                }
            }
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showNewChat = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .refreshable {
            viewModel.loadChats()
        }
        .task {
            viewModel.loadChats()
            WebSocketManager.shared.connect()
        }
        .sheet(isPresented: $showNewChat) {
            NewChatView { name, isGroup in
                viewModel.createChat(name: name, isGroup: isGroup)
            }
        }
    }
}

// MARK: - Chat Row

struct ChatRow: View {
    let chat: Chat
    
    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color.accentColor)
                .frame(width: 48, height: 48)
                .overlay(
                    Text(String(chat.name?.prefix(1) ?? "C").uppercased())
                        .foregroundColor(.white)
                )
            
            VStack(alignment: .leading, spacing: 4) {
                Text(chat.name ?? "Chat")
                    .font(.headline)
                
                if let lastMessage = chat.lastMessage {
                    Text(lastMessage.content)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }
            
            Spacer()
        }
        .padding(.vertical, 4)
    }
}

// MARK: - New Chat View

struct NewChatView: View {
    @Environment(\.dismiss) var dismiss
    @State private var chatName = ""
    @State private var isGroup = false
    
    let onCreate: (String?, Bool) -> Void
    
    var body: some View {
        NavigationStack {
            Form {
                TextField("Chat Name", text: $chatName)
                
                Toggle("Group Chat", isOn: $isGroup)
            }
            .navigationTitle("New Chat")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        onCreate(chatName.isEmpty ? nil : chatName, isGroup)
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - View Model

@MainActor
class ChatListViewModel: ObservableObject {
    @Published var chats: [Chat] = []
    @Published var isLoading = false
    
    private let api = APIService.shared
    
    func loadChats() {
        Task {
            isLoading = true
            do {
                chats = try await api.getChats()
            } catch {
                print("Failed to load chats: \(error)")
            }
            isLoading = false
        }
    }
    
    func createChat(name: String?, isGroup: Bool) {
        Task {
            do {
                _ = try await api.createChat(name: name, isGroup: isGroup, memberIds: [])
                loadChats()
            } catch {
                print("Failed to create chat: \(error)")
            }
        }
    }
}
