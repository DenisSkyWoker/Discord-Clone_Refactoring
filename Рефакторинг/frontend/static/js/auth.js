// =============================================================================
// DISCORD CLONE - AUTH.JS
// Модуль авторизации и регистрации
// =============================================================================

import {
    getToken,
    storeToken,
    clearToken,
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

    const nickname = document.getElementById('reg-nickname')?.value.trim() || '';
    const email = document.getElementById('reg-email')?.value.trim() || '';
    const password = document.getElementById('reg-password')?.value || '';
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

    const nickname = document.getElementById('login-nickname')?.value.trim() || '';
    const password = document.getElementById('login-password')?.value || '';
    const btn = document.getElementById('login-btn');

    if (!nickname || !password) {
        showError('login', 'Введите никнейм и пароль');
        return;
    }

    btn.disabled = true;
    btn.innerText = 'Вход...';

    try {
        // OAuth2 требует form-data с полями username/password
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
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });
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
    clearToken();

    // Скрытие экранов
    const appScreen = document.getElementById('app-screen');
    const authScreen = document.getElementById('auth-screen');
    if (appScreen) appScreen.style.display = 'none';
    if (authScreen) authScreen.style.display = 'flex';

    // Закрытие модальных окон
    ['email-verify-modal', 'create-channel-modal', 'channel-password-modal',
        'profile-modal', 'delete-account-modal'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    clearErrors();
    showNotification('Выход выполнен', 'success');
}

/**
 * Показать основное приложение
 */
export function showApp() {
    if (!currentUser) return;

    const authScreen = document.getElementById('auth-screen');
    const appScreen = document.getElementById('app-screen');

    if (authScreen) authScreen.style.display = 'none';
    if (appScreen) appScreen.style.display = 'flex';

    const userName = document.getElementById('user-name');
    const userAvatar = document.getElementById('user-avatar');

    if (userName) {
        userName.innerText = currentUser.nickname;
        userName.title = currentUser.nickname;
    }
    if (userAvatar) {
        userAvatar.innerText = currentUser.nickname.charAt(0).toUpperCase();
    }
}

/**
 * Проверка сохранённого токена
 */
export async function checkStoredToken() {
    const storedToken = getToken();

    if (storedToken) {
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${storedToken}`,
                    'Content-Type': 'application/json'
                }
            });

            // Обрабатываем 404 и 401
            if (response.status === 404 || response.status === 401) {
                console.log('⚪ Токен недействителен, показываем экран входа');
                clearToken();
                return;
            }

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
            console.log('⚪ Токен недействителен:', error.message);
            clearToken();
        }
    }
}

/**
 * Получить текущего пользователя
 */
export function getCurrentUser() {
    return currentUser;
}

/**
 * Получить токен авторизации
 */
export function getAuthToken() {
    return authToken;
}

/**
 * Показать модальное окно верификации
 */
export function showVerifyModal() {
    const modal = document.getElementById('email-verify-modal');
    if (modal) modal.style.display = 'flex';
}

/**
 * Закрыть модальное окно верификации
 */
export function closeVerifyModal() {
    const modal = document.getElementById('email-verify-modal');
    if (modal) modal.style.display = 'none';
    clearErrors();
}

/**
 * Подтвердить email
 */
export async function verifyEmail() {
    clearErrors();

    const code = document.getElementById('verify-code')?.value.trim() || '';

    if (!code || code.length !== 6 || !/^\d+$/.test(code)) {
        showError('verify', 'Введите 6-значный код');
        return;
    }

    if (!currentUser?.user_id) {
        showError('verify', 'Пользователь не авторизован');
        return;
    }

    try {
        const response = await fetch('/api/auth/verify-email', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: currentUser.user_id,
                code: code
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('verify', data.message || 'Email подтверждён');
            if (currentUser) currentUser.email_verified = true;
            showApp();
            showNotification('Email подтверждён!', 'success');
            setTimeout(() => closeVerifyModal(), 2000);
        } else {
            showError('verify', data.detail || 'Неверный код');
        }
    } catch (error) {
        showError('verify', 'Ошибка проверки кода');
        console.error(error);
    }
}

/**
 * Отправить код подтверждения повторно
 */
export async function resendCode() {
    if (!currentUser?.user_id) return;

    try {
        const response = await fetch('/api/auth/resend-code', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: currentUser.user_id })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('verify', data.message || 'Код отправлен');
            showNotification('Код отправлен повторно', 'success');
        } else {
            showError('verify', data.detail || 'Ошибка отправки');
        }
    } catch (error) {
        showError('verify', 'Ошибка отправки кода');
        console.error(error);
    }
}

// =============================================================================
// ЭКСПОРТ ДЛЯ ГЛОБАЛЬНОГО ДОСТУПА (для inline обработчиков в HTML)
// =============================================================================
window.login = login;
window.register = register;
window.logout = logout;
window.getCurrentUser = getCurrentUser;
window.getAuthToken = getAuthToken;
window.checkStoredToken = checkStoredToken;
window.showVerifyModal = showVerifyModal;
window.closeVerifyModal = closeVerifyModal;
window.verifyEmail = verifyEmail;
window.resendCode = resendCode;
window.showApp = showApp;

// =============================================================================
// ИНИЦИАЛИЗАЦИЯ
// =============================================================================
// Проверка токена при загрузке модуля
checkStoredToken();