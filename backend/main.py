"""
Chat App Backend - FastAPI with WebSocket Support
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
import json
import asyncio
import os
from enum import Enum

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# ============== Rate Limiter ==============
limiter = Limiter(key_func=get_remote_address)

# ============== CONFIG ==============
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chat.db")
JWT_SECRET = os.getenv("JWT_SECRET", "chat-app-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")

# ============== DATABASE ==============
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_online = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=func.now())

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class ChatMember(Base):
    __tablename__ = "chat_members"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String, default="member")  # admin, member
    joined_at = Column(DateTime, default=func.now())

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text)
    message_type = Column(String, default="text")  # text, image, file
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_message_chat_created', 'chat_id', 'created_at'),
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ============== Pydantic Models ==============
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    display_name: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 30:
            raise ValueError('Username must be at most 30 characters')
        if not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_online: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    name: Optional[str] = None
    is_group: bool = False
    member_ids: List[int] = []

class ChatResponse(BaseModel):
    id: int
    name: Optional[str]
    is_group: bool
    members: List[UserResponse]
    last_message: Optional[Message] = None
    created_at: datetime

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    chat_id: int
    content: str
    message_type: str = "text"

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    sender: Optional[UserResponse] = None
    content: str
    message_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) < 1:
            raise ValueError('Username is required')
        return v.strip().lower()

# ============== Auth ==============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user

# ============== WebSocket Manager ==============
import threading

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # user_id -> websocket
        self._lock = threading.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        with self._lock:
            self.active_connections[user_id] = websocket
        # Update user online status
        async with async_session() as session:
            from sqlalchemy import select, update
            await session.execute(update(User).where(User.id == user_id).values(is_online=True))
            await session.commit()

    def disconnect(self, user_id: int):
        with self._lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
        # Update user offline status
        asyncio.create_task(self._set_offline(user_id))

    async def _set_offline(self, user_id: int):
        try:
            async with async_session() as session:
                from sqlalchemy import update
                await session.execute(update(User).where(User.id == user_id).values(is_online=False))
                await session.commit()
        except:
            pass

    async def send_personal(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast(self, message: dict, chat_id: int):
        # Send to all members of the chat
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(ChatMember.user_id).where(ChatMember.chat_id == chat_id)
            )
            member_ids = result.scalars().all()
        
        for user_id in member_ids:
            if user_id in self.active_connections:
                await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

# ============== Cache ==============
import redis.asyncio as redis
from functools import wraps
import hashlib
import json

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return None
    return redis_client

async def invalidate_user_cache(user_id: int):
    """Invalidate all cache for a user"""
    r = await get_redis()
    if r:
        try:
            await r.delete(f"chats:user:{user_id}")
        except Exception:
            pass

# ============== FastAPI App ==============
app = FastAPI(title="Chat App API", version="1.0.0")
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
async def startup():
    await init_db()

# ============== Auth Routes ==============
@app.post("/auth/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate):
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == user.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        result = await session.execute(select(User).where(User.email == user.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")
        
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            display_name=user.display_name or user.username
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, login_request: LoginRequest):
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == login_request.username))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(login_request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ============== User Routes ==============
@app.get("/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_user)):
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.id != current_user.id))
        return result.scalars().all()

# ============== Chat Routes ==============
@app.get("/chats", response_model=List[ChatResponse])
async def get_chats(current_user: User = Depends(get_current_user)):
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Chat)
            .join(ChatMember)
            .where(ChatMember.user_id == current_user.id)
            .order_by(Chat.created_at.desc())
        )
        chats = result.scalars().all()
        
        response = []
        for chat in chats:
            # Get members
            members_result = await session.execute(
                select(User).join(ChatMember).where(ChatMember.chat_id == chat.id)
            )
            members = members_result.scalars().all()
            
            # Get last message
            last_msg_result = await session.execute(
                select(Message)
                .where(Message.chat_id == chat.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_message = last_msg_result.scalar_one_or_none()
            
            response.append(ChatResponse(
                id=chat.id,
                name=chat.name,
                is_group=chat.is_group,
                members=members,
                last_message=last_message,
                created_at=chat.created_at
            ))
        return response

@app.post("/chats", response_model=ChatResponse)
async def create_chat(chat: ChatCreate, current_user: User = Depends(get_current_user)):
    async with async_session() as session:
        from sqlalchemy import select
        
        # Create chat
        new_chat = Chat(name=chat.name, is_group=chat.is_group)
        session.add(new_chat)
        await session.commit()
        await session.refresh(new_chat)
        
        # Add members
        member_ids = chat.member_ids + [current_user.id]
        for user_id in member_ids:
            member = ChatMember(chat_id=new_chat.id, user_id=user_id)
            session.add(member)
        
        # If group with no name, auto-generate
        if chat.is_group and not chat.name:
            users_result = await session.execute(
                select(User).where(User.id.in_(member_ids))
            )
            users = users_result.scalars().all()
            names = [u.display_name or u.username for u in users[:3]]
            new_chat.name = ", ".join(names) + ("..." if len(users) > 3 else "")
        
        await session.commit()
        
        # Get members for response
        members_result = await session.execute(
            select(User).where(User.id.in_(member_ids))
        )
        members = members_result.scalars().all()
        
        return ChatResponse(
            id=new_chat.id,
            name=new_chat.name,
            is_group=new_chat.is_group,
            members=members,
            created_at=new_chat.created_at
        )

@app.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
@limiter.limit("30/minute")
async def get_messages(request: Request, chat_id: int, limit: int = 50, before: Optional[int] = None, 
                      after: Optional[int] = None, current_user: User = Depends(get_current_user)):
    # Cap limit to prevent abuse
    limit = min(limit, 100)
    
    async with async_session() as session:
        from sqlalchemy import select, func
        
        # Verify user is member
        result = await session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member of this chat")
        
        # Get messages with optimized query
        query = (
            select(Message, User)
            .join(User, Message.sender_id == User.id)
            .where(Message.chat_id == chat_id)
        )
        
        if before:
            # Load older messages (pagination backward)
            query = query.where(Message.id < before)
        elif after:
            # Load newer messages (pagination forward)
            query = query.where(Message.id > after)
        
        # Order and limit - for forward pagination, reverse the order
        if after:
            query = query.order_by(Message.created_at.asc()).limit(limit)
        else:
            query = query.order_by(Message.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        rows = result.all()
        
        # Build response
        response = []
        for msg, sender in rows:
            response.append(MessageResponse(
                id=msg.id,
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                sender=UserResponse(
                    id=sender.id,
                    username=sender.username,
                    email=sender.email,
                    display_name=sender.display_name,
                    avatar_url=sender.avatar_url,
                    is_online=sender.is_online,
                    created_at=sender.created_at
                ),
                content=msg.content,
                message_type=msg.message_type,
                is_read=msg.is_read,
                created_at=msg.created_at
            ))
        
        # Reverse if we paginated forward (to maintain chronological order)
        if after:
            response = list(reversed(response))
        
        return response

# ============== WebSocket ==============
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except:
        await websocket.close(code=4001)
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                # Save message to database
                async with async_session() as session:
                    from sqlalchemy import select
                    new_message = Message(
                        chat_id=message_data["chat_id"],
                        sender_id=user_id,
                        content=message_data["content"],
                        message_type=message_data.get("message_type", "text")
                    )
                    session.add(new_message)
                    await session.commit()
                    await session.refresh(new_message)
                    
                    # Get sender info
                    sender_result = await session.execute(select(User).where(User.id == user_id))
                    sender = sender_result.scalar_one_or_none()
                    
                    response = {
                        "type": "message",
                        "id": new_message.id,
                        "chat_id": new_message.chat_id,
                        "sender_id": user_id,
                        "sender_name": sender.display_name if sender else "Unknown",
                        "content": new_message.content,
                        "message_type": new_message.message_type,
                        "created_at": new_message.created_at.isoformat()
                    }
                    
                    # Broadcast to chat members
                    await manager.broadcast(response, new_message.chat_id)
            
            elif message_data.get("type") == "typing":
                # Broadcast typing indicator
                async with async_session() as session:
                    from sqlalchemy import select
                    sender_result = await session.execute(select(User).where(User.id == user_id))
                    sender = sender_result.scalar_one_or_none()
                
                response = {
                    "type": "typing",
                    "chat_id": message_data["chat_id"],
                    "user_id": user_id,
                    "user_name": sender.display_name if sender else "Unknown"
                }
                await manager.broadcast(response, message_data["chat_id"])
                
            elif message_data.get("type") == "read":
                # Mark messages as read
                async with async_session() as session:
                    from sqlalchemy import update
                    await session.execute(
                        update(Message)
                        .where(Message.chat_id == message_data["chat_id"])
                        .values(is_read=True)
                    )
                    await session.commit()

    except WebSocketDisconnect:
        manager.disconnect(user_id)

# ============== Additional Endpoints ==============

# Update user profile
class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

@app.put("/users/me", response_model=UserResponse)
async def update_profile(
    profile: ProfileUpdate, 
    current_user: User = Depends(get_current_user)
):
    async with async_session() as session:
        from sqlalchemy import update
        update_data = {}
        if profile.display_name:
            update_data["display_name"] = profile.display_name
        if profile.avatar_url:
            update_data["avatar_url"] = profile.avatar_url
        
        await session.execute(
            update(User).where(User.id == current_user.id).values(**update_data)
        )
        await session.commit()
        
        # Fetch updated user
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.id == current_user.id))
        return result.scalar_one()

# Delete message (soft delete)
@app.delete("/messages/{message_id}")
async def delete_message(
    message_id: int, 
    current_user: User = Depends(get_current_user)
):
    async with async_session() as session:
        from sqlalchemy import select, update
        
        # Check if message exists and user is sender
        result = await session.execute(
            select(Message).where(
                Message.id == message_id,
                Message.sender_id == current_user.id
            )
        )
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found or not authorized")
        
        # Soft delete - clear content
        await session.execute(
            update(Message).where(Message.id == message_id).values(content="[deleted]")
        )
        await session.commit()
        
        # Invalidate cache
        await invalidate_user_cache(current_user.id)
        
        return {"status": "deleted"}

# Leave chat
@app.post("/chats/{chat_id}/leave")
async def leave_chat(
    chat_id: int, 
    current_user: User = Depends(get_current_user)
):
    async with async_session() as session:
        from sqlalchemy import select, delete
        
        # Verify user is member
        result = await session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == current_user.id
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(status_code=404, detail="Not a member of this chat")
        
        # Don't allow leaving if only one member
        count_result = await session.execute(
            select(ChatMember).where(ChatMember.chat_id == chat_id)
        )
        members_count = len(count_result.scalars().all())
        
        if members_count <= 1:
            # Delete the chat instead
            await session.execute(delete(Chat).where(Chat.id == chat_id))
        else:
            await session.execute(
                delete(ChatMember).where(
                    ChatMember.chat_id == chat_id,
                    ChatMember.user_id == current_user.id
                )
            )
        
        await session.commit()
        
        # Invalidate cache
        await invalidate_user_cache(current_user.id)
        
        return {"status": "left"}

# Get chat by ID
@app.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: int, current_user: User = Depends(get_current_user)):
    async with async_session() as session:
        from sqlalchemy import select
        
        # Verify user is member
        result = await session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member of this chat")
        
        # Get chat
        chat_result = await session.execute(select(Chat).where(Chat.id == chat_id))
        chat = chat_result.scalar_one_or_none()
        
        # Get members
        members_result = await session.execute(
            select(User).join(ChatMember).where(ChatMember.chat_id == chat_id)
        )
        members = members_result.scalars().all()
        
        # Get last message
        last_msg_result = await session.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_message = last_msg_result.scalar_one_or_none()
        
        return ChatResponse(
            id=chat.id,
            name=chat.name,
            is_group=chat.is_group,
            members=members,
            last_message=last_message,
            created_at=chat.created_at
        )

# Search messages
@app.get("/chats/{chat_id}/search")
async def search_messages(
    chat_id: int, 
    q: str, 
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    async with async_session() as session:
        from sqlalchemy import select
        
        # Verify user is member
        result = await session.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not a member of this chat")
        
        # Search messages
        query = (
            select(Message, User)
            .join(User, Message.sender_id == User.id)
            .where(
                Message.chat_id == chat_id,
                Message.content.contains(q)
            )
            .order_by(Message.created_at.desc())
            .limit(min(limit, 50))
        )
        
        result = await session.execute(query)
        rows = result.all()
        
        response = []
        for msg, sender in rows:
            response.append(MessageResponse(
                id=msg.id,
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                sender=UserResponse(
                    id=sender.id,
                    username=sender.username,
                    email=sender.email,
                    display_name=sender.display_name,
                    avatar_url=sender.avatar_url,
                    is_online=sender.is_online,
                    created_at=sender.created_at
                ),
                content=msg.content,
                message_type=msg.message_type,
                is_read=msg.is_read,
                created_at=msg.created_at
            ))
        
        return response

# ============== Health Check ==============
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
