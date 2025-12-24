/**
 * Bot Embed Script
 * 
 * Load this script on your website to enable bot chat widget.
 * 
 * Usage:
 * <script src="https://your-bot-service.com/embed.js" data-site-id="catalog-001"></script>
 * 
 * Or initialize programmatically:
 * BotEmbed.init({ siteId: 'catalog-001', apiUrl: 'https://your-bot-service.com' });
 */

(function() {
    'use strict';

    // Configuration
    const DEFAULT_API_URL = 'http://localhost:8386';
    const DEFAULT_TOKEN_EXPIRY_BUFFER = 60; // Refresh token 60 seconds before expiry
    const DEFAULT_THEME = {
        primaryColor: '#FF6D3B', // Match catalog primary color
        backgroundColor: '#FFFFFF',
        textColor: '#1A1A1A',
        borderRadius: '12px',
    };

    // State
    let config = {
        siteId: null,
        apiUrl: DEFAULT_API_URL,
        token: null,
        tokenExpiry: null,
        sessionId: null,
        botConfig: null,
    };

    let chatState = {
        isOpen: false,
        isInitialized: false,
        messages: [],
        isSending: false,
    };

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    /**
     * Initialize bot embed
     */
    async function init(options = {}) {
        // Get config from window.botConfig, script tag, or options
        const windowConfig = (window.botConfig || {});
        const scriptTag = document.querySelector('script[data-site-id]');
        
        config.siteId = options.siteId || windowConfig.siteId || scriptTag?.dataset.siteId;
        config.apiUrl = options.apiUrl || windowConfig.apiUrl || scriptTag?.dataset.apiUrl || DEFAULT_API_URL;

        // Merge theme config
        if (windowConfig.theme) {
            Object.assign(DEFAULT_THEME, windowConfig.theme);
        }

        if (!config.siteId) {
            console.error('BotEmbed: site_id is required');
            return;
        }

        // Check if already initialized
        if (chatState.isInitialized) {
            console.log('BotEmbed: Already initialized');
            return;
        }

        // Generate session ID
        config.sessionId = generateSessionId();

        // Initialize embed session
        try {
            await initializeEmbed();
            createWidget();
            chatState.isInitialized = true;
            console.log('BotEmbed: Initialized successfully');
        } catch (error) {
            console.error('BotEmbed: Failed to initialize', error);
        }
    }

    /**
     * Initialize embed session and get JWT token
     */
    async function initializeEmbed() {
        const origin = window.location.origin;
        
        const response = await fetch(`${config.apiUrl}/embed/init`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Origin': origin,
            },
            body: JSON.stringify({
                site_id: config.siteId,
                platform: 'web',
                user_data: {}, // Optional: can include user email, name, etc.
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Failed to initialize embed');
        }

        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.message || 'Failed to initialize embed');
        }

        // Store token and config
        config.token = data.data.token;
        config.tokenExpiry = Date.now() + (data.data.expiresIn * 1000);
        config.botConfig = data.data.botConfig;

        // Schedule token refresh
        scheduleTokenRefresh(data.data.expiresIn);

        return data;
    }

    /**
     * Refresh JWT token before expiry
     */
    async function refreshToken() {
        try {
            await initializeEmbed();
        } catch (error) {
            console.error('BotEmbed: Failed to refresh token', error);
            // Retry after delay
            setTimeout(refreshToken, 5000);
        }
    }

    /**
     * Schedule token refresh
     */
    function scheduleTokenRefresh(expiresIn) {
        // Refresh 60 seconds before expiry
        const refreshDelay = (expiresIn - DEFAULT_TOKEN_EXPIRY_BUFFER) * 1000;
        
        if (refreshDelay > 0) {
            setTimeout(refreshToken, refreshDelay);
        }
    }

    /**
     * Generate session ID
     */
    function generateSessionId() {
        return 'session_' + Math.random().toString(36).substring(2, 15) + 
               Math.random().toString(36).substring(2, 15);
    }

    // ========================================================================
    // UI CREATION
    // ========================================================================

    /**
     * Create floating widget
     */
    function createWidget() {
        // Create container
        const container = document.createElement('div');
        container.id = 'bot-embed-container';
        container.innerHTML = `
            <div id="bot-embed-button" class="bot-embed-button">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-message-circle" aria-hidden="true">
                    <path d="M2.992 16.342a2 2 0 0 1 .094 1.167l-1.065 3.29a1 1 0 0 0 1.236 1.168l3.413-.998a2 2 0 0 1 1.099.092 10 10 0 1 0-4.777-4.719"></path>
                </svg>
            </div>
            <div id="bot-embed-window" class="bot-embed-window" style="display: none;">
                <div class="bot-embed-header">
                    <div class="bot-embed-header-content">
                        <div class="bot-embed-avatar">
                            ${config.botConfig?.avatar?.emoji || '🤖'}
                        </div>
                        <div class="bot-embed-header-text">
                            <div class="bot-embed-title">${config.botConfig?.name || 'Chat Bot'}</div>
                            <div class="bot-embed-subtitle">${config.botConfig?.subtitle || 'Chúng tôi có thể giúp gì cho bạn?'}</div>
                        </div>
                    </div>
                    <button id="bot-embed-close" class="bot-embed-close">×</button>
                </div>
                <div id="bot-embed-messages" class="bot-embed-messages"></div>
                <div class="bot-embed-input-container">
                    <input 
                        id="bot-embed-input" 
                        type="text" 
                        class="bot-embed-input" 
                        placeholder="Nhập câu hỏi của bạn..."
                        autocomplete="off"
                    />
                    <button id="bot-embed-send" class="bot-embed-send">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(container);
        injectStyles();

        // Wait a bit for DOM to be ready, then add event listeners
        setTimeout(() => {
            const button = document.getElementById('bot-embed-button');
            const closeBtn = document.getElementById('bot-embed-close');
            const sendBtn = document.getElementById('bot-embed-send');
            const input = document.getElementById('bot-embed-input');

            if (button) {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleChat();
                });
                // Also support touch events for mobile
                button.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleChat();
                });
            }

            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleChat();
                });
            }

            if (sendBtn) {
                sendBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    sendMessage();
                });
            }

            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });
            }
        }, 100);

        // Add welcome message
        addMessage('bot', config.botConfig?.welcomeMessage || 'Xin chào! Tôi có thể giúp gì cho bạn?');
    }

    /**
     * Inject CSS styles
     */
    function injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #bot-embed-container {
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 40;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }

            .bot-embed-button {
                width: 56px;
                height: 56px;
                border-radius: 50%;
                background: linear-gradient(to bottom right, ${DEFAULT_THEME.primaryColor}, #FF8559);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;
                animation: bounce 1s infinite;
                border: none;
                outline: none;
                user-select: none;
                -webkit-tap-highlight-color: transparent;
            }

            .bot-embed-button:hover {
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                transform: scale(1.1);
                animation: none;
            }

            @keyframes bounce {
                0%, 100% {
                    transform: translateY(0);
                }
                50% {
                    transform: translateY(-10px);
                }
            }

            .bot-embed-button svg {
                width: 24px;
                height: 24px;
            }

            .bot-embed-window {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 380px;
                max-width: calc(100vw - 40px);
                height: 600px;
                max-height: calc(100vh - 100px);
                background: ${DEFAULT_THEME.backgroundColor};
                border-radius: ${DEFAULT_THEME.borderRadius};
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .bot-embed-header {
                padding: 16px;
                background: ${DEFAULT_THEME.primaryColor};
                color: white;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .bot-embed-header-content {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .bot-embed-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
            }

            .bot-embed-title {
                font-weight: 600;
                font-size: 16px;
            }

            .bot-embed-subtitle {
                font-size: 12px;
                opacity: 0.9;
            }

            .bot-embed-close {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .bot-embed-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .bot-embed-message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 12px;
                word-wrap: break-word;
            }

            .bot-embed-message.user {
                align-self: flex-end;
                background: ${DEFAULT_THEME.primaryColor};
                color: white;
            }

            .bot-embed-message.bot {
                align-self: flex-start;
                background: #F3F4F6;
                color: ${DEFAULT_THEME.textColor};
            }

            .bot-embed-input-container {
                padding: 16px;
                border-top: 1px solid #E5E7EB;
                display: flex;
                gap: 8px;
            }

            .bot-embed-input {
                flex: 1;
                padding: 12px;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                font-size: 14px;
                outline: none;
            }

            .bot-embed-input:focus {
                border-color: ${DEFAULT_THEME.primaryColor};
            }

            .bot-embed-send {
                padding: 12px;
                background: ${DEFAULT_THEME.primaryColor};
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: opacity 0.2s;
            }

            .bot-embed-send:hover {
                opacity: 0.9;
            }

            .bot-embed-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            @media (max-width: 480px) {
                .bot-embed-window {
                    width: calc(100vw - 20px);
                    height: calc(100vh - 100px);
                    bottom: 10px;
                    right: 10px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // ========================================================================
    // MESSAGE HANDLING
    // ========================================================================

    /**
     * Toggle chat window
     */
    function toggleChat() {
        chatState.isOpen = !chatState.isOpen;
        const window = document.getElementById('bot-embed-window');
        window.style.display = chatState.isOpen ? 'flex' : 'none';
        
        if (chatState.isOpen) {
            document.getElementById('bot-embed-input').focus();
        }
    }

    /**
     * Send message
     */
    async function sendMessage() {
        const input = document.getElementById('bot-embed-input');
        const message = input.value.trim();
        
        if (!message || chatState.isSending) {
            return;
        }

        // Clear input
        input.value = '';

        // Add user message to UI
        addMessage('user', message);

        // Set sending state
        chatState.isSending = true;
        updateSendButton(true);

        try {
            // Check if token needs refresh
            if (Date.now() >= config.tokenExpiry - (DEFAULT_TOKEN_EXPIRY_BUFFER * 1000)) {
                await refreshToken();
            }

            // Send message to bot
            const response = await fetch(`${config.apiUrl}/bot/message?tenant_id=${config.siteId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${config.token}`,
                    'Origin': window.location.origin,
                },
                body: JSON.stringify({
                    message: message,
                    sessionId: config.sessionId,
                    attachments: [],
                }),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired, refresh and retry
                    await refreshToken();
                    return sendMessage(); // Retry with new token
                }
                
                const error = await response.json();
                throw new Error(error.message || 'Failed to send message');
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.message || 'Failed to send message');
            }

            // Add bot response to UI
            addMessage('bot', data.data.response);

        } catch (error) {
            console.error('BotEmbed: Failed to send message', error);
            addMessage('bot', 'Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.');
        } finally {
            chatState.isSending = false;
            updateSendButton(false);
            input.focus();
        }
    }

    /**
     * Add message to chat
     */
    function addMessage(sender, text) {
        const messagesContainer = document.getElementById('bot-embed-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `bot-embed-message ${sender}`;
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Update send button state
     */
    function updateSendButton(disabled) {
        const sendButton = document.getElementById('bot-embed-send');
        sendButton.disabled = disabled;
    }

    // ========================================================================
    // PUBLIC API
    // ========================================================================

    // Expose global API
    window.BotEmbed = {
        init: init,
        open: toggleChat,
        close: () => {
            if (chatState.isOpen) {
                toggleChat();
            }
        },
        sendMessage: sendMessage,
    };

    // Auto-initialize if script tag has data-site-id
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const scriptTag = document.querySelector('script[data-site-id]');
            if (scriptTag) {
                init();
            }
        });
    } else {
        const scriptTag = document.querySelector('script[data-site-id]');
        if (scriptTag) {
            init();
        }
    }

})();

