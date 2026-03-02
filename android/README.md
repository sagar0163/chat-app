# Chat App - Android

## Build & Run

```bash
# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Run on connected device
./gradlew installDebug
```

## Architecture

- **Language**: Kotlin 1.9.x
- **UI**: Jetpack Compose with Material Design 3
- **Architecture**: MVVM + Clean Architecture
- **DI**: Hilt
- **Networking**: Retrofit + OkHttp + WebSocket
- **Local Storage**: DataStore + Room

## Features

- User registration & login (JWT)
- Real-time messaging via WebSocket
- Chat list with last message preview
- Group chats
- Online status indicators
- Typing indicators
- Read receipts
