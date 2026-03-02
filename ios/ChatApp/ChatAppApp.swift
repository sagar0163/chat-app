import SwiftUI

@main
struct ChatAppApp: App {
    @StateObject private var authManager = AuthManager()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    
    var body: some View {
        NavigationStack {
            if authManager.isLoggedIn {
                ChatListView()
            } else {
                LoginView()
            }
        }
    }
}
