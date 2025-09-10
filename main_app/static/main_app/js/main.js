// JavaScript для приложения импорта/экспорта контактов

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация компонентов
    initFileUpload();
    initExportPeriodToggle();
    initTooltips();
    initProgressBars();
});

// Инициализация загрузки файлов
function initFileUpload() {
    const fileInput = document.getElementById('id_file');
    const uploadArea = document.querySelector('.file-upload-area');
    
    if (!fileInput || !uploadArea) return;
    
    // Обработка клика по области загрузки
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Обработка выбора файла
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            updateUploadArea(file);
        }
    });
    
    // Обработка drag & drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateUploadArea(files[0]);
        }
    });
}

// Обновление области загрузки файла
function updateUploadArea(file) {
    const uploadArea = document.querySelector('.file-upload-area');
    const icon = uploadArea.querySelector('.file-upload-icon');
    const text = uploadArea.querySelector('.file-upload-text');
    const hint = uploadArea.querySelector('.file-upload-hint');
    
    if (file) {
        icon.innerHTML = '📄';
        text.textContent = file.name;
        hint.textContent = `Размер: ${formatFileSize(file.size)}`;
        uploadArea.style.borderColor = '#28a745';
        uploadArea.style.backgroundColor = '#d4edda';
    }
}

// Форматирование размера файла
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Инициализация переключения периода экспорта
function initExportPeriodToggle() {
    const periodRadios = document.querySelectorAll('input[name="export_period"]');
    const dateRangeFields = document.querySelector('.date-range-fields');
    
    if (!periodRadios.length || !dateRangeFields) return;
    
    periodRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'custom') {
                dateRangeFields.classList.add('show');
            } else {
                dateRangeFields.classList.remove('show');
            }
        });
    });
}

// Инициализация подсказок
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Инициализация прогресс-баров
function initProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        if (width) {
            setTimeout(() => {
                bar.style.width = width + '%';
            }, 100);
        }
    });
}

// Показать спиннер загрузки
function showLoadingSpinner() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) {
        spinner.style.display = 'block';
    }
}

// Скрыть спиннер загрузки
function hideLoadingSpinner() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

// Показать уведомление
function showNotification(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Автоматически скрыть через 5 секунд
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
}

// Валидация формы импорта
function validateImportForm() {
    const fileInput = document.getElementById('id_file');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('Пожалуйста, выберите файл для импорта', 'warning');
        return false;
    }
    
    // Проверка размера файла (10 МБ)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification('Размер файла не должен превышать 10 МБ', 'danger');
        return false;
    }
    
    // Проверка расширения файла
    const allowedExtensions = ['.csv', '.xlsx'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedExtensions.includes(fileExtension)) {
        showNotification('Поддерживаются только файлы CSV и XLSX', 'danger');
        return false;
    }
    
    return true;
}

// Валидация формы экспорта
function validateExportForm() {
    const period = document.querySelector('input[name="export_period"]:checked');
    
    if (!period) {
        showNotification('Пожалуйста, выберите период экспорта', 'warning');
        return false;
    }
    
    if (period.value === 'custom') {
        const dateFrom = document.getElementById('id_date_from');
        const dateTo = document.getElementById('id_date_to');
        
        if (!dateFrom.value || !dateTo.value) {
            showNotification('Пожалуйста, укажите даты начала и окончания периода', 'warning');
            return false;
        }
        
        if (new Date(dateFrom.value) >= new Date(dateTo.value)) {
            showNotification('Дата начала должна быть меньше даты окончания', 'warning');
            return false;
        }
    }
    
    return true;
}

// Обработка отправки формы импорта
document.addEventListener('submit', function(e) {
    if (e.target.id === 'import-form') {
        if (!validateImportForm()) {
            e.preventDefault();
            return false;
        }
        showLoadingSpinner();
    }
    
    if (e.target.id === 'export-form') {
        if (!validateExportForm()) {
            e.preventDefault();
            return false;
        }
        showLoadingSpinner();
    }
});

// Обработка ошибок AJAX
document.addEventListener('ajaxError', function(e) {
    hideLoadingSpinner();
    showNotification('Произошла ошибка при обработке запроса', 'danger');
});

// Обработка успешного AJAX
document.addEventListener('ajaxSuccess', function(e) {
    hideLoadingSpinner();
});

// Функция для обновления статистики
function updateStats() {
    fetch('/api/stats/')
        .then(response => response.json())
        .then(data => {
            // Обновляем статистику на странице
            const statsElements = document.querySelectorAll('.stats-number');
            statsElements.forEach(element => {
                const statType = element.getAttribute('data-stat');
                if (data[statType] !== undefined) {
                    element.textContent = data[statType];
                }
            });
        })
        .catch(error => {
            console.error('Ошибка при получении статистики:', error);
        });
}

// Автообновление статистики каждые 30 секунд
setInterval(updateStats, 30000);

// Функция для копирования в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Скопировано в буфер обмена', 'success');
    }, function(err) {
        console.error('Ошибка при копировании: ', err);
        showNotification('Не удалось скопировать в буфер обмена', 'danger');
    });
}

// Обработка кнопок копирования
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-btn')) {
        const text = e.target.getAttribute('data-copy');
        if (text) {
            copyToClipboard(text);
        }
    }
});

// Функция для экспорта таблицы в CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let cellText = cols[j].innerText;
            // Экранируем кавычки
            cellText = cellText.replace(/"/g, '""');
            // Оборачиваем в кавычки если содержит запятую или кавычку
            if (cellText.includes(',') || cellText.includes('"')) {
                cellText = '"' + cellText + '"';
            }
            row.push(cellText);
        }
        csv.push(row.join(','));
    }
    
    // Создаем и скачиваем файл
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Обработка кнопок экспорта таблиц
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('export-table-btn')) {
        const tableId = e.target.getAttribute('data-table');
        const filename = e.target.getAttribute('data-filename') || 'export.csv';
        exportTableToCSV(tableId, filename);
    }
});
