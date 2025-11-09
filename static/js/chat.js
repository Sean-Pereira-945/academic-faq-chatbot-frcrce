// Chat page functionality with anime.js animations

let chatMessages = [];
let isTyping = false;

document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessagesContainer = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const charCount = document.getElementById('charCount');
    const newChatBtn = document.getElementById('newChatBtn');
    const clearChatBtn = document.getElementById('clearChat');
    const exportChatBtn = document.getElementById('exportChat');

    // Initialize animations
    initializeAnimations();

    // Load system status
    loadSystemStatus();

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        
        const length = this.value.length;
        charCount.textContent = length;
        
        // Update send button state
        sendButton.disabled = length === 0 || length > 1000;
        
        // Color code character count
        if (length > 900) {
            charCount.style.color = 'var(--error)';
        } else if (length > 700) {
            charCount.style.color = 'var(--warning)';
        } else {
            charCount.style.color = 'var(--text-tertiary)';
        }
    });

    // Send message on Enter (Shift+Enter for new line)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled) {
                sendMessage();
            }
        }
    });

    // Send button click
    sendButton.addEventListener('click', sendMessage);

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', function() {
            messageInput.value = this.textContent;
            messageInput.dispatchEvent(new Event('input'));
            sendMessage();
            
            // Hide suggestions after use
            anime({
                targets: '.suggestions',
                opacity: [1, 0],
                height: [this.parentElement.parentElement.offsetHeight, 0],
                duration: 300,
                easing: 'easeOutQuad',
                complete: () => {
                    document.querySelector('.suggestions').style.display = 'none';
                }
            });
        });
    });

    // New chat button
    newChatBtn.addEventListener('click', function() {
        if (confirm('Start a new chat? Current conversation will be saved.')) {
            clearChat();
        }
    });

    // Clear chat button
    clearChatBtn.addEventListener('click', function() {
        if (confirm('Clear all messages?')) {
            clearChat();
        }
    });

    // Export chat button
    exportChatBtn.addEventListener('click', exportChat);

    // Send message function
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || isTyping) return;

        // Add user message to UI
        addMessage(message, 'user');

        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        charCount.textContent = '0';
        sendButton.disabled = true;

        // Show typing indicator
        showTypingIndicator();

        try {
            // Send request to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: message })
            });

            const data = await response.json();

            // Hide typing indicator
            hideTypingIndicator();

            if (data.success) {
                addMessage(data.response, 'assistant');
            } else {
                addMessage(data.error || 'An error occurred. Please try again.', 'assistant', true);
            }
        } catch (error) {
            hideTypingIndicator();
            addMessage('Failed to connect to the server. Please check your connection.', 'assistant', true);
            console.error('Error:', error);
        }
    }

    // Add message to chat
    function addMessage(text, sender, isError = false) {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${sender}-wrapper`;
        messageWrapper.style.opacity = '0';

        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageWrapper.innerHTML = `
            <div class="message ${sender}-message">
                <div class="message-avatar">
                    <span>${sender === 'user' ? '👤' : '🤖'}</span>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-sender">${sender === 'user' ? 'You' : 'FinGuide Assistant'}</span>
                        <span class="message-time">${timeString}</span>
                    </div>
                    <div class="message-text ${isError ? 'error-message' : ''}">
                        ${formatMessageText(text)}
                    </div>
                </div>
            </div>
        `;

        chatMessagesContainer.appendChild(messageWrapper);

        // Animate message appearance
        anime({
            targets: messageWrapper,
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 400,
            easing: 'easeOutQuad'
        });

        // Scroll to bottom
        scrollToBottom();

        // Store message
        chatMessages.push({
            text,
            sender,
            timestamp: now
        });
    }

    // Format message text (preserve line breaks, etc.)
    function formatMessageText(text) {
        // Convert markdown-style formatting
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/\n/g, '<br>');
        
        // Convert source citations to styled elements
    text = text.replace(/\[Source: (.*?)\]/g, '<span class="source-citation">� $1</span>');
        
        return `<p>${text}</p>`;
    }

    // Show typing indicator
    function showTypingIndicator() {
        isTyping = true;
        typingIndicator.style.display = 'flex';
        typingIndicator.style.opacity = '0';
        
        anime({
            targets: typingIndicator,
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuad'
        });
        
        scrollToBottom();
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        isTyping = false;
        
        anime({
            targets: typingIndicator,
            opacity: [1, 0],
            duration: 300,
            easing: 'easeOutQuad',
            complete: () => {
                typingIndicator.style.display = 'none';
            }
        });
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        anime({
            targets: chatMessagesContainer,
            scrollTop: chatMessagesContainer.scrollHeight,
            duration: 400,
            easing: 'easeOutQuad'
        });
    }

    // Clear chat
    function clearChat() {
        chatMessages = [];
        
        const messages = chatMessagesContainer.querySelectorAll('.message-wrapper');
        
        anime({
            targets: messages,
            opacity: [1, 0],
            translateY: [0, -20],
            duration: 300,
            delay: anime.stagger(50),
            easing: 'easeOutQuad',
            complete: () => {
                chatMessagesContainer.innerHTML = `
                    <div class="message-wrapper assistant-wrapper">
                        <div class="message assistant-message">
                            <div class="message-avatar">
                                <span>🤖</span>
                            </div>
                            <div class="message-content">
                                <div class="message-header">
                                    <span class="message-sender">FinGuide Assistant</span>
                                    <span class="message-time">${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                                <div class="message-text">
                                    <p>Hello! I'm your AI finance coach. I can help with budgeting strategies, investment basics, credit scores, and tax planning.</p>
                                    <p>What money goal can I assist with?</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="suggestions">
                        <div class="suggestions-title">Try asking:</div>
                        <div class="suggestions-grid">
                            <button class="suggestion-chip">How much should I save each month?</button>
                            <button class="suggestion-chip">What is a good credit score?</button>
                            <button class="suggestion-chip">How can I start investing with $500?</button>
                            <button class="suggestion-chip">Which expenses are tax deductible?</button>
                        </div>
                    </div>
                `;
                
                // Reattach suggestion chip listeners
                document.querySelectorAll('.suggestion-chip').forEach(chip => {
                    chip.addEventListener('click', function() {
                        messageInput.value = this.textContent;
                        messageInput.dispatchEvent(new Event('input'));
                        sendMessage();
                    });
                });
            }
        });
    }

    // Export chat
    function exportChat() {
        if (chatMessages.length === 0) {
            alert('No messages to export!');
            return;
        }

        const chatText = chatMessages.map(msg => {
            const time = msg.timestamp.toLocaleString();
            return `[${time}] ${msg.sender === 'user' ? 'You' : 'Assistant'}: ${msg.text}`;
        }).join('\n\n');

        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Show success animation
        anime({
            targets: exportChatBtn,
            scale: [1, 1.1, 1],
            duration: 300,
            easing: 'easeOutElastic(1, .6)'
        });
    }

    // Load system status
    async function loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            document.getElementById('kbStatus').textContent = data.is_trained ? '✓ Loaded' : '✗ Not Loaded';
            document.getElementById('kbStatus').style.color = data.is_trained ? 'var(--success)' : 'var(--error)';
            
            document.getElementById('modelStatus').textContent = data.embedding_backend || 'N/A';
        } catch (error) {
            console.error('Failed to load status:', error);
        }
    }

    // Initialize page animations
    function initializeAnimations() {
        // Animate sidebar
        anime({
            targets: '.sidebar',
            translateX: [-280, 0],
            opacity: [0, 1],
            duration: 600,
            easing: 'easeOutQuad'
        });

        // Animate info panel
        anime({
            targets: '.info-panel',
            translateX: [320, 0],
            opacity: [0, 1],
            duration: 600,
            easing: 'easeOutQuad'
        });

        // Animate welcome message
        anime({
            targets: '.message-wrapper',
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 600,
            delay: 300,
            easing: 'easeOutQuad'
        });

        // Animate suggestions
        anime({
            targets: '.suggestions',
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 600,
            delay: 500,
            easing: 'easeOutQuad'
        });

        // Animate input area
        anime({
            targets: '.input-container',
            translateY: [50, 0],
            opacity: [0, 1],
            duration: 600,
            delay: 400,
            easing: 'easeOutQuad'
        });
    }

    console.log('Chat page initialized');
});
