package com.chatapp.android.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chatapp.android.data.model.*
import com.chatapp.android.data.repository.AuthRepository
import com.chatapp.android.data.repository.ChatRepository
import com.chatapp.android.data.repository.WebSocketRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val chatRepository: ChatRepository,
    private val webSocketRepository: WebSocketRepository
) : ViewModel() {
    
    val isLoggedIn = authRepository.isLoggedIn
    
    private val _loginState = MutableStateFlow<LoginState>(LoginState.Idle)
    val loginState: StateFlow<LoginState> = _loginState.asStateFlow()
    
    private val _registerState = MutableStateFlow<RegisterState>(RegisterState.Idle)
    val registerState: StateFlow<RegisterState> = _registerState.asStateFlow()
    
    private val _chats = MutableStateFlow<List<Chat>>(emptyList())
    val chats: StateFlow<List<Chat>> = _chats.asStateFlow()
    
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()
    
    private val _messages = MutableStateFlow<List<Message>>(emptyList())
    val messages: StateFlow<List<Message>> = _messages.asStateFlow()
    
    private val _currentChat = MutableStateFlow<Chat?>(null)
    val currentChat: StateFlow<Chat?> = _currentChat.asStateFlow()
    
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    init {
        viewModelScope.launch {
            webSocketRepository.setMessageListener { wsMessage ->
                handleWebSocketMessage(wsMessage)
            }
        }
    }
    
    fun login(username: String, password: String) {
        viewModelScope.launch {
            _loginState.value = LoginState.Loading
            val result = authRepository.login(username, password)
            _loginState.value = result.fold(
                onSuccess = { LoginState.Success },
                onFailure = { LoginState.Error(it.message ?: "Login failed") }
            )
            
            if (result.isSuccess) {
                loadChats()
                webSocketRepository.connect()
            }
        }
    }
    
    fun register(username: String, email: String, password: String, displayName: String?) {
        viewModelScope.launch {
            _registerState.value = RegisterState.Loading
            val result = authRepository.register(username, email, password, displayName)
            _registerState.value = result.fold(
                onSuccess = { RegisterState.Success },
                onFailure = { RegisterState.Error(it.message ?: "Registration failed") }
            )
        }
    }
    
    fun loadChats() {
        viewModelScope.launch {
            _isLoading.value = true
            chatRepository.getChats().onSuccess { _chats.value = it }
            _isLoading.value = false
        }
    }
    
    fun loadUsers() {
        viewModelScope.launch {
            chatRepository.getUsers().onSuccess { _users.value = it }
        }
    }
    
    fun createChat(name: String?, isGroup: Boolean, memberIds: List<Int>) {
        viewModelScope.launch {
            chatRepository.createChat(name, isGroup, memberIds).onSuccess {
                loadChats()
            }
        }
    }
    
    fun loadMessages(chatId: Int) {
        viewModelScope.launch {
            _isLoading.value = true
            chatRepository.getMessages(chatId).onSuccess { _messages.value = it }
            _isLoading.value = false
        }
    }
    
    fun sendMessage(chatId: Int, content: String) {
        webSocketRepository.sendMessage(chatId, content)
    }
    
    fun sendTyping(chatId: Int) {
        webSocketRepository.sendTyping(chatId)
    }
    
    fun markAsRead(chatId: Int) {
        webSocketRepository.sendRead(chatId)
    }
    
    private fun handleWebSocketMessage(wsMessage: WebSocketMessage) {
        when (wsMessage.type) {
            "message" -> {
                // Add new message to list
                if (wsMessage.chatId != null && wsMessage.content != null) {
                    val newMessage = Message(
                        id = wsMessage.id ?: 0,
                        chatId = wsMessage.chatId,
                        senderId = wsMessage.senderId ?: 0,
                        sender = null,
                        content = wsMessage.content,
                        messageType = wsMessage.messageType ?: "text",
                        isRead = false,
                        createdAt = wsMessage.createdAt ?: ""
                    )
                    _messages.update { listOf(newMessage) + it }
                }
            }
            "typing" -> {
                // Handle typing indicator
            }
        }
    }
    
    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            webSocketRepository.disconnect()
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        webSocketRepository.disconnect()
    }
}

sealed class LoginState {
    object Idle : LoginState()
    object Loading : LoginState()
    object Success : LoginState()
    data class Error(val message: String) : LoginState()
}

sealed class RegisterState {
    object Idle : RegisterState()
    object Loading : RegisterState()
    object Success : RegisterState()
    data class Error(val message: String) : RegisterState()
}
