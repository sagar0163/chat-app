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

### Build Variants

The app has two build variants:
- **debug**: Points to `http://10.0.2.2:8000/` (localhost for emulator)
- **release**: Points to production API URL

## Configuration

### Base URL

Edit `app/build.gradle` to change the API URL:

```groovy
buildTypes {
    debug {
        buildConfigField "String", "BASE_URL", "\"http://your-server:8000/\""
    }
    release {
        buildConfigField "String", "BASE_URL", "\"https://your-api.com/\""
    }
}
```

## Architecture

- **Language**: Kotlin 1.9.x
- **UI**: Jetpack Compose with Material Design 3
- **Architecture**: MVVM + Clean Architecture
- **DI**: Hilt
- **Networking**: Retrofit + OkHttp + WebSocket
- **Local Storage**: DataStore

## Project Structure

```
app/src/main/java/com/chatapp/android/
├── data/
│   ├── api/          # API service definitions
│   ├── model/        # Data models
│   └── repository/   # Repository implementations
├── di/               # Hilt dependency injection
└── ui/
    ├── navigation/   # Navigation setup
    ├── screens/      # UI screens
    └── theme/        # Material theme
```

## Features

- User registration & login (JWT)
- Real-time messaging via WebSocket
- Chat list with last message preview
- Group chats
- Online status indicators
- Typing indicators
- Read receipts
