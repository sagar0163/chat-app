import SwiftUI

// MARK: - Login View

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showRegister = false
    
    var body: some View {
        VStack(spacing: 24) {
            Text("Chat App")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            VStack(spacing: 16) {
                TextField("Username", text: $username)
                    .textFieldStyle(.roundedBorder)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                
                SecureField("Password", text: $password)
                    .textFieldStyle(.roundedBorder)
            }
            .padding(.horizontal)
            
            Button {
                Task {
                    isLoading = true
                    errorMessage = nil
                    do {
                        try await authManager.login(username: username, password: password)
                    } catch {
                        errorMessage = error.localizedDescription
                    }
                    isLoading = false
                }
            } label: {
                if isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else {
                    Text("Login")
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(username.isEmpty || password.isEmpty)
            .padding(.horizontal)
            
            if let error = errorMessage {
                Text(error)
                    .foregroundColor(.red)
                    .font(.caption)
            }
            
            Button {
                showRegister = true
            } label: {
                Text("Don't have an account? Register")
            }
        }
        .padding()
        .navigationDestination(isPresented: $showRegister) {
            RegisterView()
        }
    }
}

// MARK: - Register View

struct RegisterView: View {
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) var dismiss
    
    @State private var username = ""
    @State private var email = ""
    @State private var password = ""
    @State private var displayName = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        VStack(spacing: 24) {
            Text("Create Account")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            VStack(spacing: 16) {
                TextField("Username", text: $username)
                    .textFieldStyle(.roundedBorder)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                
                TextField("Email", text: $email)
                    .textFieldStyle(.roundedBorder)
                    .keyboardType(.emailAddress)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                
                TextField("Display Name (optional)", text: $displayName)
                    .textFieldStyle(.roundedBorder)
                
                SecureField("Password", text: $password)
                    .textFieldStyle(.roundedBorder)
            }
            .padding(.horizontal)
            
            Button {
                Task {
                    isLoading = true
                    errorMessage = nil
                    do {
                        try await authManager.register(
                            username: username,
                            email: email,
                            password: password,
                            displayName: displayName.isEmpty ? nil : displayName
                        )
                        dismiss()
                    } catch {
                        errorMessage = error.localizedDescription
                    }
                    isLoading = false
                }
            } label: {
                if isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                } else {
                    Text("Register")
                        .frame(maxWidth: .infinity)
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(username.isEmpty || email.isEmpty || password.isEmpty)
            .padding(.horizontal)
            
            if let error = errorMessage {
                Text(error)
                    .foregroundColor(.red)
                    .font(.caption)
            }
        }
        .padding()
    }
}

#Preview {
    NavigationStack {
        LoginView()
            .environmentObject(AuthManager())
    }
}
