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
