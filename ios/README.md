# Chat App - iOS

## Build & Run

```bash
# Open in Xcode
open ios/ChatApp.xcworkspace

# Or build from command line
cd ios
xcodebuild -workspace ChatApp.xcworkspace -scheme ChatApp -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 15' build
```

## Architecture

- **Language**: Swift 5.9
- **UI**: SwiftUI with Material Design 3
- **Architecture**: MVVM
- **Networking**: URLSession WebSocket + async/await
- **Local Storage**: UserDefaults

## Features

- User registration & login (JWT)
- Real-time messaging via WebSocket
- Chat list with last message preview
- Group chats
- Online status indicators
- Typing indicators
- Read receipts
