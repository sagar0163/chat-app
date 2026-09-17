# Chat App Backend

A FastAPI-based backend for real-time chat application with WebSocket support.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up -d
```

### Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./chat.db` | Database connection string |
| `JWT_SECRET` | (required) | Secret key for JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | Token expiry time (30 days) |
| `ALLOWED_ORIGINS` | `http://localhost:8080` | CORS allowed origins (comma-separated) |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection for caching |
| `FCM_PROJECT_ID` | | Firebase project ID for FCM (HTTP v1) |
| `FCM_SERVICE_ACCOUNT_FILE` | | Path to Firebase service account JSON |
| `FCM_SERVICE_ACCOUNT_JSON` | | Firebase service account JSON (inline) |
| `APNS_TEAM_ID` | | Apple Developer team ID for APNs |
| `APNS_KEY_ID` | | APNs auth key ID |
| `APNS_BUNDLE_ID` | | App bundle identifier (push topic) |
| `APNS_AUTH_KEY_FILE` | | Path to APNs `.p8` auth key |

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/{token}` | WebSocket connection for real-time messaging |

### WebSocket Message Types

**Send message:**
```json
{
  "type": "message",
  "chat_id": 1,
  "content": "Hello!",
  "message_type": "text"
}
```

**Typing indicator:**
```json
{
  "type": "typing",
  "chat_id": 1
}
```

**Mark as read:**
```json
{
  "type": "read",
  "chat_id": 1
}
```

## REST Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user
- `PUT /users/me` - Update profile

### Users
- `GET /users` - List all users (excluding current user)
- `POST /users/device-token` - Register a device push token (`token`, `platform`: `fcm`/`apns`)
- `DELETE /users/device-token` - Unregister a device push token (`token` query param)
- `GET /users/device-tokens` - List the current user's registered device tokens

### Push Notifications

When a message is received, offline chat members are sent a push notification
via FCM (Firebase Cloud Messaging) or APNs (Apple Push Notification Service),
depending on the device token's platform.

- Requires client apps to register a device token via `POST /users/device-token`.
- FCM uses the HTTP v1 API with a service account for OAuth2 (see env vars above).
- APNs uses signed JWT provider tokens (`.p8` key).
- If no push credentials are configured the backend logs a warning instead of crashing,
  so push is opt-in.

### Chats
- `GET /chats` - List user's chats
- `POST /chats` - Create new chat
- `GET /chats/{chat_id}` - Get chat details
- `POST /chats/{chat_id}/leave` - Leave chat
- `GET /chats/{chat_id}/messages` - Get messages (supports pagination)
- `GET /chats/{chat_id}/search` - Search messages

### Messages
- `DELETE /messages/{message_id}` - Delete message (own messages only)

### Health
- `GET /health` - Health check endpoint

## Rate Limiting

The API implements rate limiting:
- Registration: 5 requests/minute
- Login: 10 requests/minute
- Messages: 30 requests/minute

## Database

The application uses SQLAlchemy with async support. On first run, tables are created automatically.

## Caching

Redis is used for caching chat lists. Set `REDIS_URL` environment variable to enable.
