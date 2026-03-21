// =============================================================================
// DISCORD CLONE - CHAT.JS
// Модуль чата и WebSocket
// =============================================================================
import {
    escapeHtml,
    showNotification,
    formatFileSize,
    openImageModal,
    getToken
} from './utils.js';
import { getCurrentUser, getAuthToken } from './auth.js';

let ws = null;
let currentChannel = 'общий-чат';
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;
let reconnectTimer = null;

/**
 * Подключение к чату
 */
export function connectToChat() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }

    const currentUser = getCurrentUser();
    const authToken = getAuthToken();

    if (!currentUser || !authToken) {
        console.error('No user or token for WebSocket connection');
        return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    ws = new WebSocket(
        `${protocol}//${window.location.host}/ws/${encodeURIComponent(currentChannel)}/${encodeURIComponent(currentUser.nickname)}/${authToken}`
    );

    ws.onopen = () => {
        reconnectAttempts = 0;
        updateStatus(true);
        addSystemMessage(`✓ Вы подключились как ${currentUser.nickname}`);
    };

    ws.onmessage = (event) => {
        console.log('📩 Получено сообщение:', event.data);
        const data = JSON.parse(event.data);
        console.log('📦 Распарсенный тип:', data.type);

        if (data.type === 'system') {
            addSystemMessage(data.content);
        }
        else if (data.type === 'message_history') {
            document.getElementById('messages').innerHTML = '';
            if (data.messages && Array.isArray(data.messages)) {
                data.messages.forEach(msg => {
                    addMessage(
                        msg.nickname,
                        msg.content,
                        msg.time,
                        true,
                        msg.status || 'sent',
                        msg.id,
                        msg.sender_id,
                        msg.attachments || []
                    );
                });
            }
        }
        else if (data.type === 'message') {
            addMessage(
                data.nickname,
                data.content,
                data.time,
                false,
                data.status || 'sent',
                data.id,
                data.sender_id,
                data.attachments || []
            );

            if (currentUser && data.nickname !== currentUser.nickname) {
                setTimeout(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'message_delivered',
                            message_ids: [data.id],
                            sender_nickname: data.nickname
                        }));
                    }
                }, 500);

                setTimeout(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: 'message_read',
                            message_ids: [data.id],
                            sender_nickname: data.nickname
                        }));
                    }
                }, 2000);
            }
        }
        else if (data.type === 'message_status_update') {
            updateMessageStatus(data.message_id, data.status);
        }
        else if (data.type === 'online_users') {
            updateOnlineUsers(data.users);
        }
        else if (data.type === 'channel_switched') {
            currentChannel = data.channel;
            document.getElementById('chat-header').innerText = '# ' + currentChannel;
            addSystemMessage(`✓ Вы перешли в #${currentChannel}`);
        }
    };

    ws.onclose = (event) => {
        updateStatus(false);

        if (event.code === 4003) {
            addSystemMessage("✗ Ошибка авторизации. Требуется повторный вход.");
            setTimeout(() => {
                if (window.logout) window.logout();
            }, 2000);
            return;
        }

        reconnectAttempts++;
        if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) {
            addSystemMessage(`✗ Соединение разорвано. Попытка ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}...`);
            reconnectTimer = setTimeout(() => connectToChat(), 5000);
        } else {
            addSystemMessage("✗ Превышено количество попыток подключения. Перезайдите в аккаунт.");
            setTimeout(() => {
                if (window.logout) window.logout();
            }, 3000);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

/**
 * Отправка сообщения
 */
export function sendMessage() {
    sendMessageInternal(false);
}

/**
 * Отправка сообщения с вложениями
 */
export function sendMessageWithAttachments() {
    sendMessageInternal(true);
}

/**
 * Внутренняя функция отправки
 */
function sendMessageInternal(withAttachments = false) {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    const hasAttachments = window.pendingFiles && window.pendingFiles.length > 0;

    if (!text && !hasAttachments) {
        showNotification('Введите сообщение или выберите файл', 'error');
        return;
    }

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        showNotification('Нет соединения с сервером', 'error');
        return;
    }

    const messageData = {
        type: 'message',
        content: text,
        attachments: hasAttachments ? [...window.pendingFiles] : []
    };

    console.log('📤 Отправка сообщения:', messageData);
    ws.send(JSON.stringify(messageData));

    // Очистка полей
    input.value = '';
    autoResizeTextarea();

    if (window.pendingFiles) {
        window.pendingFiles = [];
    }

    const filePreviewList = document.getElementById('file-preview-list');
    const filePreviewContainer = document.getElementById('file-preview-container');

    if (filePreviewList) filePreviewList.innerHTML = '';
    if (filePreviewContainer) filePreviewContainer.style.display = 'none';

    const fileInput = document.getElementById('file-input');
    if (fileInput) fileInput.value = '';
}

/**
 * Авто-ресайз textarea
 */
function autoResizeTextarea() {
    const textarea = document.getElementById('message-input');
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

/**
 * Добавление сообщения
 */
function addMessage(user, text, time, isHistory, status = 'sent', messageId = null, senderId = null, attachments = []) {
    const currentUser = getCurrentUser();
    const div = document.createElement('div');
    const isOwnMessage = currentUser && user === currentUser.nickname;

    div.className = 'message' + (isHistory ? ' message-history' : '') + (isOwnMessage ? ' own' : ' other');

    if (messageId) {
        div.dataset.messageId = messageId;
    }

    const initial = user.charAt(0).toUpperCase();
    let dateStr;

    if (time) {
        const msgDate = new Date(time + 'Z');
        const now = new Date();
        const msgDateOnly = new Date(msgDate.getFullYear(), msgDate.getMonth(), msgDate.getDate());
        const todayOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const timeOptions = { hour: '2-digit', minute: '2-digit', hour12: false };

        if (msgDateOnly.getTime() === todayOnly.getTime()) {
            dateStr = msgDate.toLocaleTimeString('ru-RU', timeOptions);
        } else {
            const dateOptions = { day: 'numeric', month: 'short' };
            dateStr = `${msgDate.toLocaleDateString('ru-RU', dateOptions)} ${msgDate.toLocaleTimeString('ru-RU', timeOptions)}`;
        }
    } else {
        const now = new Date();
        dateStr = now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', hour12: false });
    }

    // Вложения
    let attachmentsHtml = '';
    if (attachments && attachments.length > 0) {
        attachmentsHtml = '<div class="message-attachments">';
        attachments.forEach(att => {
            if (att.file_type && att.file_type.startsWith('image/')) {
                attachmentsHtml += `<div class="attachment-item"><img src="${att.file_url}" alt="${att.file_name}" onclick="openImageModal('${att.file_url}')"></div>`;
            } else if (att.file_type && att.file_type.startsWith('video/')) {
                attachmentsHtml += `<div class="attachment-item"><video src="${att.file_url}" controls></video></div>`;
            } else {
                attachmentsHtml += `
                    <div class="attachment-item">
                        <div class="file-download">
                            <span class="file-icon">📄</span>
                            <div>
                                <div>${att.file_name}</div>
                                <div>${formatFileSize(att.file_size)}</div>
                            </div>
                            <a href="${att.file_url}" download>⬇️</a>
                        </div>
                    </div>
                `;
            }
        });
        attachmentsHtml += '</div>';
    }

    if (isOwnMessage) {
        let checkIcon = '✓';
        let checkClass = 'sent';

        if (status === 'delivered') {
            checkIcon = '✓✓';
            checkClass = 'delivered';
        } else if (status === 'read') {
            checkIcon = '✓✓';
            checkClass = 'read';
        }

        div.innerHTML = `
            <div class="message-bubble">
                <p>${escapeHtml(text)}</p>
                ${attachmentsHtml}
                <div class="message-time">
                    ${dateStr}
                    <span class="message-check ${checkClass}">${checkIcon}</span>
                </div>
            </div>
        `;
    } else {
        div.innerHTML = `
            <div class="avatar">${initial}</div>
            <div class="message-bubble">
                <span class="message-username">${escapeHtml(user)}</span>
                <p>${escapeHtml(text)}</p>
                ${attachmentsHtml}
                <div class="message-time">${dateStr}</div>
            </div>
        `;
    }

    const container = document.getElementById('messages');
    if (container) {
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
}

/**
 * Добавление системного сообщения
 */
export function addSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'system-message';
    div.innerText = text;

    const container = document.getElementById('messages');
    if (container) {
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }
}

/**
 * Обновление статуса подключения
 */
function updateStatus(connected) {
    const status = document.getElementById('connection-status');
    if (status) {
        status.className = 'connection-status ' + (connected ? 'status-connected' : 'status-disconnected');
        status.innerText = connected ? 'Подключено' : 'Отключено';
    }
}

/**
 * Обновление списка онлайн пользователей
 */
function updateOnlineUsers(users) {
    const list = document.getElementById('user-list');
    const count = document.getElementById('online-count');

    if (list && count) {
        list.innerHTML = '';
        count.innerText = users.length;

        users.forEach(user => {
            const div = document.createElement('div');
            div.className = 'user-item';
            div.innerHTML = `<div class="user-status"></div>${escapeHtml(user)}`;
            list.appendChild(div);
        });
    }
}

/**
 * Обновление статуса сообщения
 */
function updateMessageStatus(messageId, status) {
    const msgElement = document.querySelector(`[data-message-id="${messageId}"]`);

    if (msgElement) {
        const check = msgElement.querySelector('.message-check');
        if (check) {
            if (status === 'delivered') {
                check.textContent = '✓✓';
                check.classList.remove('sent', 'read');
                check.classList.add('delivered');
            } else if (status === 'read') {
                check.textContent = '✓✓';
                check.classList.remove('sent', 'delivered');
                check.classList.add('read');
            }
        }
    }
}

// Экспорт для глобального доступа
window.connectToChat = connectToChat;
window.sendMessage = sendMessage;
window.sendMessageWithAttachments = sendMessageWithAttachments;
window.addSystemMessage = addSystemMessage;
window.autoResizeTextarea = autoResizeTextarea;
