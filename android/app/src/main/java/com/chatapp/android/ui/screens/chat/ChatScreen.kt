package com.chatapp.android.ui.screens.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chatapp.android.data.model.Message

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    chatId: Int,
    onBack: () -> Unit,
    viewModel: ChatViewModel = hiltViewModel()
) {
    var messageText by remember { mutableStateOf("") }
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val listState = rememberLazyListState()
    
    LaunchedEffect(chatId) {
        viewModel.loadMessages(chatId)
        viewModel.markAsRead(chatId)
    }
    
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(0)
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Chat") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Messages list
            if (isLoading && messages.isEmpty()) {
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp),
                    state = listState,
                    reverseLayout = true
                ) {
                    items(messages) { message ->
                        MessageItem(
                            message = message,
                            isOwnMessage = message.senderId == 1 // TODO: Get current user ID
                        )
                    }
                }
            }
            
            // Input area
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shadowElevation = 8.dp
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = messageText,
                        onValueChange = { 
                            messageText = it
                            viewModel.sendTyping(chatId)
                        },
                        modifier = Modifier.weight(1f),
                        placeholder = { Text("Type a message...") },
                        maxLines = 4,
                        shape = RoundedCornerShape(24.dp)
                    )
                    
                    Spacer(modifier = Modifier.width(8.dp))
                    
                    FilledIconButton(
                        onClick = {
                            if (messageText.isNotBlank()) {
                                viewModel.sendMessage(chatId, messageText)
                                messageText = ""
                            }
                        },
                        enabled = messageText.isNotBlank()
                    ) {
                        Icon(Icons.Filled.Send, contentDescription = "Send")
                    }
                }
            }
        }
    }
}

@Composable
fun MessageItem(
    message: Message,
    isOwnMessage: Boolean
) {
    val alignment = if (isOwnMessage) Alignment.End else Alignment.Start
    val backgroundColor = if (isOwnMessage) 
        MaterialTheme.colorScheme.primary 
    else 
        MaterialTheme.colorScheme.surfaceVariant
    val textColor = if (isOwnMessage)
        MaterialTheme.colorScheme.onPrimary
    else
        MaterialTheme.colorScheme.onSurfaceVariant
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalAlignment = alignment
    ) {
        if (!isOwnMessage && message.sender?.displayName != null) {
            Text(
                text = message.sender.displayName,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 2.dp)
            )
        }
        
        Box(
            modifier = Modifier
                .widthIn(max = 280.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(backgroundColor)
                .padding(horizontal = 12.dp, vertical = 8.dp)
        ) {
            Text(
                text = message.content,
                color = textColor,
                style = MaterialTheme.typography.bodyMedium
            )
        }
        
        Text(
            text = formatTime(message.createdAt),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 2.dp)
        )
    }
}

private fun formatTime(timestamp: String): String {
    return try {
        // Simple time extraction - in production, parse properly
        if (timestamp.contains("T")) {
            timestamp.substringAfter("T").substring(0, 5)
        } else {
            timestamp.take(5)
        }
    } catch (e: Exception) {
        ""
    }
}
