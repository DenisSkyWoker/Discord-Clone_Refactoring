// =============================================================================
// DISCORD CLONE - CHANNELS.JS
// Модуль управления каналами
// =============================================================================

import {
    secureFetch,
    showNotification,
    showError,
    escapeHtml
} from './utils.js';
import { getCurrentUser } from './auth.js';

let protectedChannelsJoined = new Set();
let pendingChannel = null;

/**
 * Загрузка списка каналов
 */
export async function loadChannels() {
    try {
        const response = await secureFetch('/api/channels');
        const data = await response.json();

        const channelList = document.getElementById('channel-list');
        if (!channelList) return;

        channelList.innerHTML = '';

        const currentUser = getCurrentUser();

        data.channels.forEach((channel) => {
            const div = document.createElement('div');
            div.className = 'channel-item' + (channel.is_default ? '' : ' private');

            const currentChannel = window.currentChannel || 'общий-чат';
            if (channel.name === currentChannel) {
                div.classList.add('active');
            }

            const icon = channel.has_password ? '🔒' : '#';

            let deleteBtn = '';
            if (!channel.is_default && channel.creator_id === currentUser?.user_id) {
                deleteBtn = `<button class="channel-delete-btn" onclick="deleteChannel(${channel.id}, '${channel.name}')" title="Удалить канал">🗑️</button>`;
            }

            div.innerHTML = `
                <span style="flex: 1;" onclick="switchChannel('${channel.name}', ${channel.has_password})">
                    ${icon} ${escapeHtml(channel.name)}
                </span>
                ${deleteBtn}
            `;

            channelList.appendChild(div);
        });

    } catch (error) {
        console.error('Ошибка загрузки каналов:', error);
        showNotification('Не удалось загрузить каналы', 'error');
    }
}

/**
 * Переключение канала
 */
export async function switchChannel(channelName, hasPassword) {
    if (hasPassword && !protectedChannelsJoined.has(channelName)) {
        showChannelPasswordModal(channelName);
        return;
    }

    const ws = window.ws;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'switch_channel',
            channel: channelName
        }));

        window.currentChannel = channelName;

        const chatHeader = document.getElementById('chat-header');
        if (chatHeader) {
            chatHeader.innerText = '# ' + channelName;
        }

        document.querySelectorAll('.channel-item').forEach(item => {
            item.classList.remove('active');
            if (item.textContent.includes(channelName)) {
                item.classList.add('active');
            }
        });
    }
}

/**
 * Показать модальное окно создания канала
 */
export function showCreateChannelModal() {
    const modal = document.getElementById('create-channel-modal');
    const nameInput = document.getElementById('channel-name-input');
    const passwordInput = document.getElementById('channel-password-input');
    const errorEl = document.getElementById('create-channel-error');

    if (modal) modal.style.display = 'flex';
    if (nameInput) nameInput.value = '';
    if (passwordInput) passwordInput.value = '';
    if (errorEl) errorEl.style.display = 'none';
}

/**
 * Закрыть модальное окно создания канала
 */
export function closeCreateChannelModal() {
    const modal = document.getElementById('create-channel-modal');
    if (modal) modal.style.display = 'none';
}

/**
 * Создание нового канала
 */
export async function createChannel() {
    const nameInput = document.getElementById('channel-name-input');
    const passwordInput = document.getElementById('channel-password-input');
    const channelName = nameInput?.value.trim() || '';
    const channelPassword = passwordInput?.value.trim() || '';

    // Валидация
    if (!channelName || channelName.length < 3 || channelName.length > 25) {
        showError('create-channel', 'Название канала должно быть от 3 до 25 символов');
        return;
    }

    if (!/[a-zA-Zа-яА-Я]/.test(channelName)) {
        showError('create-channel', 'Название должно содержать хотя бы одну букву');
        return;
    }

    if (!/^[a-zA-Zа-яА-Я0-9_-]+$/.test(channelName)) {
        showError('create-channel', 'Только буквы, цифры, дефис и подчёркивание');
        return;
    }

    if (/^[0-9_-]/.test(channelName)) {
        showError('create-channel', 'Название должно начинаться с буквы');
        return;
    }

    const reservedNames = ['общий-чат', 'флудилка', 'мемы', 'администраторы', 'admin', 'mod'];
    if (reservedNames.includes(channelName.toLowerCase())) {
        showError('create-channel', 'Это название зарезервировано');
        return;
    }

    try {
        const response = await secureFetch('/api/channels/create', {
            method: 'POST',
            body: JSON.stringify({
                name: channelName,
                password: channelPassword || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(`Канал #${channelName} создан`, 'success');
            closeCreateChannelModal();
            await loadChannels();
        } else {
            showError('create-channel', data.detail || 'Ошибка создания канала');
        }
    } catch (error) {
        showError('create-channel', 'Ошибка соединения с сервером');
        console.error(error);
    }
}

/**
 * Удаление канала
 */
export async function deleteChannel(channelId, channelName) {
    if (!confirm(`Вы уверены что хотите удалить канал "#${channelName}"?\nЭто действие необратимо!`)) {
        return;
    }

    try {
        const response = await secureFetch(`/api/channels/${channelId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(`Канал #${channelName} удалён`, 'success');

            const currentChannel = window.currentChannel || 'общий-чат';
            if (currentChannel === channelName) {
                await switchChannel('общий-чат', false);
            }

            await loadChannels();
        } else {
            showNotification(data.detail || 'Ошибка удаления канала', 'error');
        }
    } catch (error) {
        console.error('Ошибка удаления канала:', error);
        showNotification('Ошибка соединения с сервером', 'error');
    }
}

/**
 * Показать модальное окно пароля канала
 */
export function showChannelPasswordModal(channelName) {
    pendingChannel = channelName;

    const prompt = document.getElementById('channel-password-prompt');
    const modal = document.getElementById('channel-password-modal');
    const passwordInput = document.getElementById('join-channel-password-input');
    const errorEl = document.getElementById('channel-password-error');

    if (prompt) prompt.innerText = `Введите пароль для #${channelName}`;
    if (modal) modal.style.display = 'flex';
    if (passwordInput) passwordInput.value = '';
    if (errorEl) errorEl.style.display = 'none';
}

/**
 * Закрыть модальное окно пароля канала
 */
export function closeChannelPasswordModal() {
    const modal = document.getElementById('channel-password-modal');
    if (modal) modal.style.display = 'none';
    pendingChannel = null;
}

/**
 * Вход в защищённый канал
 */
export async function joinProtectedChannel() {
    const passwordInput = document.getElementById('join-channel-password-input');
    const password = passwordInput?.value || '';

    if (!password) {
        showError('channel-password', 'Введите пароль');
        return;
    }

    const channelName = pendingChannel;

    try {
        const response = await secureFetch('/api/channels/join', {
            method: 'POST',
            body: JSON.stringify({ name: channelName, password })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(`Вход в #${channelName} успешен!`, 'success');
            closeChannelPasswordModal();
            protectedChannelsJoined.add(channelName);
            window.currentChannel = channelName;

            // Переподключение к WebSocket
            const ws = window.ws;
            if (ws) {
                ws.onclose = null;
                ws.close();
                window.ws = null;
            }

            await new Promise(resolve => setTimeout(resolve, 300));

            if (window.connectToChat) {
                window.connectToChat();
            }

            document.querySelectorAll('.channel-item').forEach(i => {
                i.classList.remove('active');
            });

            const chatHeader = document.getElementById('chat-header');
            if (chatHeader) {
                chatHeader.innerText = '# ' + channelName;
            }

            const messages = document.getElementById('messages');
            if (messages) {
                messages.innerHTML = '';
            }

            if (window.addSystemMessage) {
                window.addSystemMessage(`Переход в #${channelName}...`);
            }
        } else {
            showError('channel-password', data.detail || 'Неверный пароль');
        }
    } catch (error) {
        showError('channel-password', 'Ошибка соединения');
        console.error(error);
    }
}

// Экспорт для глобального доступа
window.loadChannels = loadChannels;
window.switchChannel = switchChannel;
window.showCreateChannelModal = showCreateChannelModal;
window.closeCreateChannelModal = closeCreateChannelModal;
window.createChannel = createChannel;
window.deleteChannel = deleteChannel;
window.showChannelPasswordModal = showChannelPasswordModal;
window.closeChannelPasswordModal = closeChannelPasswordModal;
window.joinProtectedChannel = joinProtectedChannel;