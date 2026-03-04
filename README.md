# Chat App - Real-time Messaging Application

[![Release](https://img.shields.io/badge/release-1.0.0-blue.svg)](https://github.com/sagar0163/chat-app)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A full-stack real-time messaging application with WebSocket support, featuring a Python FastAPI backend, Android (Kotlin) app, and iOS (Swift) app.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend                             │
├─────────────────────┬───────────────────────────────────┤
│   Android (Kotlin)  │       iOS (Swift)                │
│  Jetpack Compose    │       SwiftUI                    │
└─────────┬───────────┴───────────────┬───────────────────┘
          │                           │
          │      WebSocket            │
          └───────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 Backend (Python)                        │
│  FastAPI + WebSocket + SQLite + Redis                   │
└─────────────────────────────────────────────────────────┘
```

## 📱 Features

- ✅ User Registration & Login (JWT Authentication)
- ✅ Real-time Messaging (WebSocket)
- ✅ Chat List with Last Message Preview
- ✅ Group Chats
- ✅ Online Status Indicators
- ✅ Typing Indicators
- ✅ Read Receipts
- ✅ End-to-end encryption ready

## 🚀 Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up -d
```

### Android

```bash
cd android

# Build debug APK
./gradlew assembleDebug

# Install on device
./gradlew installDebug
```

### iOS

```bash
cd ios

# Open in Xcode
open ChatApp.xcworkspace

# Or build from command line
xcodebuild -workspace ChatApp.xcworkspace -scheme ChatApp \
    -configuration Debug \
    -destination 'platform=iOS Simulator,name=iPhone 15' build
```

## 📁 Project Structure

```
chat-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── docker-compose.yml   # Docker configuration
│   └── README.md
│
├── android/
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/chatapp/android/
│   │   │   │   ├── data/          # Data layer
│   │   │   │   ├── di/            # Dependency injection
│   │   │   │   └── ui/            # UI layer
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle
│   └── README.md
│
├── ios/
│   ├── ChatApp/
│   │   ├── ChatAppApp.swift
│   │   ├── Models.swift
│   │   ├── APIService.swift
│   │   ├── Managers.swift
│   │   └── Views/
│   │       ├── LoginView.swift
│   │       ├── ChatListView.swift
│   │       └── ChatView.swift
│   └── README.md
│
└── README.md
```

## 🔧 Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./chat.db` | Database connection |
| `JWT_SECRET` | `your-secret-key` | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | Token expiry (30 days) |

### Android Configuration

Edit `app/build.gradle`:
```groovy
buildConfigField "String", "BASE_URL", "\"http://your-server:8000/\""
```

### iOS Configuration

The base URL is configured in `APIService.swift`:
```swift
private let baseURL = "http://your-server:8000"
```

## 🔨 Building for Release

### Version Management

This project uses [release-it](https://github.com/release-it/release-it) for versioning:

```bash
# Install release-it
npm install -g release-it

# Bump version and create release
release-it

# Or with specific version
release-it --release-type minor
release-it --release-type major
```

### Android Release

```bash
cd android
./gradlew assembleRelease
# APK will be at app/build/outputs/apk/release/
```

### iOS Release

1. Open `ios/ChatApp.xcworkspace` in Xcode
2. Select your team for code signing
3. Product → Archive

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get token |
| GET | `/auth/me` | Get current user |
| GET | `/users` | List all users |
| GET | `/chats` | List user's chats |
| POST | `/chats` | Create new chat |
| GET | `/chats/{id}/messages` | Get chat messages |
| WS | `/ws/{token}` | WebSocket connection |

## 🐳 Docker

```bash
# Start backend with Redis
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📄 License

MIT License - see LICENSE file for details

## 👤 Author

Sagar Jadhav
