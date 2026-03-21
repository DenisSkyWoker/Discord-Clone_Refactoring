// =============================================================================
// DISCORD CLONE - AUTH.JS
// Модуль авторизации и регистрации
// =============================================================================

import {
    secureFetch,
    storeToken,
    showNotification,
    showError,
    clearErrors,
    checkPasswordStrength,
    validateNicknameLength
} from './utils.js';

let currentUser = null;
let authToken = null;

/**
 * Регистрация пользователя
 */
export async function register() {
    clearErrors();

    const nickname = document.getElementById('reg-nickname').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const btn = document.getElementById('register-btn');

    // Валидация
    if (!nickname || nickname.length < 3 || nickname.length > 25) {
        showError('register', 'Никнейм должен быть от 3 до 25 символов');
        return;
    }

    if (!/^[a-zA-Zа-яА-Я0-9_]+$/.test(nickname)) {
        showError('register', 'Никнейм может содержать только буквы, цифры и подчёркивание');
        return;
    }

    if (!password || password.length < 8) {
        showError('register', 'Пароль должен быть не менее 8 символов');
        return;
    }

    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
        showError('register', 'Пароль должен содержать заглавные, строчные буквы и цифры');
        return;
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showError('register', 'Введите корректный Email адрес');
        return;
    }

    btn.disabled = true;
    btn.innerText = 'Регистрация...';

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nickname, password, email })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = {
                nickname: data.nickname,
                user_id: data.user_id,
                email_verified: data.email_verified
            };

            storeToken(authToken);
            showApp();

            // Подключение к чату будет вызвано из app.js
            if (window.connectToChat) window.connectToChat();
            if (window.loadChannels) window.loadChannels();

            if (!data.email_verified && email) {
                if (window.showVerifyModal) window.showVerifyModal();
            }

            showNotification('Регистрация успешна!', 'success');
        } else {
            const errorMessage = typeof data === 'object'
                ? (data.detail || data.message || 'Ошибка регистрации')
                : String(data);
            showError('register', errorMessage);
            showNotification(errorMessage, 'error');
        }
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Ошибка соединения с сервером';
        showError('register', errorMessage);
        showNotification(errorMessage, 'error');
        console.error('Register error:', error);
    } finally {
        btn.disabled = false;
        btn.innerText = 'Зарегистрироваться';
    }
}

/**
 * Вход пользователя
 */
export async function login() {
    clearErrors();

    const nickname = document.getElementById('login-nickname').value.trim();
    const password = document.getElementById('login-password').value;
    const btn = document.getElementById('login-btn');

    if (!nickname || !password) {
        showError('login', 'Введите никнейм и пароль');
        return;
    }

    btn.disabled = true;
    btn.innerText = 'Вход...';

    try {
        const formData = new URLSearchParams();
        formData.append('username', nickname);
        formData.append('password', password);

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = {
                nickname: data.nickname,
                user_id: data.user_id,
                email_verified: data.email_verified
            };

            storeToken(authToken);
            showApp();

            if (window.connectToChat) window.connectToChat();
            if (window.loadChannels) window.loadChannels();

            showNotification('Вход выполнен!', 'success');
        } else if (response.status === 423) {
            showError('login', data.detail || 'Аккаунт заблокирован');
            showNotification('Аккаунт заблокирован', 'error');
        } else {
            showError('login', data.detail || 'Неверный логин или пароль');
            showNotification('Неверный логин или пароль', 'error');
        }
    } catch (error) {
        showError('login', 'Ошибка соединения с сервером');
        showNotification('Ошибка соединения', 'error');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.innerText = 'Войти';
    }
}

/**
 * Выход пользователя
 */
export async function logout() {
    if (window.reconnectTimer) {
        clearTimeout(window.reconnectTimer);
        window.reconnectTimer = null;
    }

    window.reconnectAttempts = 0;

    if (window.protectedChannelsJoined) {
        window.protectedChannelsJoined.clear();
    }

    if (authToken) {
        try {
            await secureFetch('/api/auth/logout', { method: 'POST' });
        } catch (e) {
            console.error('Logout error:', e);
        }
    }

    if (window.ws) {
        window.ws.close();
        window.ws = null;
    }

    authToken = null;
    currentUser = null;

    // Очистка токена из utils
    if (window.clearToken) window.clearToken();

    // Скрытие экранов
    document.getElementById('app-screen').style.display = 'none';
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('email-verify-modal').style.display = 'none';
    document.getElementById('create-channel-modal').style.display = 'none';
    document.getElementById('channel-password-modal').style.display = 'none';
    document.getElementById('profile-modal').style.display = 'none';
    document.getElementById('delete-account-modal').style.display = 'none';

    clearErrors();
    showNotification('Выход выполнен', 'success');
}

/**
 * Показ основного приложения
 */
export function showApp() {
    if (!currentUser) return;

    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('app-screen').style.display = 'flex';

    document.getElementById('user-name').innerText = currentUser.nickname;
    document.getElementById('user-name').title = currentUser.nickname;
    document.getElementById('user-avatar').innerText = currentUser.nickname.charAt(0).toUpperCase();
}

/**
 * Проверка сохранённого токена
 */
export async function checkStoredToken() {
    const storedToken = getToken();

    if (storedToken) {
        try {
            const response = await secureFetch('/api/auth/me');
            const data = await response.json();

            authToken = storedToken;
            currentUser = {
                nickname: data.nickname,
                user_id: data.user_id,
                email_verified: data.email_verified
            };

            showApp();

            if (window.connectToChat) window.connectToChat();
            if (window.loadChannels) window.loadChannels();
        } catch (error) {
            console.log('Token invalid, showing login');
            if (window.clearToken) window.clearToken();
        }
    }
}

/**
 * Получение текущего пользователя
 */
export function getCurrentUser() {
    return currentUser;
}

/**
 * Получение токена авторизации
 */
export function getAuthToken() {
    return authToken;
}

// Экспорт для глобального доступа
window.register = register;
window.login = login;
window.logout = logout;
window.getCurrentUser = getCurrentUser;
window.getAuthToken = getAuthToken;