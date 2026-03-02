package com.chatapp.android.data.model

import com.google.gson.annotations.SerializedName

data class User(
    val id: Int,
    val username: String,
    val email: String,
    @SerializedName("display_name") val displayName: String?,
    @SerializedName("avatar_url") val avatarUrl: String?,
    @SerializedName("is_online") val isOnline: Boolean,
    @SerializedName("created_at") val createdAt: String
)

data class UserCreate(
    val username: String,
    val email: String,
    val password: String,
    @SerializedName("display_name") val displayName: String? = null
)

data class LoginRequest(
    val username: String,
    val password: String
)

data class Token(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String
)

data class Chat(
    val id: Int,
    val name: String?,
    @SerializedName("is_group") val isGroup: Boolean,
    val members: List<User>,
    @SerializedName("last_message") val lastMessage: Message?,
    @SerializedName("created_at") val createdAt: String
)

data class ChatCreate(
    val name: String? = null,
    @SerializedName("is_group") val isGroup: Boolean = false,
    @SerializedName("member_ids") val memberIds: List<Int> = emptyList()
)

data class Message(
    val id: Int,
    @SerializedName("chat_id") val chatId: Int,
    @SerializedName("sender_id") val senderId: Int,
    val sender: User?,
    val content: String,
    @SerializedName("message_type") val messageType: String,
    @SerializedName("is_read") val isRead: Boolean,
    @SerializedName("created_at") val createdAt: String
)

data class MessageCreate(
    @SerializedName("chat_id") val chatId: Int,
    val content: String,
    @SerializedName("message_type") val messageType: String = "text"
)

data class WebSocketMessage(
    val type: String,
    val id: Int? = null,
    @SerializedName("chat_id") val chatId: Int? = null,
    @SerializedName("sender_id") val senderId: Int? = null,
    @SerializedName("sender_name") val senderName: String? = null,
    val content: String? = null,
    @SerializedName("message_type") val messageType: String? = null,
    @SerializedName("created_at") val createdAt: String? = null,
    @SerializedName("user_id") val userId: Int? = null,
    @SerializedName("user_name") val userName: String? = null
)
