// =============================================================================
// DISCORD CLONE - PROFILE.JS
// Модуль управления профилем пользователя
// =============================================================================

import {
    secureFetch,
    showNotification,
    validateNicknameLength,
    isValidEmail
} from './utils.js';
import { getCurrentUser, getAuthToken, logout } from './auth.js';

let verificationTimer = null;
let canResendCode = true;

/**
 * Показать модальное окно профиля
 */
export function showProfileModal() {
    const modal = document.getElementById('profile-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadProfileData();
    }
}

/**
 * Закрыть модальное окно профиля
 */
export function closeProfileModal() {
    const modal = document.getElementById('profile-modal');
    if (modal) modal.style.display = 'none';

    clearProfileMessages();

    if (verificationTimer) {
        clearInterval(verificationTimer);
        verificationTimer = null;
    }

    canResendCode = true;
}

/**
 * Очистка сообщений профиля
 */
function clearProfileMessages() {
    const elements = [
        'profile-success',
        'profile-error',
        'delete-account-error',
        'verify-email-success',
        'verify-email-error'
    ];

    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.style.display = 'none';
            el.classList.remove('active');
        }
    });
}

/**
 * Показ успеха
 */
function showProfileSuccess(message) {
    const el = document.getElementById('profile-success');
    if (el) {
        el.innerText = message;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    }
}

/**
 * Показ ошибки
 */
function showProfileError(message) {
    const el = document.getElementById('profile-error');
    if (el) {
        el.innerText = message;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    }
}

/**
 * Загрузка данных профиля
 */
export async function loadProfileData() {
    try {
        const response = await secureFetch('/api/auth/me');
        const data = await response.json();

        // Заполнение полей
        const fields = {
            'profile-name': data.nickname,
            'profile-nickname-input': data.nickname,
            'profile-email': data.email || 'Не указан',
            'profile-email-input': data.email || '',
            'profile-user-id': data.user_id,
            'profile-avatar-large': data.nickname.charAt(0).toUpperCase()
        };

        Object.entries(fields).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) el.innerText = value;
        });

        // Бейдж email
        const emailBadge = document.getElementById('profile-email-badge');
        if (emailBadge) {
            if (data.email_verified) {
                emailBadge.className = 'profile-status-badge verified';
                emailBadge.innerText = 'Подтверждён';
            } else {
                emailBadge.className = 'profile-status-badge unverified';
                emailBadge.innerText = 'Не подтверждён';
            }
        }

        // Даты
        if (data.created_at) {
            const createdDate = new Date(data.created_at);
            const el = document.getElementById('profile-created-at');
            if (el) {
                el.innerText = createdDate.toLocaleDateString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            }
        }

        if (data.last_login) {
            const lastLogin = new Date(data.last_login);
            const el = document.getElementById('profile-last-login');
            if (el) {
                el.innerText = lastLogin.toLocaleString('ru-RU', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        }

        initializeEmailButton();
        await loadProfileStats();
        await loadProfileSessions();

    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
        showProfileError('Не удалось загрузить данные профиля');
    }
}

/**
 * Загрузка статистики профиля
 */
export async function loadProfileStats() {
    try {
        const response = await secureFetch('/api/profile/stats');
        const data = await response.json();

        const messagesCount = document.getElementById('profile-messages-count');
        const channelsCount = document.getElementById('profile-channels-count');

        if (messagesCount) {
            messagesCount.innerText = String(data.messages_count || 0);
        }
        if (channelsCount) {
            channelsCount.innerText = String(data.channels_count || 0);
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

/**
 * Загрузка списка сессий
 */
export async function loadProfileSessions() {
    try {
        const response = await secureFetch('/api/auth/sessions');
        const data = await response.json();

        const sessionsList = document.getElementById('profile-sessions-list');
        if (!sessionsList) return;

        sessionsList.innerHTML = '';

        if (data.sessions && data.sessions.length > 0) {
            data.sessions.forEach((session) => {
                const {
                    id,
                    is_current = false,
                    device = 'Неизвестное устройство',
                    ip_address = 'IP неизвестен',
                    last_active = 'Время неизвестно'
                } = session;

                const div = document.createElement('div');
                div.className = 'profile-session-item' + (is_current ? ' profile-session-current' : '');

                div.innerHTML = `
                    <div class="profile-session-info">
                        <div class="profile-session-device">
                            ${is_current ? '🖥️' : '💻'} ${device}
                        </div>
                        <div class="profile-session-location">
                            📍 ${ip_address} • ${last_active}
                        </div>
                    </div>
                    ${is_current
                    ? '<span class="profile-status-badge verified">Активна</span>'
                    : `<button class="profile-session-terminate" data-session-id="${id}">Завершить</button>`
                }
                `;

                sessionsList.appendChild(div);
            });
        } else {
            sessionsList.innerHTML = `
                <div class="profile-session-item">
                    <div class="profile-session-info">
                        <div class="profile-session-device">Нет активных сессий</div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Ошибка загрузки сессий:', error);
    }
}

/**
 * Обновление профиля
 */
export async function updateProfile() {
    clearProfileMessages();

    const nickname = document.getElementById('profile-nickname-input')?.value.trim() || '';
    const email = document.getElementById('profile-email-input')?.value.trim() || '';

    if (!nickname || nickname.length < 3 || nickname.length > 25) {
        showProfileError('Никнейм должен быть от 3 до 25 символов');
        return;
    }

    try {
        const response = await secureFetch('/api/auth/profile', {
            method: 'PUT',
            body: JSON.stringify({ nickname, email: email || null })
        });

        const data = await response.json();

        if (response.ok) {
            showProfileSuccess('✅ Профиль обновлён!');

            const currentUser = getCurrentUser();
            if (currentUser) {
                currentUser.nickname = nickname;
            }

            // Обновление UI
            const elements = {
                'user-name': nickname,
                'user-avatar': nickname.charAt(0).toUpperCase(),
                'profile-avatar-large': nickname.charAt(0).toUpperCase(),
                'profile-name': nickname
            };

            Object.entries(elements).forEach(([id, value]) => {
                const el = document.getElementById(id);
                if (el) el.innerText = value;
            });
        } else {
            showProfileError(data.detail || 'Ошибка обновления профиля');
        }
    } catch (error) {
        console.error('Ошибка обновления профиля:', error);
        showProfileError('Ошибка соединения с сервером');
    }
}

/**
 * Изменение пароля
 */
export async function changePassword() {
    clearProfileMessages();

    const currentPassword = document.getElementById('profile-current-password')?.value || '';
    const newPassword = document.getElementById('profile-new-password')?.value || '';
    const confirmPassword = document.getElementById('profile-confirm-password')?.value || '';

    if (!currentPassword || !newPassword || !confirmPassword) {
        showProfileError('Заполните все поля пароля');
        return;
    }

    if (newPassword !== confirmPassword) {
        showProfileError('Новые пароли не совпадают');
        return;
    }

    if (newPassword.length < 8) {
        showProfileError('Пароль должен быть не менее 8 символов');
        return;
    }

    try {
        const response = await secureFetch('/api/auth/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showProfileSuccess('✅ Пароль успешно изменён!');

            // Очистка полей
            ['profile-current-password', 'profile-new-password', 'profile-confirm-password'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = '';
            });
        } else {
            showProfileError(data.detail || 'Ошибка смены пароля');
        }
    } catch (error) {
        console.error('Ошибка смены пароля:', error);
        showProfileError('Ошибка соединения с сервером');
    }
}

/**
 * Завершение всех сессий
 */
export async function terminateAllSessions() {
    try {
        const response = await secureFetch('/api/auth/sessions', { method: 'DELETE' });

        if (response.ok) {
            showProfileSuccess('✅ Все другие сессии завершены');
            await loadProfileSessions();
        } else {
            showProfileError('Не удалось завершить сессии');
        }
    } catch (error) {
        console.error('Ошибка завершения сессий:', error);
        showProfileError('Ошибка соединения с сервером');
    }
}

/**
 * Показать подтверждение удаления аккаунта
 */
export function showDeleteAccountConfirm() {
    const modal = document.getElementById('delete-account-modal');
    const nicknameInput = document.getElementById('delete-confirm-nickname');
    const errorEl = document.getElementById('delete-account-error');

    if (modal) modal.style.display = 'flex';
    if (nicknameInput) nicknameInput.value = '';
    if (errorEl) errorEl.style.display = 'none';
}

/**
 * Закрыть подтверждение удаления аккаунта
 */
export function closeDeleteAccountModal() {
    const modal = document.getElementById('delete-account-modal');
    if (modal) modal.style.display = 'none';
}

/**
 * Удаление аккаунта
 */
export async function deleteAccount() {
    const currentUser = getCurrentUser();
    const confirmNickname = document.getElementById('delete-confirm-nickname')?.value.trim() || '';
    const errorEl = document.getElementById('delete-account-error');

    if (confirmNickname !== currentUser?.nickname) {
        if (errorEl) {
            errorEl.innerText = 'Никнейм не совпадает';
            errorEl.style.display = 'block';
        }
        return;
    }

    try {
        const response = await secureFetch('/api/auth/delete-account', { method: 'DELETE' });

        if (response.ok) {
            await logout();
            showNotification('Аккаунт удалён', 'warning');
        } else {
            const data = await response.json();
            if (errorEl) {
                errorEl.innerText = data.detail || 'Ошибка удаления';
                errorEl.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('Ошибка удаления аккаунта:', error);
        if (errorEl) {
            errorEl.innerText = 'Ошибка соединения';
            errorEl.style.display = 'block';
        }
    }
}

/**
 * Подтверждение email из профиля
 */
export async function verifyEmailFromProfile() {
    const currentUser = getCurrentUser();
    const code = document.getElementById('profile-verification-code')?.value.trim() || '';
    const errorEl = document.getElementById('verify-email-error');
    const successEl = document.getElementById('verify-email-success');

    if (!code || code.length !== 6 || !/^\d+$/.test(code)) {
        if (errorEl) {
            errorEl.innerText = '❌ Введите 6-значный код из письма';
            errorEl.classList.add('active');
            setTimeout(() => errorEl.classList.remove('active'), 5000);
        }
        return;
    }

    try {
        const response = await secureFetch('/api/auth/verify-email', {
            method: 'POST',
            body: JSON.stringify({ user_id: currentUser?.user_id, code })
        });

        const data = await response.json();

        if (response.ok) {
            if (successEl) {
                successEl.innerText = '✅ Email подтверждён!';
                successEl.classList.add('active');
            }

            const emailBadge = document.getElementById('profile-email-badge');
            if (emailBadge) {
                emailBadge.className = 'profile-status-badge verified';
                emailBadge.innerText = 'Подтверждён';
            }

            setTimeout(() => {
                const container = document.getElementById('verification-code-container');
                if (container) container.style.display = 'none';
                if (successEl) successEl.classList.remove('active');
            }, 2000);

            showNotification('Email подтверждён!', 'success');
        } else {
            if (errorEl) {
                errorEl.innerText = '❌ ' + (data.detail || 'Неверный код');
                errorEl.classList.add('active');
                setTimeout(() => errorEl.classList.remove('active'), 5000);
            }
        }
    } catch (error) {
        console.error('Ошибка подтверждения email:', error);
        if (errorEl) {
            errorEl.innerText = '❌ Ошибка соединения с сервером';
            errorEl.classList.add('active');
            setTimeout(() => errorEl.classList.remove('active'), 5000);
        }
    }
}

/**
 * Отправка кода подтверждения email
 */
export async function sendVerificationEmail() {
    const currentUser = getCurrentUser();
    const btn = document.getElementById('verify-email-btn');
    const successEl = document.getElementById('verify-email-success');
    const errorEl = document.getElementById('verify-email-error');
    const emailInput = document.getElementById('profile-email-input');
    const codeContainer = document.getElementById('verification-code-container');

    if (successEl) successEl.classList.remove('active');
    if (errorEl) errorEl.classList.remove('active');

    if (!canResendCode) {
        if (errorEl) {
            errorEl.innerText = '⏳ Подождите окончания таймера';
            errorEl.classList.add('active');
            setTimeout(() => errorEl.classList.remove('active'), 5000);
        }
        return;
    }

    const email = emailInput?.value.trim() || '';
    if (!email || !isValidEmail(email)) {
        if (errorEl) {
            errorEl.innerText = '❌ Введите корректный email';
            errorEl.classList.add('active');
            setTimeout(() => errorEl.classList.remove('active'), 5000);
        }
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '⏳ Отправка...';
        btn.classList.add('sending');
    }

    try {
        const response = await secureFetch('/api/auth/resend-code', {
            method: 'POST',
            body: JSON.stringify({ user_id: currentUser?.user_id })
        });

        const data = await response.json();

        if (response.ok) {
            if (successEl) {
                successEl.innerText = '✅ Код отправлен на ' + email;
                successEl.classList.add('active');
            }
            if (codeContainer) codeContainer.style.display = 'block';
            startResendTimer(60);
            setTimeout(() => {
                if (successEl) successEl.classList.remove('active');
            }, 5000);
        } else {
            if (errorEl) {
                errorEl.innerText = '❌ ' + (data.detail || 'Ошибка отправки кода');
                errorEl.classList.add('active');
                setTimeout(() => errorEl.classList.remove('active'), 5000);
            }
        }
    } catch (error) {
        let errorMessage = 'Ошибка соединения с сервером';
        if (error.message.includes('401')) errorMessage = 'Требуется повторный вход';
        else if (error.message.includes('429')) errorMessage = 'Слишком много запросов';

        if (errorEl) {
            errorEl.innerText = '❌ ' + errorMessage;
            errorEl.classList.add('active');
            setTimeout(() => errorEl.classList.remove('active'), 5000);
        }
    } finally {
        if (canResendCode && btn) {
            btn.disabled = false;
            btn.innerHTML = '📩 Отправить код повторно';
            btn.classList.remove('sending');
        }
    }
}

/**
 * Таймер повторной отправки
 */
function startResendTimer(seconds) {
    canResendCode = false;

    const btn = document.getElementById('verify-email-btn');
    const timerEl = document.getElementById('verify-email-timer');
    const countdownEl = document.getElementById('timer-countdown');

    let remaining = seconds;

    if (timerEl) timerEl.classList.add('active');

    verificationTimer = setInterval(() => {
        remaining--;

        if (countdownEl) countdownEl.innerText = remaining;

        if (remaining <= 0) {
            clearInterval(verificationTimer);
            verificationTimer = null;

            if (timerEl) timerEl.classList.remove('active');
            canResendCode = true;

            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '📩 Отправить код повторно';
                btn.classList.remove('sending');
            }
        }
    }, 1000);
}

/**
 * Инициализация кнопки email
 */
function initializeEmailButton() {
    canResendCode = true;

    if (verificationTimer) {
        clearInterval(verificationTimer);
        verificationTimer = null;
    }
}

// Обработчик кнопок завершения сессии
document.addEventListener('DOMContentLoaded', () => {
    const sessionsList = document.getElementById('profile-sessions-list');

    if (sessionsList) {
        sessionsList.addEventListener('click', async (event) => {
            const button = event.target.closest('.profile-session-terminate');
            if (!button) return;

            const sessionId = button.dataset.sessionId;
            if (!sessionId) return;

            button.disabled = true;
            button.textContent = '...';

            try {
                const response = await secureFetch(`/api/auth/sessions/${sessionId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    showProfileSuccess('✅ Сессия завершена');
                    await loadProfileSessions();
                } else {
                    showProfileError('Не удалось завершить сессию');
                    button.disabled = false;
                    button.textContent = 'Завершить';
                }
            } catch (error) {
                console.error('Ошибка завершения сессии:', error);
                showProfileError('Ошибка соединения с сервером');
                button.disabled = false;
                button.textContent = 'Завершить';
            }
        });
    }
});

// Экспорт для глобального доступа
window.showProfileModal = showProfileModal;
window.closeProfileModal = closeProfileModal;
window.loadProfileData = loadProfileData;
window.updateProfile = updateProfile;
window.changePassword = changePassword;
window.terminateAllSessions = terminateAllSessions;
window.showDeleteAccountConfirm = showDeleteAccountConfirm;
window.closeDeleteAccountModal = closeDeleteAccountModal;
window.deleteAccount = deleteAccount;
window.verifyEmailFromProfile = verifyEmailFromProfile;
window.sendVerificationEmail = sendVerificationEmail;