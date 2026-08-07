/**
 * Gemini AI Assistant - Frontend Application
 */

(function () {
    'use strict';

    // =====================================================
    // State
    // =====================================================
    const state = {
        currentChatId: null,
        isStreaming: false,
        isRecording: false,
        activeUtility: null,
        pendingImageFile: null,
        imageMode: 'analyze',
        settings: {
            theme: 'dark',
            temperature: 0.7,
            max_tokens: 2048,
            voice_enabled: true,
            auto_scroll: true,
        },
    };

    // =====================================================
    // DOM Elements
    // =====================================================
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const elements = {
        sidebar: $('#sidebar'),
        sidebarOverlay: $('#sidebarOverlay'),
        sidebarToggle: $('#sidebarToggle'),
        mobileMenuBtn: $('#mobileMenuBtn'),
        newChatBtn: $('#newChatBtn'),
        searchInput: $('#searchInput'),
        chatHistory: $('#chatHistory'),
        themeToggle: $('#themeToggle'),
        settingsBtn: $('#settingsBtn'),
        utilitiesBtn: $('#utilitiesBtn'),
        exportBtn: $('#exportBtn'),
        deleteChatBtn: $('#deleteChatBtn'),
        chatTitle: $('#chatTitle'),
        chatArea: $('#chatArea'),
        welcomeScreen: $('#welcomeScreen'),
        messagesContainer: $('#messagesContainer'),
        typingIndicator: $('#typingIndicator'),
        messageInput: $('#messageInput'),
        sendBtn: $('#sendBtn'),
        charCounter: $('#charCounter'),
        uploadFileBtn: $('#uploadFileBtn'),
        uploadImageBtn: $('#uploadImageBtn'),
        voiceBtn: $('#voiceBtn'),
        emojiBtn: $('#emojiBtn'),
        pdfInput: $('#pdfInput'),
        imageInput: $('#imageInput'),
        settingsModal: $('#settingsModal'),
        exportModal: $('#exportModal'),
        utilitiesModal: $('#utilitiesModal'),
        imageTransformModal: $('#imageTransformModal'),
        emojiPicker: $('#emojiPicker'),
        emojiGrid: $('#emojiGrid'),
        toastContainer: $('#toastContainer'),
        errorBanner: $('#errorBanner'),
        errorMessage: $('#errorMessage'),
        errorClose: $('#errorClose'),
        loadingOverlay: $('#loadingOverlay'),
        suggestedPrompts: $('#suggestedPrompts'),
        temperatureSlider: $('#temperatureSlider'),
        temperatureValue: $('#temperatureValue'),
        maxTokensInput: $('#maxTokensInput'),
        autoScrollCheck: $('#autoScrollCheck'),
        voiceEnabledCheck: $('#voiceEnabledCheck'),
        clearHistoryBtn: $('#clearHistoryBtn'),
        transformGrid: $('#transformGrid'),
        transformPrompt: $('#transformPrompt'),
    };

    // =====================================================
    // Initialize
    // =====================================================
    document.addEventListener('DOMContentLoaded', init);

    async function init() {
        configureMarked();
        initEmojiPicker();
        bindEvents();
        await loadSettings();
        await loadChatHistory();
    }

    function configureMarked() {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                highlight: (code, lang) => {
                    if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                        return hljs.highlight(code, { language: lang }).value;
                    }
                    return code;
                },
                breaks: true,
                gfm: true,
            });
        }
    }

    // =====================================================
    // Event Bindings
    // =====================================================
    function bindEvents() {
        elements.sidebarToggle.addEventListener('click', toggleSidebarCollapse);
        elements.mobileMenuBtn.addEventListener('click', openMobileSidebar);
        elements.sidebarOverlay.addEventListener('click', closeMobileSidebar);
        elements.newChatBtn.addEventListener('click', createNewChat);
        elements.searchInput.addEventListener('input', debounce(handleSearch, 300));
        elements.themeToggle.addEventListener('click', toggleTheme);
        elements.settingsBtn.addEventListener('click', () => openModal('settingsModal'));
        elements.utilitiesBtn.addEventListener('click', () => openModal('utilitiesModal'));
        elements.exportBtn.addEventListener('click', () => openModal('exportModal'));
        elements.deleteChatBtn.addEventListener('click', deleteCurrentChat);
        elements.messageInput.addEventListener('input', handleInputChange);
        elements.messageInput.addEventListener('keydown', handleInputKeydown);
        elements.sendBtn.addEventListener('click', sendMessage);
        elements.uploadFileBtn.addEventListener('click', () => elements.pdfInput.click());
        elements.uploadImageBtn.addEventListener('click', handleImageUploadClick);
        elements.voiceBtn.addEventListener('click', toggleVoiceRecording);
        elements.emojiBtn.addEventListener('click', toggleEmojiPicker);
        elements.pdfInput.addEventListener('change', handlePdfUpload);
        elements.imageInput.addEventListener('change', handleImageSelect);
        elements.errorClose.addEventListener('click', hideError);
        elements.clearHistoryBtn.addEventListener('click', clearAllHistory);
        elements.temperatureSlider.addEventListener('input', updateTemperatureDisplay);
        elements.suggestedPrompts.addEventListener('click', handleSuggestedPrompt);

        $$('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => closeModal(btn.dataset.close));
        });

        $$('.modal-backdrop').forEach(backdrop => {
            backdrop.addEventListener('click', () => {
                backdrop.closest('.modal').classList.remove('active');
            });
        });

        $$('.theme-option').forEach(btn => {
            btn.addEventListener('click', () => setTheme(btn.dataset.theme));
        });

        $$('.export-option').forEach(btn => {
            btn.addEventListener('click', () => exportChat(btn.dataset.format));
        });

        $$('.utility-card').forEach(btn => {
            btn.addEventListener('click', () => selectUtility(btn.dataset.utility));
        });

        $$('.transform-option').forEach(btn => {
            btn.addEventListener('click', () => applyImageTransform(btn.dataset.style));
        });

        document.addEventListener('click', (e) => {
            if (!elements.emojiPicker.contains(e.target) && e.target !== elements.emojiBtn) {
                elements.emojiPicker.classList.remove('active');
            }
        });
    }

    // =====================================================
    // API Helpers
    // =====================================================
    async function api(url, options = {}) {
        try {
            const response = await fetch(`/api${url}`, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options,
            });

            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || `Request failed (${response.status})`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            }
            return response;
        } catch (error) {
            if (error.message.includes('Failed to fetch')) {
                throw new Error('No internet connection. Please check your network.');
            }
            throw error;
        }
    }

    // =====================================================
    // Settings
    // =====================================================
    async function loadSettings() {
        try {
            const settings = await api('/settings');
            state.settings = { ...state.settings, ...settings };
            applySettings();
        } catch (error) {
            console.warn('Could not load settings:', error.message);
            applySettings();
        }
    }

    function applySettings() {
        document.documentElement.setAttribute('data-theme', state.settings.theme);
        elements.temperatureSlider.value = state.settings.temperature;
        elements.temperatureValue.textContent = state.settings.temperature;
        elements.maxTokensInput.value = state.settings.max_tokens;
        elements.autoScrollCheck.checked = state.settings.auto_scroll === 'true' || state.settings.auto_scroll === true;
        elements.voiceEnabledCheck.checked = state.settings.voice_enabled === 'true' || state.settings.voice_enabled === true;

        $$('.theme-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === state.settings.theme);
        });

        const themeLabel = $('.theme-label');
        if (themeLabel) {
            themeLabel.textContent = state.settings.theme === 'dark' ? 'Dark Mode' : 'Light Mode';
        }
    }

    async function saveSettings() {
        const data = {
            theme: state.settings.theme,
            temperature: parseFloat(elements.temperatureSlider.value),
            max_tokens: parseInt(elements.maxTokensInput.value, 10),
            auto_scroll: elements.autoScrollCheck.checked,
            voice_enabled: elements.voiceEnabledCheck.checked,
        };

        try {
            await api('/settings', { method: 'PUT', body: JSON.stringify(data) });
            state.settings = { ...state.settings, ...data };
            showToast('Settings saved', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    function toggleTheme() {
        const newTheme = state.settings.theme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    }

    function setTheme(theme) {
        state.settings.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        $$('.theme-option').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
        const themeLabel = $('.theme-label');
        if (themeLabel) {
            themeLabel.textContent = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
        }
        saveSettings();
    }

    function updateTemperatureDisplay() {
        elements.temperatureValue.textContent = elements.temperatureSlider.value;
    }

    // =====================================================
    // Chat History
    // =====================================================
    async function loadChatHistory(search = '') {
        try {
            const data = await api(`/history${search ? '?search=' + encodeURIComponent(search) : ''}`);
            renderChatHistory(data.chats);
        } catch (error) {
            showToast('Failed to load chat history', 'error');
        }
    }

    function renderChatHistory(categories) {
        const sections = {
            pinned: { section: $('#pinnedSection'), list: $('#pinnedList') },
            today: { section: $('#todaySection'), list: $('#todayList') },
            yesterday: { section: $('#yesterdaySection'), list: $('#yesterdayList') },
            last_week: { section: $('#weekSection'), list: $('#weekList') },
            older: { section: $('#olderSection'), list: $('#olderList') },
        };

        Object.entries(sections).forEach(([key, { section, list }]) => {
            const chats = categories[key] || [];
            list.innerHTML = '';
            section.style.display = chats.length ? 'block' : 'none';

            chats.forEach(chat => {
                const li = document.createElement('li');
                li.className = 'history-item' + (chat.id === state.currentChatId ? ' active' : '');
                li.dataset.chatId = chat.id;
                li.innerHTML = `
                    ${chat.pinned ? '<span class="pin-icon">📌</span>' : ''}
                    <span>${escapeHtml(chat.title)}</span>
                    <div class="history-item-actions">
                        <button class="history-action-btn pin-btn" title="Pin">📌</button>
                        <button class="history-action-btn rename-btn" title="Rename">✏️</button>
                        <button class="history-action-btn delete-btn" title="Delete">🗑️</button>
                    </div>
                `;

                li.addEventListener('click', (e) => {
                    if (e.target.closest('.history-action-btn')) return;
                    loadChat(chat.id);
                });

                li.querySelector('.pin-btn')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    togglePinChat(chat.id, !chat.pinned);
                });

                li.querySelector('.rename-btn')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    renameChat(chat.id, chat.title);
                });

                li.querySelector('.delete-btn')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteChat(chat.id);
                });

                list.appendChild(li);
            });
        });
    }

    async function createNewChat() {
        try {
            const data = await api('/new-chat', { method: 'POST', body: JSON.stringify({}) });
            state.currentChatId = data.chat_id;
            state.activeUtility = null;
            clearMessages();
            showWelcomeScreen();
            elements.chatTitle.textContent = 'New Chat';
            await loadChatHistory();
            closeMobileSidebar();
            elements.messageInput.focus();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function loadChat(chatId) {
        try {
            showLoading(true);
            const data = await api(`/history/${chatId}`);
            state.currentChatId = chatId;
            state.activeUtility = null;
            hideWelcomeScreen();
            clearMessages();

            elements.chatTitle.textContent = data.chat.title;

            data.messages.forEach(msg => {
                appendMessage(msg.role, msg.content, msg.created_at, false, msg.attachments || []);
            });

            scrollToBottom();
            await loadChatHistory();
            closeMobileSidebar();
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            showLoading(false);
        }
    }

    async function deleteChat(chatId) {
        if (!confirm('Delete this chat?')) return;

        try {
            await api(`/delete-chat/${chatId}`, { method: 'DELETE' });
            if (state.currentChatId === chatId) {
                state.currentChatId = null;
                clearMessages();
                showWelcomeScreen();
                elements.chatTitle.textContent = 'Gemini AI Assistant';
            }
            await loadChatHistory();
            showToast('Chat deleted', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function deleteCurrentChat() {
        if (!state.currentChatId) {
            showToast('No chat selected', 'info');
            return;
        }
        await deleteChat(state.currentChatId);
    }

    async function togglePinChat(chatId, pinned) {
        try {
            await api(`/pin-chat/${chatId}`, {
                method: 'PUT',
                body: JSON.stringify({ pinned }),
            });
            await loadChatHistory();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function renameChat(chatId, currentTitle) {
        const title = prompt('Rename chat:', currentTitle);
        if (!title || title.trim() === currentTitle) return;

        try {
            await api(`/rename-chat/${chatId}`, {
                method: 'PUT',
                body: JSON.stringify({ title: title.trim() }),
            });
            if (state.currentChatId === chatId) {
                elements.chatTitle.textContent = title.trim();
            }
            await loadChatHistory();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function clearAllHistory() {
        if (!confirm('Clear all chat history? This cannot be undone.')) return;

        try {
            await api('/settings/clear-history', { method: 'DELETE' });
            state.currentChatId = null;
            clearMessages();
            showWelcomeScreen();
            elements.chatTitle.textContent = 'Gemini AI Assistant';
            await loadChatHistory();
            closeModal('settingsModal');
            showToast('History cleared', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    function handleSearch() {
        loadChatHistory(elements.searchInput.value.trim());
    }

    // =====================================================
    // Messaging
    // =====================================================
    function handleInputChange() {
        autoResizeTextarea();
        const len = elements.messageInput.value.length;
        elements.charCounter.textContent = `${len} / 32000`;
        elements.sendBtn.disabled = len === 0 || state.isStreaming;
    }

    function handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    function autoResizeTextarea() {
        const textarea = elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    async function sendMessage() {
        const message = elements.messageInput.value.trim();
        if (!message || state.isStreaming) return;

        hideWelcomeScreen();
        appendMessage('user', message);
        elements.messageInput.value = '';
        handleInputChange();
        autoResizeTextarea();

        if (state.activeUtility) {
            await sendUtilityMessage(message);
            return;
        }

        await streamChatResponse(message);
    }

    async function streamChatResponse(message) {
        state.isStreaming = true;
        elements.sendBtn.disabled = true;
        showTypingIndicator(true);

        let assistantMsgEl = null;
        let fullResponse = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    chat_id: state.currentChatId,
                    stream: true,
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to send message');
            }

            showTypingIndicator(false);
            assistantMsgEl = appendMessage('assistant', '', new Date().toISOString(), false);
            const bodyEl = assistantMsgEl.querySelector('.message-body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value, { stream: true });
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data.startsWith('[DONE:')) {
                            state.currentChatId = parseInt(data.match(/\[DONE:(\d+)\]/)?.[1]) || state.currentChatId;
                        } else if (data.startsWith('[ERROR:')) {
                            throw new Error(data.slice(7, -1));
                        } else {
                            fullResponse += data;
                            bodyEl.innerHTML = renderMarkdown(fullResponse);
                            enhanceCodeBlocks(bodyEl);
                            if (state.settings.auto_scroll === 'true' || state.settings.auto_scroll === true) {
                                scrollToBottom();
                            }
                        }
                    }
                }
            }

            if (state.settings.voice_enabled === 'true' || state.settings.voice_enabled === true) {
                speakText(fullResponse);
            }

            await loadChatHistory();
        } catch (error) {
            showTypingIndicator(false);
            if (assistantMsgEl) {
                assistantMsgEl.remove();
            }
            showError(error.message);
        } finally {
            state.isStreaming = false;
            elements.sendBtn.disabled = elements.messageInput.value.trim().length === 0;
        }
    }

    async function sendUtilityMessage(message) {
        state.isStreaming = true;
        showTypingIndicator(true);

        try {
            const data = await api('/chat', {
                method: 'POST',
                body: JSON.stringify({
                    message,
                    chat_id: state.currentChatId,
                    stream: false,
                    utility: state.activeUtility,
                }),
            });

            showTypingIndicator(false);
            state.currentChatId = data.chat_id;
            appendMessage('assistant', data.response);
            await loadChatHistory();
        } catch (error) {
            showTypingIndicator(false);
            showError(error.message);
        } finally {
            state.isStreaming = false;
            elements.sendBtn.disabled = false;
        }
    }

    async function regenerateResponse(messageEl) {
        if (!state.currentChatId || state.isStreaming) return;

        const msgIndex = Array.from(elements.messagesContainer.children).indexOf(messageEl);
        if (msgIndex < 0) return;

        messageEl.remove();
        state.isStreaming = true;
        showTypingIndicator(true);

        let assistantMsgEl = null;
        let fullResponse = '';

        try {
            const response = await fetch('/api/chat/regenerate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: state.currentChatId }),
            });

            showTypingIndicator(false);
            assistantMsgEl = appendMessage('assistant', '', new Date().toISOString(), false);
            const bodyEl = assistantMsgEl.querySelector('.message-body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value, { stream: true });
                for (const line of text.split('\n')) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data.startsWith('[ERROR:')) {
                            throw new Error(data.slice(7, -1));
                        } else if (!data.startsWith('[DONE:')) {
                            fullResponse += data;
                            bodyEl.innerHTML = renderMarkdown(fullResponse);
                            enhanceCodeBlocks(bodyEl);
                            scrollToBottom();
                        }
                    }
                }
            }

            await loadChatHistory();
        } catch (error) {
            showTypingIndicator(false);
            if (assistantMsgEl) assistantMsgEl.remove();
            showError(error.message);
        } finally {
            state.isStreaming = false;
        }
    }

    function appendMessage(role, content, timestamp, animate = true, attachments = []) {
        const msgEl = document.createElement('div');
        msgEl.className = `message ${role}`;
        if (!animate) msgEl.style.animation = 'none';

        const time = timestamp
            ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const avatar = role === 'user' ? 'U' : '✦';
        const roleName = role === 'user' ? 'You' : 'Gemini';
        const attachmentsHtml = renderAttachments(attachments);

        msgEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-role">${roleName}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-body">${role === 'assistant' ? renderMarkdown(content) : escapeHtml(content)}</div>
                ${attachmentsHtml}
                <div class="message-actions">
                    ${role === 'assistant' ? `
                        <button class="msg-action-btn copy-btn">📋 Copy</button>
                        <button class="msg-action-btn regen-btn">🔄 Regenerate</button>
                    ` : `
                        <button class="msg-action-btn edit-btn">✏️ Edit</button>
                    `}
                </div>
            </div>
        `;

        if (role === 'assistant') {
            enhanceCodeBlocks(msgEl.querySelector('.message-body'));
            msgEl.querySelector('.copy-btn')?.addEventListener('click', () => {
                copyToClipboard(content || msgEl.querySelector('.message-body').textContent);
            });
            msgEl.querySelector('.regen-btn')?.addEventListener('click', () => {
                regenerateResponse(msgEl);
            });
        } else {
            msgEl.querySelector('.edit-btn')?.addEventListener('click', () => {
                elements.messageInput.value = content;
                handleInputChange();
                elements.messageInput.focus();
            });
        }

        elements.messagesContainer.appendChild(msgEl);
        scrollToBottom();
        return msgEl;
    }

    function renderAttachments(attachments) {
        if (!attachments || !attachments.length) return '';

        return `
            <div class="message-attachments">
                ${attachments.map(att => {
                    if (att.type === 'image' && att.filename) {
                        const url = escapeHtml(att.url || `/uploads/${att.filename}`);
                        return `<img src="${url}" alt="${escapeHtml(att.filename)}" class="message-attachment" />`;
                    }
                    const href = escapeHtml(att.url || '#');
                    const label = escapeHtml(att.filename || 'Attachment');
                    return `<div class="message-attachment-link"><a href="${href}" target="_blank" rel="noopener noreferrer">${label}</a></div>`;
                }).join('')}
            </div>
        `;
    }

    function clearMessages() {
        elements.messagesContainer.innerHTML = '';
    }

    function showWelcomeScreen() {
        elements.welcomeScreen.style.display = 'flex';
    }

    function hideWelcomeScreen() {
        elements.welcomeScreen.style.display = 'none';
    }

    function showTypingIndicator(show) {
        elements.typingIndicator.classList.toggle('active', show);
        if (show) scrollToBottom();
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
        });
    }

    function handleSuggestedPrompt(e) {
        const card = e.target.closest('.prompt-card');
        if (!card) return;
        elements.messageInput.value = card.dataset.prompt;
        handleInputChange();
        sendMessage();
    }

    // =====================================================
    // Markdown Rendering
    // =====================================================
    function renderMarkdown(text) {
        if (!text) return '';
        try {
            if (typeof marked !== 'undefined') {
                return marked.parse(text);
            }
            return escapeHtml(text).replace(/\n/g, '<br>');
        } catch {
            return escapeHtml(text);
        }
    }

    function enhanceCodeBlocks(container) {
        container.querySelectorAll('pre code').forEach(block => {
            if (typeof hljs !== 'undefined') {
                hljs.highlightElement(block);
            }

            const pre = block.parentElement;
            if (pre.parentElement?.classList.contains('code-block-wrapper')) return;

            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);

            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-code-btn';
            copyBtn.textContent = 'Copy';
            copyBtn.addEventListener('click', () => copyToClipboard(block.textContent));
            wrapper.appendChild(copyBtn);
        });
    }

    // =====================================================
    // File Uploads
    // =====================================================
    async function handlePdfUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        e.target.value = '';

        if (file.size > 10 * 1024 * 1024) {
            showError('PDF too large. Maximum size is 10 MB.');
            return;
        }

        showLoading(true);
        hideWelcomeScreen();

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (state.currentChatId) formData.append('chat_id', state.currentChatId);

            const response = await fetch('/api/upload-pdf', { method: 'POST', body: formData });
            const data = await response.json();

            if (!response.ok) throw new Error(data.error);

            state.currentChatId = data.chat_id;
            appendMessage('user', `📄 Uploaded PDF: ${data.filename}`);
            appendMessage('assistant', data.message);
            elements.chatTitle.textContent = `PDF: ${data.filename.substring(0, 30)}`;
            await loadChatHistory();
            showToast('PDF uploaded successfully', 'success');
        } catch (error) {
            showError(error.message);
        } finally {
            showLoading(false);
        }
    }

    function handleImageUploadClick() {
        const choice = confirm('Choose image action:\n\nOK = Analyze Image\nCancel = Transform Image');
        state.imageMode = choice ? 'analyze' : 'transform';
        elements.imageInput.click();
    }

    function handleImageSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        e.target.value = '';

        if (file.size > 5 * 1024 * 1024) {
            showError('Image too large. Maximum size is 5 MB.');
            return;
        }

        state.pendingImageFile = file;

        if (state.imageMode === 'transform') {
            openModal('imageTransformModal');
        } else {
            uploadAndAnalyzeImage(file);
        }
    }

    async function uploadAndAnalyzeImage(file, style = '', customPrompt = '') {
        showLoading(true);
        hideWelcomeScreen();

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('mode', state.imageMode);
            formData.append('prompt', customPrompt || elements.messageInput.value.trim() || 'Describe this image in detail.');
            if (style) formData.append('style', style);
            if (state.currentChatId) formData.append('chat_id', state.currentChatId);

            const response = await fetch('/api/upload-image', { method: 'POST', body: formData });
            const data = await response.json();

            if (!response.ok) throw new Error(data.error);

            state.currentChatId = data.chat_id;
            appendMessage('user', `🖼️ Image uploaded${style ? ` (${style})` : ''}`);
            appendMessage('assistant', data.response);
            elements.chatTitle.textContent = 'Image Chat';
            await loadChatHistory();
            showToast('Image processed successfully', 'success');
        } catch (error) {
            showError(error.message);
        } finally {
            showLoading(false);
            state.pendingImageFile = null;
            closeModal('imageTransformModal');
        }
    }

    function applyImageTransform(style) {
        if (!state.pendingImageFile) return;
        const customPrompt = elements.transformPrompt.value.trim();
        uploadAndAnalyzeImage(state.pendingImageFile, style, customPrompt);
    }

    // =====================================================
    // Voice
    // =====================================================
    let recognition = null;

    function toggleVoiceRecording() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            showToast('Speech recognition not supported in this browser', 'error');
            return;
        }

        if (state.isRecording) {
            stopRecording();
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            state.isRecording = true;
            elements.voiceBtn.classList.add('recording');
            showToast('Listening...', 'info');
        };

        recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            elements.messageInput.value = transcript;
            handleInputChange();

            if (event.results[event.results.length - 1].isFinal) {
                stopRecording();
                sendMessage();
            }
        };

        recognition.onerror = (event) => {
            stopRecording();
            showToast(`Voice error: ${event.error}`, 'error');
        };

        recognition.onend = () => {
            stopRecording();
        };

        recognition.start();
    }

    function stopRecording() {
        state.isRecording = false;
        elements.voiceBtn.classList.remove('recording');
        if (recognition) {
            try { recognition.stop(); } catch {}
        }
    }

    function speakText(text) {
        if (!('speechSynthesis' in window)) return;
        const utterance = new SpeechSynthesisUtterance(text.substring(0, 500));
        utterance.rate = 1;
        utterance.pitch = 1;
        speechSynthesis.speak(utterance);
    }

    // =====================================================
    // Utilities
    // =====================================================
    function selectUtility(utility) {
        state.activeUtility = utility;
        closeModal('utilitiesModal');

        const names = {
            grammar: 'Grammar Checker',
            resume: 'Resume Analyzer',
            cover_letter: 'Cover Letter Generator',
            email: 'Email Generator',
            blog: 'Blog Writer',
            code: 'Code Generator',
            sql: 'SQL Generator',
            regex: 'Regex Generator',
            json: 'JSON Formatter',
            translate: 'Translator',
            summarize: 'Summarizer',
        };

        showToast(`${names[utility] || utility} mode activated`, 'info');
        elements.messageInput.placeholder = `Enter text for ${names[utility] || utility}...`;
        elements.messageInput.focus();
    }

    // =====================================================
    // Export
    // =====================================================
    async function exportChat(format) {
        if (!state.currentChatId) {
            showToast('No chat to export', 'info');
            return;
        }

        closeModal('exportModal');
        window.open(`/api/export/${state.currentChatId}?format=${format}`, '_blank');
        showToast(`Exporting as ${format.toUpperCase()}...`, 'success');
    }

    // =====================================================
    // Emoji Picker
    // =====================================================
    const EMOJIS = [
        '😀','😃','😄','😁','😅','😂','🤣','😊',
        '😇','🙂','😉','😌','😍','🥰','😘','😗',
        '😋','😛','😜','🤪','😎','🤩','🥳','😏',
        '😒','😞','😔','😟','😕','🙁','😣','😖',
        '😫','😩','🥺','😢','😭','😤','😠','😡',
        '🤔','🤨','😐','😑','😶','🙄','😯','😦',
        '👍','👎','👏','🙌','🤝','💪','✌️','🤞',
        '❤️','🧡','💛','💚','💙','💜','🖤','💯',
        '⭐','🌟','✨','🔥','💡','📌','🎉','🎊',
    ];

    function initEmojiPicker() {
        elements.emojiGrid.innerHTML = EMOJIS.map(emoji =>
            `<button class="emoji-item" type="button">${emoji}</button>`
        ).join('');

        elements.emojiGrid.addEventListener('click', (e) => {
            if (e.target.classList.contains('emoji-item')) {
                elements.messageInput.value += e.target.textContent;
                handleInputChange();
                elements.messageInput.focus();
            }
        });
    }

    function toggleEmojiPicker() {
        elements.emojiPicker.classList.toggle('active');
    }

    // =====================================================
    // UI Helpers
    // =====================================================
    function toggleSidebarCollapse() {
        elements.sidebar.classList.toggle('collapsed');
    }

    function openMobileSidebar() {
        elements.sidebar.classList.add('open');
        elements.sidebarOverlay.classList.add('active');
    }

    function closeMobileSidebar() {
        elements.sidebar.classList.remove('open');
        elements.sidebarOverlay.classList.remove('active');
    }

    function openModal(id) {
        $(`#${id}`).classList.add('active');
    }

    function closeModal(id) {
        $(`#${id}`).classList.remove('active');
        if (id === 'settingsModal') saveSettings();
    }

    function showLoading(show) {
        elements.loadingOverlay.classList.toggle('active', show);
    }

    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorBanner.classList.add('active');
        setTimeout(hideError, 8000);
    }

    function hideError() {
        elements.errorBanner.classList.remove('active');
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard', 'success');
        }).catch(() => {
            showToast('Failed to copy', 'error');
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function debounce(fn, delay) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    }
})();
