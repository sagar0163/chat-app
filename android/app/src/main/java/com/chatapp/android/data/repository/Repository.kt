package com.chatapp.android.data.repository

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.chatapp.android.data.api.ChatApiService
import com.chatapp.android.data.model.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import okhttp3.*
import okio.ByteString
import org.json.JSONObject
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "chat_prefs")

@Singleton
class AuthRepository @Inject constructor(
    private val api: ChatApiService,
    private val context: Context
) {
    private val tokenKey = stringPreferencesKey("auth_token")
    
    val isLoggedIn: Flow<Boolean> = context.dataStore.data.map { prefs ->
        prefs[tokenKey] != null
    }
    
    suspend fun getToken(): String? = context.dataStore.data.first()[tokenKey]
    
    suspend fun login(username: String, password: String): Result<Token> {
        return try {
            val response = api.login(LoginRequest(username, password))
            if (response.isSuccessful) {
                response.body()?.let { token ->
                    saveToken(token.accessToken)
                    Result.success(token)
                } ?: Result.failure(Exception("Empty response"))
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Login failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun register(username: String, email: String, password: String, displayName: String?): Result<User> {
        return try {
            val response = api.register(UserCreate(username, email, password, displayName))
            if (response.isSuccessful) {
                response.body()?.let { Result.success(it) }
                    ?: Result.failure(Exception("Empty response"))
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Registration failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun saveToken(token: String) {
        context.dataStore.edit { prefs ->
            prefs[tokenKey] = token
        }
    }
    
    suspend fun logout() {
        context.dataStore.edit { prefs ->
            prefs.remove(tokenKey)
        }
    }
}

@Singleton
class ChatRepository @Inject constructor(
    private val api: ChatApiService
) {
    suspend fun getChats(): Result<List<Chat>> {
        return try {
            val response = api.getChats()
            if (response.isSuccessful) {
                Result.success(response.body() ?: emptyList())
            } else {
                Result.failure(Exception("Failed to get chats"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getUsers(): Result<List<User>> {
        return try {
            val response = api.getUsers()
            if (response.isSuccessful) {
                Result.success(response.body() ?: emptyList())
            } else {
                Result.failure(Exception("Failed to get users"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun createChat(name: String?, isGroup: Boolean, memberIds: List<Int>): Result<Chat> {
        return try {
            val response = api.createChat(ChatCreate(name, isGroup, memberIds))
            if (response.isSuccessful) {
                response.body()?.let { Result.success(it) }
                    ?: Result.failure(Exception("Empty response"))
            } else {
                Result.failure(Exception("Failed to create chat"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getMessages(chatId: Int): Result<List<Message>> {
        return try {
            val response = api.getMessages(chatId)
            if (response.isSuccessful) {
                Result.success(response.body() ?: emptyList())
            } else {
                Result.failure(Exception("Failed to get messages"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

@Singleton
class WebSocketRepository @Inject constructor(
    private val authRepository: AuthRepository
) {
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private var messageListener: ((WebSocketMessage) -> Unit)? = null
    
    suspend fun connect() {
        val token = authRepository.getToken() ?: return
        
        val request = Request.Builder()
            .url("ws://10.0.2.2:8000/ws/$token")
            .build()
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                println("WebSocket connected")
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    val message = WebSocketMessage(
                        type = json.getString("type"),
                        id = json.optInt("id", 0).takeIf { it != 0 },
                        chatId = json.optInt("chat_id", 0).takeIf { it != 0 },
                        senderId = json.optInt("sender_id", 0).takeIf { it != 0 },
                        senderName = json.optString("sender_name").takeIf { it.isNotEmpty() },
                        content = json.optString("content").takeIf { it.isNotEmpty() },
                        messageType = json.optString("message_type").takeIf { it.isNotEmpty() },
                        createdAt = json.optString("created_at").takeIf { it.isNotEmpty() },
                        userId = json.optInt("user_id", 0).takeIf { it != 0 },
                        userName = json.optString("user_name").takeIf { it.isNotEmpty() }
                    )
                    messageListener?.invoke(message)
                } catch (e: Exception) {
                    println("Parse error: ${e.message}")
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                println("WebSocket error: ${t.message}")
            }
        })
    }
    
    fun sendMessage(chatId: Int, content: String) {
        val json = JSONObject().apply {
            put("type", "message")
            put("chat_id", chatId)
            put("content", content)
            put("message_type", "text")
        }
        webSocket?.send(json.toString())
    }
    
    fun sendTyping(chatId: Int) {
        val json = JSONObject().apply {
            put("type", "typing")
            put("chat_id", chatId)
        }
        webSocket?.send(json.toString())
    }
    
    fun sendRead(chatId: Int) {
        val json = JSONObject().apply {
            put("type", "read")
            put("chat_id", chatId)
        }
        webSocket?.send(json.toString())
    }
    
    fun setMessageListener(listener: (WebSocketMessage) -> Unit) {
        messageListener = listener
    }
    
    fun disconnect() {
        webSocket?.close(1000, "User disconnected")
        webSocket = null
    }
}
