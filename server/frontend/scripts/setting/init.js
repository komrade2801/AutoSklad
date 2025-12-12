 import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.jsonTablesDB = window.jsonTablesDB || {};

const categoryTranslations = {
    network: 'Сеть',
    security: 'Безопасность',
    database: 'База данных',
    sync: 'Синхронизация',
    frontend: 'Интерфейс'
};

const allowedRoles = new Set(['Разработчик', 'Администратор']);
const securityKeys = new Set(['SECRET_KEY', 'AES_KEY']);

let settingsState = {};
const originalValues = new Map();
const pendingChanges = new Map();
let isSaving = false;
let factoryResetLocked = false;

async function initialization(element_name) {
    if (!localStorage.getItem('token')) {
        console.log('token не обнаружен в хранилище!');
        window.location.href = '/';
        return;
    }

    nav_btn_add(element_name);
    await navbar_add(element_name);

    try {
        await ensureUserHasAccess();
    } catch (error) {
        console.error('Доступ к настройкам запрещён:', error);
        return;
    }

    try {
        await loadSettingsFromDatabase();
    } catch (error) {
        console.error('Error loading settings:', error);
        renderSettingsError();
    }
}

async function ensureUserHasAccess() {
    const rawUser = localStorage.getItem('user');
    if (!rawUser) {
        window.location.href = '/';
        return;
    }

    const userData = JSON.parse(rawUser);
    const response = await fetch(`/backend/get_role/${userData.role_id}`, {
        method: 'GET',
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error('Не удалось получить данные роли');
    }

    const roleData = await response.json();
    if (!allowedRoles.has(roleData.name)) {
        renderAccessDenied(roleData.name);
        throw new Error('Недостаточно прав для просмотра настроек');
    }
    return roleData;
}

function renderAccessDenied(roleName) {
    const column = document.getElementById('column-1');
    if (column) {
        column.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #fff;">
                <h3 style="margin-bottom: 16px;">Доступ ограничен</h3>
                <p>Ваша роль «${roleName || 'Неизвестно'}» не имеет прав на изменение системных настроек.</p>
            </div>
        `;
    }

    const buttons = [document.getElementById('saveButton'), document.getElementById('startButton')];
    buttons.forEach(btn => {
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Недоступно';
        }
    });

    const warning = document.getElementById('factoryResetWarning');
    if (warning) {
        warning.style.display = 'block';
        warning.textContent = 'Начните работу от учётной записи администратора или разработчика.';
    }
}

function renderSettingsError() {
    const column = document.getElementById('column-1');
    if (column) {
        column.innerHTML = '<p style="color: #fff;">Не удалось загрузить настройки. Попробуйте обновить страницу.</p>';
    }
}

async function loadSettingsFromDatabase() {
    const response = await fetch('../backend/settings');
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    settingsState = data || {};
    originalValues.clear();
    Object.values(settingsState).forEach(category => {
        category.forEach(setting => {
            originalValues.set(setting.key, setting.value);
        });
    });

    displaySettings(settingsState);
    updateSaveButtonState();
}

function displaySettings(settingsData) {
    const container = document.getElementById('column-1');
    if (!container) {
        return;
    }

    container.innerHTML = '';
    container.style.cssText = `
        --settings-padding: 10px;
        --settings-border-radius: 12px;
        --settings-border-color: rgba(255, 255, 255, 0.15);
        --settings-background: rgba(255, 255, 255, 0.05);
        --settings-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        --settings-primary-color: #003171;
        --settings-secondary-color: #C7E0F9;
        --settings-gap: 16px;
    `;
    container.style.flexDirection = 'column';
    container.style.flex = '1';
    container.style.height = '100%';
    container.style.overflow = 'hidden';
    container.style.padding = 'var(--settings-padding)';
    container.style.gap = 'var(--settings-gap)';

    const tabContainer = document.createElement('div');
    tabContainer.className = 'settings-tabs-header';
    Object.assign(tabContainer.style, {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '16px',
        backgroundColor: 'var(--settings-background)',
        borderRadius: 'var(--settings-border-radius)',
        border: '1px solid var(--settings-border-color)',
        boxShadow: 'var(--settings-shadow)',
        flexShrink: '0',
        justifyContent: 'center'
    });

    const contentContainer = document.createElement('div');
    contentContainer.className = 'settings-content';
    Object.assign(contentContainer.style, {
        flex: '1',
        overflowY: 'auto',
        padding: '16px 4px 0 0',
        minHeight: '0'
    });

    const categories = Object.keys(settingsData || {});
    if (categories.length === 0) {
        contentContainer.innerHTML = '<p style="color:#fff;">Настройки не найдены.</p>';
    }

    categories.forEach((category, index) => {
        const tabBtn = document.createElement('button');
        tabBtn.className = 'btn_vending settings-tab-btn';
        tabBtn.dataset.category = category;
        tabBtn.textContent = categoryTranslations[category] || category;
        Object.assign(tabBtn.style, {
            fontSize: '16px',
            fontWeight: '600',
            padding: '10px 16px',
            margin: '0',
            borderRadius: '8px',
            transition: 'all 0.3s ease'
        });
        tabBtn.onclick = () => showCategory(category, settingsData[category], contentContainer);
        tabContainer.appendChild(tabBtn);

        if (index === 0) {
            showCategory(category, settingsData[category], contentContainer);
        }
    });

    container.appendChild(tabContainer);
    container.appendChild(contentContainer);
}

function showCategory(categoryName, categorySettings = [], contentContainer) {
    const categoryDisplayName = categoryTranslations[categoryName] || categoryName;
    contentContainer.innerHTML = `
        <h3 style="color: white; margin-bottom: 20px; text-transform: capitalize; font-size: 18px; font-weight: 700; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">
            ${categoryDisplayName} - Настройки
        </h3>
    `;

    const formContainer = document.createElement('div');
    Object.assign(formContainer.style, {
        width: '100%',
        maxWidth: '700px',
        display: 'flex',
        flexDirection: 'column',
        gap: '15px'
    });

    categorySettings.forEach(setting => {
        const fieldContainer = document.createElement('div');
        fieldContainer.dataset.settingKey = setting.key;
        Object.assign(fieldContainer.style, {
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            transition: 'border-color 0.2s ease, box-shadow 0.2s ease'
        });

        const inputRow = document.createElement('div');
        Object.assign(inputRow.style, {
            display: 'flex',
            alignItems: 'center',
            gap: '15px',
            flexWrap: 'wrap'
        });

        const label = document.createElement('label');
        label.textContent = `${setting.key}:`;
        Object.assign(label.style, {
            color: 'white',
            fontWeight: 'bold',
            fontSize: '16px',
            minWidth: '120px',
            flexShrink: '0'
        });
        inputRow.appendChild(label);

        const currentValue = pendingChanges.has(setting.key)
            ? pendingChanges.get(setting.key)
            : setting.value;

        const input = createInputForSetting(setting, currentValue);
        inputRow.appendChild(input);
        fieldContainer.appendChild(inputRow);

        if (securityKeys.has(setting.key)) {
            fieldContainer.appendChild(createSecurityControls(setting, input));
        }

        if (setting.requires_restart) {
            const restartHint = document.createElement('small');
            restartHint.textContent = 'Требуется перезапуск приложения';
            Object.assign(restartHint.style, {
                color: '#ffc107',
                fontSize: '13px',
                marginTop: '6px'
            });
            fieldContainer.appendChild(restartHint);
        }

        if (setting.description) {
            const desc = document.createElement('small');
            desc.textContent = setting.description;
            Object.assign(desc.style, {
                color: '#ccc',
                fontSize: '14px',
                marginTop: '8px',
                fontStyle: 'italic',
                lineHeight: '1.4'
            });
            fieldContainer.appendChild(desc);
        }

        formContainer.appendChild(fieldContainer);
        updateFieldVisualState(setting.key);
    });

    contentContainer.appendChild(formContainer);
    updateActiveTab(categoryName);
}

function createInputForSetting(setting, currentValue) {
    let input;
    if (setting.type === 'bool') {
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = Boolean(currentValue);
        Object.assign(input.style, {
            width: '20px',
            height: '20px',
            flexShrink: '0'
        });
        input.addEventListener('change', (event) => handleInputChange(setting, event.target));
    } else {
        input = document.createElement('input');
        if (setting.sensitive) {
            input.type = 'password';
        } else if (setting.type === 'int') {
            input.type = 'number';
        } else {
            input.type = 'text';
        }
        input.value = currentValue ?? '';
        Object.assign(input.style, {
            flex: '1',
            minWidth: '220px',
            height: '40px',
            padding: '8px 12px',
            borderRadius: '6px',
            border: '2px solid #ddd',
            fontSize: '16px',
            backgroundColor: 'white',
            color: '#333'
        });
        input.addEventListener('input', (event) => handleInputChange(setting, event.target));
    }
    input.id = `input-${setting.key}`;
    return input;
}

function createSecurityControls(setting, inputElement) {
    const wrapper = document.createElement('div');
    Object.assign(wrapper.style, {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        marginTop: '8px'
    });

    const checkboxWrapper = document.createElement('label');
    checkboxWrapper.style.display = 'flex';
    checkboxWrapper.style.alignItems = 'center';
    checkboxWrapper.style.gap = '8px';
    checkboxWrapper.style.color = '#fff';
    checkboxWrapper.style.fontSize = '14px';

    const toggleCheckbox = document.createElement('input');
    toggleCheckbox.type = 'checkbox';
    toggleCheckbox.addEventListener('change', () => {
        inputElement.type = toggleCheckbox.checked ? 'text' : 'password';
    });
    checkboxWrapper.appendChild(toggleCheckbox);
    checkboxWrapper.appendChild(document.createTextNode('Показать ключ'));

    const regenerateBtn = document.createElement('button');
    regenerateBtn.type = 'button';
    regenerateBtn.className = 'btn_vending';
    regenerateBtn.textContent = 'Обновить';
    Object.assign(regenerateBtn.style, {
        width: '130px',
        height: '32px'
    });
    regenerateBtn.addEventListener('click', () => {
        const newKey = generateKeyFor(setting.key);
        inputElement.value = newKey;
        inputElement.dispatchEvent(new Event('input', { bubbles: true }));
    });

    wrapper.appendChild(checkboxWrapper);
    wrapper.appendChild(regenerateBtn);
    return wrapper;
}

function generateKeyFor(settingKey) {
    if (settingKey === 'AES_KEY') {
        return generateHexKey(16);
    }
    return generateBase64Key(32);
}

function getCrypto() {
    return window.crypto || window.msCrypto || null;
}

function generateHexKey(byteLength) {
    const cryptoObj = getCrypto();
    const array = new Uint8Array(byteLength);
    if (cryptoObj?.getRandomValues) {
        cryptoObj.getRandomValues(array);
    } else {
        for (let i = 0; i < byteLength; i += 1) {
            array[i] = Math.floor(Math.random() * 256);
        }
    }
    return Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('');
}

function generateBase64Key(byteLength) {
    const cryptoObj = getCrypto();
    const array = new Uint8Array(byteLength);
    if (cryptoObj?.getRandomValues) {
        cryptoObj.getRandomValues(array);
    } else {
        for (let i = 0; i < byteLength; i += 1) {
            array[i] = Math.floor(Math.random() * 256);
        }
    }
    let binary = '';
    array.forEach((b) => {
        binary += String.fromCharCode(b);
    });
    return btoa(binary).replace(/=+$/, '').slice(0, 48);
}

function handleInputChange(setting, inputElement) {
    const newValue = parseInputValue(setting, inputElement);
    updatePendingValue(setting.key, newValue);
    updateFieldVisualState(setting.key);
    updateSaveButtonState();
}

function parseInputValue(setting, inputElement) {
    if (setting.type === 'bool') {
        return inputElement.checked;
    }
    if (setting.type === 'int') {
        return inputElement.value === '' ? '' : Number(inputElement.value);
    }
    return inputElement.value;
}

function updatePendingValue(settingKey, newValue) {
    const originalValue = originalValues.get(settingKey);
    if (valuesAreEqual(newValue, originalValue)) {
        pendingChanges.delete(settingKey);
    } else {
        pendingChanges.set(settingKey, newValue);
    }
}

function valuesAreEqual(a, b) {
    if (typeof a === 'number' || typeof b === 'number') {
        return Number(a) === Number(b);
    }
    if (typeof a === 'boolean' || typeof b === 'boolean') {
        return Boolean(a) === Boolean(b);
    }
    return String(a ?? '') === String(b ?? '');
}

function updateFieldVisualState(settingKey) {
    const container = document.querySelector(`[data-setting-key="${settingKey}"]`);
    if (!container) return;
    const isDirty = pendingChanges.has(settingKey);
    container.style.borderColor = isDirty ? '#ffc107' : 'rgba(255, 255, 255, 0.1)';
    container.style.boxShadow = isDirty ? '0 0 10px rgba(255, 193, 7, 0.4)' : 'none';
}

function updateActiveTab(activeCategory) {
    const tabButtons = document.querySelectorAll('.settings-tabs-header .btn_vending');
    tabButtons.forEach((btn) => {
        if (btn.dataset.category === activeCategory) {
            btn.style.backgroundColor = 'var(--settings-primary-color)';
            btn.style.color = 'var(--settings-secondary-color)';
            btn.style.boxShadow = '0 2px 8px rgba(0, 49, 114, 0.4)';
            btn.style.transform = 'translateY(-1px)';
        } else {
            btn.style.background = 'radial-gradient(black, rgb(131,173,239) 1%, rgb(120,158,217) 97%, white)';
            btn.style.color = 'rgb(0,49,114)';
            btn.style.boxShadow = 'none';
            btn.style.transform = 'translateY(0)';
        }
    });
}

function updateSaveButtonState() {
    const saveBtn = document.getElementById('saveButton');
    if (!saveBtn) return;

    if (factoryResetLocked) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Сохранение недоступно';
        return;
    }

    if (isSaving) {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Сохранение...';
        return;
    }

    saveBtn.disabled = pendingChanges.size === 0;
    saveBtn.textContent = 'Сохранить';
}

function setSavingState(state) {
    isSaving = state;
    updateSaveButtonState();
}

async function saveSetting(settingKey, newValue) {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`../backend/settings/${settingKey}`, {
        method: 'PUT',
        headers: headers,
        body: JSON.stringify(newValue)
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `Не удалось сохранить настройку ${settingKey}`);
    }

    return response.json();
}

async function saveAllSettings() {
    if (factoryResetLocked) {
        alert('Сохранение недоступно во время сброса к заводским настройкам.');
        return;
    }

    if (pendingChanges.size === 0) {
        alert('Нет изменений для сохранения.');
        return;
    }

    try {
        validatePendingChanges();
    } catch (error) {
        alert(error.message);
        return;
    }

    setSavingState(true);

    try {
        const saveOperations = [];
        const requiresRestart = new Set();
        
        // Собираем информацию о настройках, требующих перезапуска
        pendingChanges.forEach((value, key) => {
            const meta = findSettingByKey(key);
            if (meta?.requires_restart) {
                requiresRestart.add(key);
            }
            saveOperations.push(saveSetting(key, value));
        });
        
        await Promise.all(saveOperations);
        pendingChanges.clear();
        await loadSettingsFromDatabase();
        
        // Перезапуск только если есть настройки, требующие перезапуска
        if (requiresRestart.size > 0) {
            await requestApplicationRestart();
            alert('Настройки сохранены. Приложение перезапускается...');
        } else {
            alert('Настройки успешно сохранены.');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Error saving settings: ' + error.message);
    } finally {
        setSavingState(false);
        updateSaveButtonState();
    }
}

function validatePendingChanges() {
    pendingChanges.forEach((value, key) => {
        const meta = findSettingByKey(key);
        if (!meta) {
            throw new Error(`Настройка ${key} не найдена.`);
        }
        
        // Валидация целых чисел
        if (meta.type === 'int') {
            if (value === '' || value === null || value === undefined) {
                throw new Error(`Поле ${key} не может быть пустым.`);
            }
            const numValue = Number(value);
            if (Number.isNaN(numValue) || !Number.isInteger(numValue)) {
                throw new Error(`Поле ${key} должно быть целым числом.`);
            }
            
            // Специфичная валидация для порта
            if (key === 'port') {
                if (numValue < 1 || numValue > 65535) {
                    throw new Error(`Порт должен быть в диапазоне от 1 до 65535, получено: ${numValue}`);
                }
            }
            
            // Специфичная валидация для таймаутов
            if (key === 'SENDER_TIMEOUT' || key === 'RECEIVER_TIMEOUT') {
                if (numValue < 1 || numValue > 3600) {
                    throw new Error(`Таймаут должен быть в диапазоне от 1 до 3600 секунд, получено: ${numValue}`);
                }
            }
        }
        
        // Валидация IP-адреса
        if (key === 'Host') {
            const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            if (!ipRegex.test(String(value))) {
                throw new Error(`Некорректный IP-адрес: ${value}`);
            }
        }
        
        // Валидация булевых значений
        if (meta.type === 'bool') {
            if (typeof value !== 'boolean' && value !== 0 && value !== 1 && value !== '0' && value !== '1') {
                throw new Error(`Поле ${key} должно быть булевым значением (true/false).`);
            }
        }
    });
}

function findSettingByKey(settingKey) {
    for (const category of Object.values(settingsState)) {
        const found = category.find((item) => item.key === settingKey);
        if (found) return found;
    }
    return null;
}

async function requestApplicationRestart() {
    try {
        const response = await fetch('../backend/settings/restart', {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error('Не удалось инициировать перезапуск приложения:', error);
        alert('Не удалось инициировать перезапуск: ' + error.message);
    }
}

function setFactoryResetLock(locked) {
    factoryResetLocked = locked;
    const warning = document.getElementById('factoryResetWarning');
    if (warning) {
        if (locked) {
            warning.style.display = 'block';
            warning.textContent = 'Идёт сброс к заводским настройкам. Дождитесь завершения.';
        } else {
            warning.style.display = 'none';
            warning.textContent = '';
        }
    }
    updateSaveButtonState();
}

// Export functions for compatibility with inline handlers
window.loadSettingsFromDatabase = loadSettingsFromDatabase;
window.displaySettings = displaySettings;
window.editSetting = () => {};
window.saveSetting = saveSetting;
window.saveAllSettings = saveAllSettings;
window.initialization = initialization;
window.setFactoryResetLock = setFactoryResetLock;
window.isFactoryResetLocked = () => factoryResetLocked;