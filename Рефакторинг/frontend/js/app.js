// =============================================================================
// DISCORD CLONE - APP.JS
// Основное приложение - инициализация и координация модулей
// =============================================================================
import { checkStoredToken } from './auth.js';
import { initFileUpload } from './files.js';

/**
 * Инициализация приложения
 */
function initApp() {
    console.log('🚀 Discord Clone - Инициализация приложения...');

    // Инициализация загрузки файлов
    initFileUpload();

    // Проверка сохранённого токена
    checkStoredToken();

    // Настройка глобальных обработчиков
    setupGlobalHandlers();

    console.log('✅ Приложение инициализировано');
}

/**
 * Настройка глобальных обработчиков
 */
function setupGlobalHandlers() {
    // Авто-ресайз textarea
    const messageInput = document.getElementById('message-input');

    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });

        // ✅ ЕДИНСТВЕННЫЙ обработчик Enter
        messageInput.addEventListener('keydown', (event) => {
            if (event.defaultPrevented) {
                return;
            }

            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();

                // Блокировка повторной отправки
                if (messageInput.dataset.sending === 'true') {
                    return;
                }

                messageInput.dataset.sending = 'true';

                try {
                    if (window.sendMessage) {
                        window.sendMessage();
                    }
                } finally {
                    setTimeout(() => {
                        messageInput.dataset.sending = 'false';
                    }, 100);
                }
            }
        });

        // Инициализация высоты
        messageInput.style.height = 'auto';
    }

    // Обработка закрытия модальных окон по клику вне
    document.addEventListener('click', (event) => {
        const modals = document.querySelectorAll('.modal, .profile-modal');

        modals.forEach(modal => {
            if (event.target === modal) {
                const closeBtn = modal.querySelector('.close-btn, .profile-close-btn');
                if (closeBtn && closeBtn.onclick) {
                    closeBtn.onclick();
                }
            }
        });
    });

    // Обработка ESC для закрытия модальных окон
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal[style*="flex"], .profile-modal[style*="flex"]');

            openModals.forEach(modal => {
                const closeBtn = modal.querySelector('.close-btn, .profile-close-btn');
                if (closeBtn && closeBtn.onclick) {
                    closeBtn.onclick();
                }
            });
        }
    });
}

/**
 * Проверка видимости страницы (для реконнекта)
 */
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        console.log('👁️ Страница стала видимой, проверка соединения...');

        const ws = window.ws;
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.log('🔄 Соединение отсутствует, попытка переподключения...');

            if (window.connectToChat) {
                window.connectToChat();
            }
        }
    }
});

/**
 * Обработка онлайн/оффлайн статуса браузера
 */
window.addEventListener('online', () => {
    console.log('🌐 Сеть доступна');
    showNotification('Соединение восстановлено', 'success');

    if (window.connectToChat) {
        window.connectToChat();
    }
});

window.addEventListener('offline', () => {
    console.log('🚫 Сеть недоступна');
    showNotification('Нет соединения с интернетом', 'error');
});

/**
 * Показ уведомления
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerText = typeof message === 'object'
        ? (message.detail || message.message || JSON.stringify(message))
        : String(message);

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// =============================================================================
// ЗАПУСК ПРИЛОЖЕНИЯ
// =============================================================================
document.addEventListener('DOMContentLoaded', initApp);

// Экспорт для глобального доступа
window.showNotification = showNotification;