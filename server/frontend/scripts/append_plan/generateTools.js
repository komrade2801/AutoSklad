//import { createHistory } from './createHistory.js';
import { updateJsonHistoryLoad, createHistory } from './selected_tools.js';

// Функция для создания строк инструмента на основе JSON-данных
export function generateTools() {
    console.log('generateTools');
    console.log(window.appData.tools);
//    const container = document.getElementById(containerId);
//    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек

    if (window.appData.tools != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#loadable_tools_table').bootstrapTable('load', window.appData.tools);
        $('#loadable_tools_table').bootstrapTable('hideLoading');
    }
    return;
}

// Функция для массовой загрузки
function performMassLoad(toolId, toolName, toolSum, amount) {

    console.log(`🔄 Starting mass load: ${amount} "${toolName}" "`);
//    console.log('📊 Pre-load tool inventory state:', getToolInventoryState());

//    const freeCells = getFreeCells();

    var currentLoadAmount = 0;

    if (window.appData.history.operation) {
        currentLoadAmount = Object.keys(window.appData.history.operation).length;
    } else {
        currentLoadAmount = 0;
    }

    console.log(`✅ Loading ${amount} tools into cells`);

    // Ничего не делаем, если содержимое пустое
    if (toolName === 'None') return;

    // Убедимся, что window.appData.history.operation существует
    if (!window.appData.history.operation) {
        window.appData.history.operation = {}; // Инициализируем, если это null или undefined
    }

    // create new operation in history

//    const newKey = Object.keys(window.appData.history.operation).length + 1;

    const operation = window.appData.history.operation[toolId];
    var newAmount = amount;

    if (operation) {
        newAmount += operation.quantity;
    }

    window.appData.history.operation[toolId] = {
        id: toolId,
        name: toolName,
        quantity: newAmount
    }

    updateJsonHistoryLoad();

    for (var i = 0; i < amount; i++) {
        updateToolsJSONMass(toolId, 1);
    }

//    console.log('📊 Post-load tool inventory state:', getToolInventoryState());
//    console.log('📝 Current load history state:', getHistoryState());
    console.log('📝 Final window.appData.history:', window.appData.history);

    // Обновляем UI
    generateTools();
    createHistory();
//    initializeDragAndDrop();

}

window.performMassLoad = performMassLoad;

function updateToolsJSONMass(toolId, subtractAmount) {
    console.log("updateToolsJSONMass успешно вызвана");

    const tool = findToolById(toolId);

    if (!tool) {
        console.error("Tool not found for id:", toolId);
        return;
    }

    // ИСПРАВЛЕНО: обрабатываем случаи, когда sum отсутствует или null/undefined
    if (tool.sum === undefined || tool.sum === null) {
        // Для инструментов с бесконечным запасом не уменьшаем sum
        // (можно оставить как есть или установить специальное значение)
        return;
    }

    // Для бесконечного запаса не изменяем sum
    const currentSum = parseInt(tool.sum, 10);
    if (isNaN(currentSum) || currentSum < 0) {
        console.warn(`Invalid sum value for tool ${toolId}:`, tool.sum);
        return;
    }

    // Уменьшаем значение sum на указанное количество
    const newSum = currentSum - subtractAmount;
    // Не позволяем sum стать отрицательным (должно быть >= 0)
    tool.sum = Math.max(0, newSum).toString();

    // Обновляем отображение элементов на странице
    createTools();
//    initializeDragAndDrop();
}

// Функция для поиска инструмента по ID
function findToolById(toolId) {
    for (const [idx, tool] of Object.entries(window.appData.tools)) {
        if (tool.id == toolId) {
            return tool;
        }
    }
    return null;
}