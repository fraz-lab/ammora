// API Base URL
const API_BASE = 'https://ammora.onrender.com/api';

// Global state
let currentUserId = null;
let currentUsername = null;

// DOM Elements
const onboardingScreen = document.getElementById('onboarding-screen');
const preferencesScreen = document.getElementById('preferences-screen');
const chatScreen = document.getElementById('chat-screen');
const registrationForm = document.getElementById('registration-form');
const preferencesForm = document.getElementById('preferences-form');
const chatForm = document.getElementById('chat-form');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const userNameDisplay = document.getElementById('user-name-display');
const skipPreferencesBtn = document.getElementById('skip-preferences');
const newChatBtn = document.getElementById('new-chat-btn');

// Check for existing user session
window.addEventListener('DOMContentLoaded', () => {
    const savedUserId = localStorage.getItem('userId');
    const savedUsername = localStorage.getItem('username');

    if (savedUserId && savedUsername) {
        currentUserId = savedUserId;
        currentUsername = savedUsername;
        showChatScreen();
        loadChatHistory();
    }
});

// Registration Form Handler
registrationForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const age = document.getElementById('age').value;

    if (!username || !age) {
        alert('Please fill in all fields');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/user/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, age: parseInt(age) })
        });

        const data = await response.json();

        if (response.ok) {
            currentUserId = data.user_id;
            currentUsername = data.username;

            // Save to localStorage
            localStorage.setItem('userId', currentUserId);
            localStorage.setItem('username', currentUsername);

            // Show preferences screen
            showScreen('preferences');
        } else {
            alert(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('Failed to register. Please try again.');
    }
});

// Preferences Form Handler
preferencesForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const preferences = {
        relationship_style: document.getElementById('relationship_style').value,
        emotional_needs: document.getElementById('emotional_needs').value.trim(),
        conversation_topics: document.getElementById('conversation_topics').value.trim(),
        love_language: document.getElementById('love_language').value
    };

    await savePreferences(preferences);
});

// Skip Preferences Button
skipPreferencesBtn.addEventListener('click', () => {
    showChatScreen();
});

// Save Preferences Function
async function savePreferences(preferences) {
    try {
        const response = await fetch(`${API_BASE}/user/preferences`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUserId,
                preferences: preferences
            })
        });

        if (response.ok) {
            showChatScreen();
        } else {
            const data = await response.json();
            alert(data.error || 'Failed to save preferences');
        }
    } catch (error) {
        console.error('Preferences error:', error);
        alert('Failed to save preferences. Please try again.');
    }
}

// Chat Form Handler
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to UI
    addMessage('user', message);

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Disable send button
    sendBtn.disabled = true;

    // Show typing indicator
    showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: currentUserId,
                message: message
            })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        if (response.ok) {
            // Add assistant message to UI
            addMessage('assistant', data.message);
        } else {
            alert(data.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator();
        alert('Failed to send message. Please try again.');
    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
});

// Auto-resize textarea
messageInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Handle Enter key (send) vs Shift+Enter (new line)
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// New Chat Button
newChatBtn.addEventListener('click', () => {
    if (confirm('Start a new chat? This will clear your current conversation.')) {
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
        currentUserId = null;
        currentUsername = null;
        location.reload();
    }
});

// Screen Management
function showScreen(screenName) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });

    if (screenName === 'onboarding') {
        onboardingScreen.classList.add('active');
    } else if (screenName === 'preferences') {
        preferencesScreen.classList.add('active');
    } else if (screenName === 'chat') {
        chatScreen.classList.add('active');
    }
}

function showChatScreen() {
    showScreen('chat');
    userNameDisplay.textContent = currentUsername;
    messageInput.focus();
}

// Add Message to Chat
function addMessage(role, content) {
    // Remove welcome message if it exists
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = content;

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageContent.appendChild(messageText);
    messageContent.appendChild(messageTime);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Typing Indicator
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.style.background = 'var(--primary-gradient)';
    avatar.textContent = '🤖';

    const dotsContainer = document.createElement('div');
    dotsContainer.className = 'typing-dots';

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.className = 'typing-dot';
        dotsContainer.appendChild(dot);
    }

    typingDiv.appendChild(avatar);
    typingDiv.appendChild(dotsContainer);

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Load Chat History
async function loadChatHistory() {
    try {
        const response = await fetch(`${API_BASE}/messages/${currentUserId}`);
        const data = await response.json();

        if (response.ok && data.messages.length > 0) {
            // Remove welcome message
            const welcomeMessage = chatMessages.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }

            // Add all messages
            data.messages.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}
