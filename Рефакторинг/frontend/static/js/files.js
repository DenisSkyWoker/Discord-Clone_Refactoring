// =============================================================================
// DISCORD CLONE - FILES.JS
// Модуль загрузки и управления файлами
// =============================================================================

import {
    getToken,
    showNotification,
    formatFileSize
} from './utils.js';

let pendingFiles = [];

/**
 * Инициализация обработчика загрузки файлов
 */
export function initFileUpload() {
    const fileInput = document.getElementById('file-input');

    if (!fileInput) {
        console.warn('⚠️ File input element not found');
        return;
    }

    fileInput.addEventListener('change', handleFileSelect);
    console.log('✅ [FILES] Инициализация завершена');
}

/**
 * Обработка выбора файлов
 */
async function handleFileSelect(event) {
    console.log('🚀 [FILE INPUT] Событие change активировано');

    const files = event.target.files;
    console.log('📂 [FILE INPUT] Получено файлов:', files ? files.length : 0);

    if (!files || files.length === 0) {
        console.warn('⚠️ [FILE INPUT] Файлы не выбраны');
        return;
    }

    // Очистка предыдущих данных
    pendingFiles = [];
    const filePreviewList = document.getElementById('file-preview-list');
    if (filePreviewList) {
        filePreviewList.innerHTML = '';
    }

    for (let file of files) {
        console.log(`🔄 [LOOP] Обработка файла: "${file.name}" (${file.size} байт)`);

        // Проверка размера (макс. 10 MB)
        if (file.size > 10 * 1024 * 1024) {
            console.error(`❌ [VALIDATION] Файл слишком большой: ${file.name}`);
            showNotification(`Файл ${file.name} слишком большой (макс. 10 MB)`, 'error');
            continue;
        }

        const formData = new FormData();
        formData.append('file', file);

        console.log(`⬆️ [UPLOAD] Загрузка файла: "${file.name}"`);

        try {
            const token = getToken();
            console.log(`🔑 [AUTH] Token: ${token ? 'Да' : 'Нет'}`);

            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            console.log(`📡 [NETWORK] Ответ сервера: Status ${response.status}`);

            const data = await response.json();

            if (response.ok) {
                console.log(`✅ [SUCCESS] Файл загружен:`, data);
                pendingFiles.push(data);
                window.pendingFiles = pendingFiles;  // ← Синхронизируем с window
                addFilePreview(data);
            } else {
                console.error(`⚠️ [SERVER ERROR] Ошибка:`, data);
                showNotification(`Ошибка загрузки ${file.name}: ${data.detail}`, 'error');
            }
        } catch (error) {
            console.error(`💥 [EXCEPTION] Ошибка загрузки:`, error);
            showNotification(`Ошибка загрузки ${file.name}`, 'error');
        }
    }

    // Показ контейнера превью
    const filePreviewContainer = document.getElementById('file-preview-container');
    if (filePreviewContainer) {
        filePreviewContainer.style.display = pendingFiles.length > 0 ? 'block' : 'none';
    }

    console.log('🏁 [FILE INPUT] Обработка завершена');
}

/**
 * Добавление превью файла
 */
function addFilePreview(fileData) {
    console.log('🖼️ [PREVIEW] Добавление превью:', fileData.file_name);

    const filePreviewList = document.getElementById('file-preview-list');
    if (!filePreviewList) return;

    const previewItem = document.createElement('div');
    previewItem.className = 'file-preview-item';

    let previewContent = '';

    if (fileData.file_type && fileData.file_type.startsWith('image/')) {
        previewContent = `
            <img src="${fileData.file_url}" alt="${fileData.file_name}">
            <span class="file-name">${fileData.file_name}</span>
            <span class="file-size">${formatFileSize(fileData.file_size)}</span>
        `;
    } else if (fileData.file_type && fileData.file_type.startsWith('video/')) {
        previewContent = `
            <video src="${fileData.file_url}" controls></video>
            <span class="file-name">${fileData.file_name}</span>
            <span class="file-size">${formatFileSize(fileData.file_size)}</span>
        `;
    } else {
        previewContent = `
            <div class="file-icon">📄</div>
            <div class="file-info">
                <span class="file-name">${fileData.file_name}</span>
                <span class="file-size">${formatFileSize(fileData.file_size)}</span>
            </div>
        `;
    }

    previewItem.innerHTML = `
        ${previewContent}
        <button type="button" class="remove-file-btn" onclick="removeFile('${fileData.file_url}')">✕</button>
    `;

    filePreviewList.appendChild(previewItem);
    console.log('✅ [PREVIEW] Превью добавлено');
}

/**
 * Удаление файла из очереди
 */
export function removeFile(fileUrl) {
    console.log('🗑️ [REMOVE] Удаление файла:', fileUrl);

    pendingFiles = pendingFiles.filter(f => f.file_url !== fileUrl);
    window.pendingFiles = pendingFiles;  // ← Синхронизируем с window

    const filePreviewList = document.getElementById('file-preview-list');
    if (filePreviewList) {
        filePreviewList.innerHTML = '';
        pendingFiles.forEach(f => addFilePreview(f));
    }

    const filePreviewContainer = document.getElementById('file-preview-container');
    if (filePreviewContainer && pendingFiles.length === 0) {
        filePreviewContainer.style.display = 'none';
    }
}

/**
 * Отмена загрузки файлов
 */
export function cancelFileUpload() {
    console.log('❌ [CANCEL] Отмена загрузки');

    pendingFiles = [];
    window.pendingFiles = pendingFiles;  // ← Синхронизируем с window

    const filePreviewList = document.getElementById('file-preview-list');
    const filePreviewContainer = document.getElementById('file-preview-container');
    const fileInput = document.getElementById('file-input');

    if (filePreviewList) filePreviewList.innerHTML = '';
    if (filePreviewContainer) filePreviewContainer.style.display = 'none';
    if (fileInput) fileInput.value = '';
}

/**
 * Получение ожидающих файлов
 */
export function getPendingFiles() {
    return [...pendingFiles];
}

/**
 * Очистка очереди файлов
 */
export function clearPendingFiles() {
    pendingFiles = [];
    window.pendingFiles = pendingFiles;  // ← Синхронизируем с window

    const filePreviewList = document.getElementById('file-preview-list');
    const filePreviewContainer = document.getElementById('file-preview-container');
    const fileInput = document.getElementById('file-input');

    if (filePreviewList) filePreviewList.innerHTML = '';
    if (filePreviewContainer) filePreviewContainer.style.display = 'none';
    if (fileInput) fileInput.value = '';
}

// =============================================================================
// ЭКСПОРТ ДЛЯ ГЛОБАЛЬНОГО ДОСТУПА
// =============================================================================
window.removeFile = removeFile;
window.cancelFileUpload = cancelFileUpload;
window.getPendingFiles = getPendingFiles;
window.clearPendingFiles = clearPendingFiles;
window.pendingFiles = pendingFiles;  // ← Важно для chat.js!

// ✅ Инициализация при загрузке модуля (не DOMContentLoaded!)
initFileUpload();