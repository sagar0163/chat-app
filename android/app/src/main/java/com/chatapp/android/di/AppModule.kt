package com.chatapp.android.di

import android.content.Context
import com.chatapp.android.BuildConfig
import com.chatapp.android.data.api.ChatApiService
import com.chatapp.android.data.repository.AuthRepository
import com.chatapp.android.data.repository.ChatRepository
import com.chatapp.android.data.repository.WebSocketRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideOkHttpClient(@ApplicationContext context: Context): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        val authInterceptor = Interceptor { chain ->
            val token = runBlocking {
                try {
                    val prefs = context.getSharedPreferences("chat_prefs", Context.MODE_PRIVATE)
                    prefs.getString("auth_token", null)
                } catch (e: Exception) {
                    null
                }
            }
            val request = chain.request().newBuilder()
            if (token != null) {
                request.addHeader("Authorization", "Bearer $token")
            }
            chain.proceed(request.build())
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(logging)
            .addInterceptor(authInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    @Provides
    @Singleton
    fun provideChatApiService(retrofit: Retrofit): ChatApiService {
        return retrofit.create(ChatApiService::class.java)
    }
    
    @Provides
    @Singleton
    fun provideAuthRepository(
        api: ChatApiService,
        @ApplicationContext context: Context
    ): AuthRepository {
        return AuthRepository(api, context)
    }
    
    @Provides
    @Singleton
    fun provideChatRepository(api: ChatApiService): ChatRepository {
        return ChatRepository(api)
    }
    
    @Provides
    @Singleton
    fun provideWebSocketRepository(authRepository: AuthRepository): WebSocketRepository {
        return WebSocketRepository(authRepository)
    }
}
