// =============================================================================
// DISCORD CLONE - UTILS.JS
// Утилиты и вспомогательные функции
// =============================================================================

/**
 * Переключение вкладок авторизации
 */
export function switchTab(tabName) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabs = document.querySelectorAll('.auth-tab');

    if (tabName === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
    }

    clearErrors();
}

/**
 * Экранирование HTML
 */
export function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

/**
 * Сохранение токена
 */
export function storeToken(token) {
    if (!token || token.length < 50) {
        console.error('Invalid token');
        return false;
    }
    localStorage.setItem('discord_token', token);
    return true;
}

/**
 * Получение токена
 */
export function getToken() {
    return localStorage.getItem('discord_token');
}

/**
 * Очистка токена
 */
export function clearToken() {
    localStorage.removeItem('discord_token');
}

/**
 * Проверка сложности пароля
 */
export function checkPasswordStrength() {
    const password = document.getElementById('reg-password')?.value || '';
    const bar = document.getElementById('password-strength-bar');

    if (!bar) return;

    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[!@#$%^&*()?]/.test(password)) strength++;

    bar.className = 'password-strength';
    if (strength <= 2) bar.classList.add('weak');
    else if (strength <= 4) bar.classList.add('medium');
    else bar.classList.add('strong');
}

/**
 * Показ уведомления
 */
export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerText = typeof message === 'object'
        ? (message.detail || message.message || JSON.stringify(message))
        : String(message);
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

/**
 * Безопасный fetch с токеном
 */
export async function secureFetch(url, options = {}) {
    const token = getToken();
    if (!token) throw new Error('No authentication token');

    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };

    const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'same-origin'
    });

    if (response.status === 401) {
        if (window.logout) await window.logout();
        throw new Error('Unauthorized - token expired');
    }

    if (response.status === 429) {
        throw new Error('Слишком много запросов. Подождите немного.');
    }

    return response;
}

/**
 * Очистка ошибок
 */
export function clearErrors() {
    [
        'login-error', 'register-error', 'verify-error',
        'verify-success', 'create-channel-error', 'channel-password-error'
    ].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}

/**
 * Показ ошибки
 */
export function showError(prefix, message) {
    const el = document.getElementById(`${prefix}-error`);
    if (el) {
        el.innerText = typeof message === 'object'
            ? (message.detail || message.message || JSON.stringify(message))
            : String(message);
        el.style.display = 'block';
    }
}

/**
 * Показ успеха
 */
export function showSuccess(prefix, message) {
    const el = document.getElementById(`${prefix}-success`);
    if (el) {
        el.innerText = String(message);
        el.style.display = 'block';
    }
}

/**
 * Валидация длины никнейма
 */
export function validateNicknameLength(input) {
    const value = input.value;
    const sanitized = value.replace(/[^a-zA-Zа-яА-Я0-9_]/g, '');

    if (value !== sanitized) input.value = sanitized;

    if (sanitized.length > 25) {
        input.value = sanitized.substring(0, 25);
        const warning = document.getElementById('profile-nickname-warning');
        if (warning) {
            warning.innerText = '⚠️ Никнейм не более 25 символов';
            warning.style.display = 'block';
            input.style.borderColor = 'var(--yellow)';
            setTimeout(() => {
                warning.style.display = 'none';
                input.style.borderColor = 'transparent';
            }, 3000);
        }
    }

    return sanitized;
}

/**
 * Форматирование размера файла
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Открытие изображения
 */
export function openImageModal(url) {
    window.open(url, '_blank');
}

/**
 * Валидация email
 */
export function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// =============================================================================
// ЭКСПОРТ ДЛЯ ГЛОБАЛЬНОГО ДОСТУПА (для onclick в HTML)
// =============================================================================
window.switchTab = switchTab;
window.escapeHtml = escapeHtml;
window.storeToken = storeToken;
window.getToken = getToken;
window.clearToken = clearToken;
window.checkPasswordStrength = checkPasswordStrength;
window.showNotification = showNotification;
window.secureFetch = secureFetch;
window.clearErrors = clearErrors;
window.showError = showError;
window.showSuccess = showSuccess;
window.validateNicknameLength = validateNicknameLength;
window.formatFileSize = formatFileSize;
window.openImageModal = openImageModal;
window.isValidEmail = isValidEmail;