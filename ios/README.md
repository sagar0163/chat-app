# Chat App - iOS

## Build & Run

```bash
# Open in Xcode
open ios/ChatApp.xcworkspace

# Or build from command line
cd ios
xcodebuild -workspace ChatApp.xcworkspace -scheme ChatApp -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 15' build
```

## Configuration

### Base URL

The app uses UserDefaults to store the API base URL. For development:
- iOS Simulator: `http://localhost:8000`
- Physical device: `http://your-computer-ip:8000`

Set it programmatically or via App's UserDefaults.

## Architecture

- **Language**: Swift 5.9
- **UI**: SwiftUI with Material Design 3
- **Architecture**: MVVM
- **Networking**: URLSession WebSocket + async/await
- **Local Storage**: UserDefaults

## Project Structure

```
ios/ChatApp/
├── ChatAppApp.swift      # App entry point
├── APIService.swift      # API client
├── Managers.swift        # WebSocket & Auth managers
├── Models.swift          # Data models
└── Views/
    ├── LoginView.swift   # Login/Register screen
    ├── ChatListView.swift# Chat list screen
    └── ChatView.swift   # Chat detail screen
```

## Features

- User registration & login (JWT)
- Real-time messaging via WebSocket
- Chat list with last message preview
- Group chats
- Online status indicators
- Typing indicators
- Read receipts
