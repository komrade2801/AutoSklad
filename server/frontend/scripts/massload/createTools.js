//import { jsonObjectTools } from './init.js';
// Функция для создания строк инструмента на основе JSON-данных
//import { createHistory } from './createHistory.js';
import { updateJsonHistoryLoad, createHistory } from './history_load.js';

//let currentInputRow = null; // Глобальная переменная для текущей строки с вводом

// Вспомогательная функция для подсчета общего количества инструментов к загрузке
function getTotalToolsToLoad() {
    if (!window.appData.history || !window.appData.history.operation) {
        return 0;
    }
    return Object.values(window.appData.history.operation)
        .reduce((total, operation) => total + operation.sum, 0);
}

// Делаем функцию доступной глобально
window.getTotalToolsToLoad = getTotalToolsToLoad;

export function createTools() {
    if (window.appData.tools != undefined) {
        // Заменяем "-" на символ бесконечности перед загрузкой в таблицу
        const processedTools = window.appData.tools.map(tool => ({
            ...tool,
            sum: (tool.sum === '-' || tool.count === 0 || tool.count === '-') ? '∞' : (tool.sum || tool.count)
        }));

        $('#loadable_tools_table').bootstrapTable('load', processedTools);
        $('#loadable_tools_table').bootstrapTable('hideLoading');
    }
}

// Функция для массовой загрузки
function performMassLoad(toolId, toolName, toolSum, amount) {

    console.log(`🔄 Starting mass load: ${amount} "${toolName}" "`);
//    console.log('📊 Pre-load tool inventory state:', getToolInventoryState());

//    const freeCells = getFreeCells();

    const currentLoadAmount = getTotalToolsToLoad();

    if (window.appData.freeCells < amount + currentLoadAmount) {
        console.warn(`❌ Mass load failed: Requested ${amount} cells, only ${window.appData.freeCells} free cells available`);
        alert('Не хватает свободных ячеек.');
        return;
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
        newAmount += operation.sum;
    }

    window.appData.history.operation[toolId] = {
        tool: toolId,
        name: toolName,
        plan: null,
        sum: newAmount
    }

    updateJsonHistoryLoad();

    for (var i = 0; i < amount; i++) {
        updateToolsJSONMass(toolId, 1);
    }

//    console.log('📊 Post-load tool inventory state:', getToolInventoryState());
//    console.log('📝 Current load history state:', getHistoryState());
    console.log('📝 Final window.appData.history:', window.appData.history);

    // Обновляем UI
    createTools();
    createHistory();
//    initializeDragAndDrop();

//    // Закрываем строку ввода
//    closeCurrentInputRow();
}

window.performMassLoad = performMassLoad;

// Функция для получения свободных ячеек
function getFreeCells() {
    const jsonObjectCells = window.appData.cells;
    const free = [];
    for (const rowKey in jsonObjectCells.rows) {
        const row = jsonObjectCells.rows[rowKey];
        for (const cellKey in row.cells) {
            const cell = row.cells[cellKey];
            if (!cell.block) {
                free.push({'id':cell.id, 'number':cell.number});
            }
        }
    }
    return free.sort((a, b) => a.id - b.id); // Сортировка по id по возрастанию
}

// Функция для получения текущего состояния инвентаря инструментов
function getToolInventoryState() {
    const tools = window.appData.tools;
    const inventory = {};

    for (const planKey in tools.plans) {
        const plan = tools.plans[planKey];
        inventory[plan.name] = {};

        for (const groupKey in plan.groups) {
            const group = plan.groups[groupKey];
            inventory[plan.name][group.name] = {};

            for (const toolKey in group.value) {
                const tool = group.value[toolKey];
                inventory[plan.name][group.name][tool.name] = tool.sum;
            }
        }
    }

    return inventory;
}

// Функция для получения текущего состояния истории загрузки
function getHistoryState() {
    const history = window.appData.history;
    if (!history || !history.operation) {
        return { totalOperations: 0, operations: {} };
    }

    const operationsList = Object.keys(history.operation).map(key => ({
        index: key,
        cell: history.operation[key].cell,
        tool: history.operation[key].tool,
        plan: history.operation[key].plan
    }));

    return {
        totalOperations: operationsList.length,
        operations: operationsList
    };
}

// Функция для закрытия текущей строки ввода
function closeCurrentInputRow() {
    if (currentInputRow) {
        currentInputRow.remove();
        currentInputRow = null;
    }
}

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

function deleteLoad(toolId) {

    // Вносим изменения в инструмент: найти по id и увеличить sum
    // ИСПРАВЛЕНО: используем новый формат данных tools.tools вместо plans.groups.value

    if (toolId !== null) {
        // Удаляем операцию с указанным индексом
        const operation = window.appData.history.operation[toolId];
        delete window.appData.history.operation[toolId];

        updateToolsJSONMass(toolId, -operation.sum);
    }

    updateJsonHistoryLoad();
    createTools();
    createHistory();
}
window.deleteLoad = deleteLoad;