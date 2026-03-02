package com.chatapp.android.data.api

import com.chatapp.android.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ChatApiService {
    
    // Auth
    @POST("auth/register")
    suspend fun register(@Body user: UserCreate): Response<User>
    
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<Token>
    
    @GET("auth/me")
    suspend fun getCurrentUser(): Response<User>
    
    // Users
    @GET("users")
    suspend fun getUsers(): Response<List<User>>
    
    // Chats
    @GET("chats")
    suspend fun getChats(): Response<List<Chat>>
    
    @POST("chats")
    suspend fun createChat(@Body chat: ChatCreate): Response<Chat>
    
    // Messages
    @GET("chats/{chatId}/messages")
    suspend fun getMessages(
        @Path("chatId") chatId: Int,
        @Query("limit") limit: Int = 50,
        @Query("before") before: Int? = null
    ): Response<List<Message>>
}
