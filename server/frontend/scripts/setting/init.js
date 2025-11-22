import { createTableDB } from './createTableDB.js'
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

window.jsonTablesDB = window.jsonTablesDB || {};

//// Функция для получения JSON-данных через эндпоинт
//export async function fetchData(url) {
//    try {
//        const response = await fetch(url);
//        if (!response.ok) {
//            throw new Error("Ошибка сети, статус: ${response.status}");
//        }
//        const jsonData = await response.json();
//        return jsonData;
//    } catch (error) {
//        console.error("Ошибка получения данных:", error);
//        return null;
//    }
//}
//
///*
// * Функция загрузки и сохранения JSON.
// * Возвращает Promise, чтобы можно было ждать результата.
// */
//export function initData(url) {
//    return fetchData(url)
//      .then(data => {
//        return data;
//      })
//      .catch(err => {
//        console.error('Не удалось загрузить инструменты', err);
//        return null;
//      });
//}


async function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
        return;
    }
    nav_btn_add(element_name);
    navbar_add(element_name);

    // Load settings from database instead of JSON
    try {
        await loadSettingsFromDatabase();
    } catch (error) {
        console.error('Error loading settings:', error);
        document.getElementById('column-1').innerHTML = '<p>Error loading settings from database</p>';
    }
}

// Load all settings from database and display in UI
async function loadSettingsFromDatabase() {
    try {
        const response = await fetch('../backend/settings');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        console.log('Loaded settings from database:', data);

        // Display settings in the UI
        displaySettings(data);

    } catch (error) {
        console.error('Failed to load settings:', error);
        document.getElementById('column-1').innerHTML = '<p>Error loading settings</p>';
        throw error;
    }
}

// Russian translation mapping
const categoryTranslations = {
    'network': 'Сеть',
    'security': 'Безопасность',
    'database': 'База данных',
    'sync': 'Синхронизация',
    'frontend': 'Интерфейс'
};

// Display settings grouped by categories
function displaySettings(settingsData) {
    const container = document.getElementById('column-1');
    container.innerHTML = '';

    // Define CSS variables for consistent styling
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

    // Set container to flex column layout with consistent padding
    container.style.flexDirection = 'column';
    container.style.flex = '1'
    container.style.height = '100%';
    container.style.overflow = 'hidden';
    container.style.padding = 'var(--settings-padding)';
    container.style.gap = 'var(--settings-gap)';

    // Create tab navigation header with styled container
    const tabContainer = document.createElement('div');
    tabContainer.className = 'settings-tabs-header';
    tabContainer.style.display = 'flex';
    tabContainer.style.flexWrap = 'wrap';
    tabContainer.style.gap = '12px';
    tabContainer.style.padding = '16px';
    tabContainer.style.backgroundColor = 'var(--settings-background)';
    tabContainer.style.borderRadius = 'var(--settings-border-radius)';
    tabContainer.style.border = '1px solid var(--settings-border-color)';
    tabContainer.style.boxShadow = 'var(--settings-shadow)';
    tabContainer.style.flexShrink = '0';
    tabContainer.style.justifyContent = 'center'

    // Create scrollable content container with proper styling
    const contentContainer = document.createElement('div');
    contentContainer.className = 'settings-content';
    contentContainer.style.flex = '1';
    contentContainer.style.overflowY = 'auto';
    contentContainer.style.padding = '16px 4px 0 0'; // Add padding but preserve scrollbar
    contentContainer.style.minHeight = '0'; // Allow shrinking

    // Get all categories
    const categories = Object.keys(settingsData);

    categories.forEach((category, index) => {
        // Create tab button with improved styling
        const tabBtn = document.createElement('button');
        tabBtn.className = 'btn_vending settings-tab-btn';
        tabBtn.textContent = categoryTranslations[category] || category;
        tabBtn.style.fontSize = '16px';
        tabBtn.style.fontWeight = '600';
        tabBtn.style.padding = '10px 16px';
        tabBtn.style.margin = '0';
        tabBtn.style.borderRadius = '8px';
        tabBtn.style.transition = 'all 0.3s ease';
        tabBtn.onclick = () => showCategory(category, settingsData[category], contentContainer);
        tabContainer.appendChild(tabBtn);

        // Active state for first tab with custom properties
        if (index === 0) {
            tabBtn.style.backgroundColor = 'var(--settings-primary-color)';
            tabBtn.style.color = 'var(--settings-secondary-color)';
            tabBtn.style.boxShadow = '0 2px 8px rgba(0, 49, 114, 0.4)';
            showCategory(category, settingsData[category], contentContainer);
        }
    });

    container.appendChild(tabContainer);
    container.appendChild(contentContainer);
}

// Show settings for a specific category
function showCategory(categoryName, categorySettings, contentContainer) {
    const categoryDisplayName = categoryTranslations[categoryName] || categoryName;
    contentContainer.innerHTML = `<h3 style="color: white; margin-bottom: 20px; text-transform: capitalize; font-size: 18px; font-weight: 700; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">${categoryDisplayName} - Настройки</h3>`;

    const formContainer = document.createElement('div');
    formContainer.style.width = '100%';
    formContainer.style.maxWidth = '700px';
    formContainer.style.display = 'flex';
    formContainer.style.flexDirection = 'column';
    formContainer.style.gap = '15px';

    categorySettings.forEach(setting => {
        const fieldContainer = document.createElement('div');
        fieldContainer.style.display = 'flex';
        fieldContainer.style.flexDirection = 'column';
        fieldContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
        fieldContainer.style.padding = '12px';
        fieldContainer.style.borderRadius = '8px';
        fieldContainer.style.border = '1px solid rgba(255, 255, 255, 0.1)';

        // Label and input row
        const inputRow = document.createElement('div');
        inputRow.style.display = 'flex';
        inputRow.style.alignItems = 'center';
        inputRow.style.gap = '15px';

        // Label
        const label = document.createElement('label');
        label.textContent = `${setting.key}:`;
        label.style.color = 'white';
        label.style.fontWeight = 'bold';
        label.style.fontSize = '16px';
        label.style.minWidth = '120px';
        label.style.flexShrink = '0';
        inputRow.appendChild(label);

        // Input field
        let input;
        if (setting.type === 'bool') {
            input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = setting.value;
            input.style.width = '20px';
            input.style.height = '20px';
            input.style.flexShrink = '0';
        } else {
            input = document.createElement('input');
            if (setting.sensitive) {
                input.type = 'password';
            } else if (setting.type === 'int') {
                input.type = 'number';
            } else {
                input.type = 'text';
            }
            input.value = setting.value;
            input.style.flex = '1';
            input.style.height = '40px';
            input.style.padding = '8px 12px';
            input.style.borderRadius = '6px';
            input.style.border = '2px solid #ddd';
            input.style.fontSize = '16px';
            input.style.backgroundColor = 'white';
            input.style.color = '#333';
        }

        input.id = `input-${setting.key}`;
        input.addEventListener('change', () => {
            const saveBtn = document.getElementById(`save-btn-${setting.key}`);
            if (saveBtn) saveBtn.style.display = 'inline';
        });

        inputRow.appendChild(input);

        // Save button for this field
        const saveBtn = document.createElement('button');
        saveBtn.textContent = 'Сохранить';
        saveBtn.className = 'btn_vending';
        saveBtn.style.fontSize = '16px';
        saveBtn.style.width = '100px';
        saveBtn.style.height = '36px';
        saveBtn.style.display = 'none';
        saveBtn.id = `save-btn-${setting.key}`;
        saveBtn.onclick = () => saveSetting(setting.key);
        inputRow.appendChild(saveBtn);

        fieldContainer.appendChild(inputRow);

        // Description
        if (setting.description) {
            const desc = document.createElement('small');
            desc.textContent = setting.description;
            desc.style.color = '#ccc';
            desc.style.fontSize = '14px';
            desc.style.marginTop = '8px';
            desc.style.fontStyle = 'italic';
            desc.style.lineHeight = '1.4';
            fieldContainer.appendChild(desc);
        }

        formContainer.appendChild(fieldContainer);
    });

    contentContainer.appendChild(formContainer);

    // Update active tab styling
    updateActiveTab(categoryName);
}

// Update active tab styling
function updateActiveTab(activeCategory) {
    const tabButtons = document.querySelectorAll('.settings-tabs-header .btn_vending');

    tabButtons.forEach(btn => {
        // Find the category by checking if the button text matches our translation
        const category = Object.keys(categoryTranslations).find(cat =>
            categoryTranslations[cat] === btn.textContent
        ) || activeCategory;

        if (category === activeCategory) {
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

// Edit a setting value
function editSetting(setting) {
    const valueCell = document.getElementById(`value-cell-${setting.key}`);
    const saveBtn = document.getElementById(`save-btn-${setting.key}`);

    // Create input field
    const input = document.createElement('input');
    if (setting.sensitive) {
        input.type = 'password';
    } else if (setting.type === 'int') {
        input.type = 'number';
    } else if (setting.type === 'bool') {
        input.type = 'checkbox';
        input.checked = setting.value;
    } else {
        input.type = 'text';
    }

    if (setting.type !== 'bool') {
        input.value = setting.value;
    }

    input.id = `input-${setting.key}`;
    input.style.width = '100%';

    valueCell.innerHTML = '';
    valueCell.appendChild(input);

    saveBtn.style.display = 'inline';
}

// Save a setting value
async function saveSetting(settingKey) {
    const input = document.getElementById(`input-${settingKey}`);
    let newValue;

    if (input.type === 'checkbox') {
        newValue = input.checked;
    } else if (input.type === 'number') {
        newValue = parseInt(input.value);
    } else {
        newValue = input.value;
    }

    try {
        const response = await fetch(`../backend/settings/${settingKey}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newValue)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save setting');
        }

        const result = await response.json();
        console.log(`Setting ${settingKey} updated:`, result);

        // Hide save button
        document.getElementById(`save-btn-${settingKey}`).style.display = 'none';

        // Reload settings to reflect changes
        await loadSettingsFromDatabase();

        // Show success message
        alert(`Setting ${settingKey} updated successfully!${result.requires_restart ? ' A restart may be required.' : ''}`);

    } catch (error) {
        console.error('Error saving setting:', error);
        alert(`Failed to save setting: ${error.message}`);
    }
}

// Save all modified settings
async function saveAllSettings() {
    const inputs = document.querySelectorAll('input[id^="input-"]');
    const savePromises = [];
    let hasChanges = false;

    inputs.forEach(input => {
        const settingKey = input.id.replace('input-', '');
        const saveBtn = document.getElementById(`save-btn-${settingKey}`);

        // Only save if the field has been modified (save button is visible)
        if (saveBtn && saveBtn.style.display !== 'none') {
            hasChanges = true;
            savePromises.push(saveSetting(settingKey));
        }
    });

    if (!hasChanges) {
        alert('No changes to save.');
        return;
    }

    try {
        await Promise.all(savePromises);
        alert('All settings saved successfully!');
    } catch (error) {
        console.error('Error saving all settings:', error);
        alert('Error saving settings: ' + error.message);
    }
}



// Export functions for use by HTML (backward compatibility)
window.loadSettingsFromDatabase = loadSettingsFromDatabase;
window.displaySettings = displaySettings;
window.editSetting = editSetting;
window.saveSetting = saveSetting;
window.saveAllSettings = saveAllSettings;

// Делаем функцию доступной глобально
window.initialization = initialization;
