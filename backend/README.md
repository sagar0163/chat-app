# Chat App Backend

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up -d
```

### Environment Variables
```
DATABASE_URL=sqlite:///./chat.db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## WebSocket Endpoints
- `/ws/{token}` - WebSocket connection for real-time messaging

## REST Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get token
- `GET /users` - List users
- `GET /chats` - List user's chats
- `POST /chats` - Create new chat
- `GET /chats/{chat_id}/messages` - Get chat messages
