package com.chatapp.android.ui.screens.chat

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.chatapp.android.data.model.Chat

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatListScreen(
    onChatClick: (Int) -> Unit,
    onLogout: () -> Unit,
    viewModel: ChatViewModel = hiltViewModel()
) {
    val chats by viewModel.chats.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    var showNewChatDialog by remember { mutableStateOf(false) }
    
    LaunchedEffect(Unit) {
        viewModel.loadChats()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Chats") },
                actions = {
                    IconButton(onClick = { showNewChatDialog = true }) {
                        Icon(Icons.Default.Add, contentDescription = "New Chat")
                    }
                    IconButton(onClick = {
                        viewModel.logout()
                        onLogout()
                    }) {
                        Icon(Icons.Default.Logout, contentDescription = "Logout")
                    }
                }
            )
        }
    ) { padding ->
        if (isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (chats.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("No chats yet")
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(onClick = { showNewChatDialog = true }) {
                        Text("Start a conversation")
                    }
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
            ) {
                items(chats) { chat ->
                    ChatListItem(
                        chat = chat,
                        onClick = { onChatClick(chat.id) }
                    )
                }
            }
        }
    }
    
    if (showNewChatDialog) {
        NewChatDialog(
            onDismiss = { showNewChatDialog = false },
            onCreateChat = { name, isGroup, memberIds ->
                viewModel.createChat(name, isGroup, memberIds)
                showNewChatDialog = false
            }
        )
    }
}

@Composable
fun ChatListItem(
    chat: Chat,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            shape = MaterialTheme.shapes.medium,
            color = MaterialTheme.colorScheme.primaryContainer,
            modifier = Modifier.size(48.dp)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = (chat.name?.firstOrNull() ?: 'C').uppercase(),
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }
        
        Spacer(modifier = Modifier.width(16.dp))
        
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = chat.name ?: "Chat",
                style = MaterialTheme.typography.titleMedium
            )
            chat.lastMessage?.let { msg ->
                Text(
                    text = msg.content,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1
                )
            }
        }
    }
    
    Divider()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewChatDialog(
    onDismiss: () -> Unit,
    onCreateChat: (String?, Boolean, List<Int>) -> Unit
) {
    var isGroup by remember { mutableStateOf(false) }
    var chatName by remember { mutableStateOf("") }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("New Chat") },
        text = {
            Column {
                OutlinedTextField(
                    value = chatName,
                    onValueChange = { chatName = it },
                    label = { Text("Chat Name") },
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = isGroup,
                        onCheckedChange = { isGroup = it }
                    )
                    Text("Group Chat")
                }
            }
        },
        confirmButton = {
            Button(onClick = { onCreateChat(chatName.ifBlank { null }, isGroup, emptyList()) }) {
                Text("Create")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
