// import { jsonObjectTools } from './init.js';
// import { jsonObjectCells } from './init.js';
import { jsonObjectHistory } from './init.js';
import { createTools } from './createTools.js';
import { createCells } from './createCells.js';
import { createHistory } from './createHistory.js';
import { searchCellById } from './searchCellById.js';
import { initializeDragAndDrop } from './drag_and_drop.js';

const BLOCKED_CELL_IDS = new Set([1, 36, 71, 106, 141, 176]);


export function deleteLoad(jsonObjectHistory, jsonObjectCells, jsonObjectTools, planName, toolId, cellId) {
    //console.log(planName)
    //console.log(toolId)
    //console.log(cellId)

    // ИСПРАВЛЕНО: используем window.appData.cells напрямую для гарантии актуальных данных
    const cellsData = window.appData.cells || jsonObjectCells;
    
    // Вносим изменения в ячейку
    const cell = searchCellById(cellId)
    
    if (!cell) {
        console.error(`Cell with id ${cellId} not found`);
        return;
    }

    console.log(`[deleteLoad] Before update - cell ${cellId}:`, {
        backgroundColor: cell.backgroundColor,
        content: cell.content,
        block: cell.block
    });

    cell.content.plan = "None";
    cell.content.tool = "None";

    // ИСПРАВЛЕНО: устанавливаем правильный цвет для пустой ячейки
    // Используем цвет из легенды: #979797 для пустых ячеек
    cell.backgroundColor = '#979797';

    if (!BLOCKED_CELL_IDS.has(Number(cellId))) {
        cell.block = false;
    }

    console.log(`[deleteLoad] After update - cell ${cellId}:`, {
        backgroundColor: cell.backgroundColor,
        content: cell.content,
        block: cell.block
    });

    // Вносим изменения в инструмент: найти по id и увеличить sum
    // ИСПРАВЛЕНО: используем новый формат данных tools.tools вместо plans.groups.value
    let toolFound = false;
    const toolsData = jsonObjectTools.tools || {};
    
    for (const [idx, tool] of Object.entries(toolsData)) {
        if (tool.id == toolId) {
            // ИСПРАВЛЕНО: обрабатываем случаи, когда sum отсутствует или null/undefined
            if (tool.sum === undefined || tool.sum === null) {
                // Для инструментов с бесконечным запасом не изменяем sum
                // (можно оставить как есть или установить специальное значение)
            } else {
                const currentSum = parseInt(tool.sum, 10);
                if (!isNaN(currentSum)) {
                    // Если sum <= 0 (бесконечный запас), не увеличиваем
                    // Иначе увеличиваем на 1
                    if (currentSum > 0) {
                        tool.sum = (currentSum + 1).toString();
                    }
                    // Для бесконечного запаса (sum <= 0) оставляем как есть
                }
            }
            toolFound = true;
            break;
        }
    }

    // Вносим изменения в историю
    // ИСПРАВЛЕНО: используем window.appData.history для гарантии актуальных данных
    const historyData = window.appData.history || jsonObjectHistory;
    if (!historyData.operation) {
        historyData.operation = {};
    }
    
    // ИСПРАВЛЕНО: ищем по operationData.tool, а не operationData.toolId
    let targetIndex = null;

    for (const operationKey in historyData.operation) {
        const operationData = historyData.operation[operationKey];
        // ИСПРАВЛЕНО: используем tool вместо toolId
        if (operationData.cell == cellId && operationData.tool == toolId) {
            targetIndex = parseInt(operationKey, 10); // Сохраняем индекс для удаления
            break;
        }
    }

    if (targetIndex !== null) {
        // Удаляем операцию с указанным индексом
        delete historyData.operation[targetIndex];

        // Сдвигаем оставшиеся индексы на 1 вверх
        for (const operationKey in historyData.operation) {
            var currentKey = parseInt(operationKey, 10);
            if (currentKey > targetIndex) {
                const newKey = (currentKey - 1).toString();
                historyData.operation[newKey] = historyData.operation[operationKey];
                delete historyData.operation[operationKey];
            }
        }
    }
    
    // Обновляем window.appData.history
    window.appData.history = historyData;

    console.log(jsonObjectTools)
    //console.log(toolId)
    //console.log(cellId)
    //console.log("Это конец удаления")
    
    // ИСПРАВЛЕНО: используем window.appData.cells для гарантии актуальных данных
    // Обновляем window.appData.cells для синхронизации
    window.appData.cells = cellsData;
    
    createCells('cells-container', cellsData);
    createTools('tools-container', window.appData.tools || jsonObjectTools);
    createHistory('history', historyData, toolId);
    initializeDragAndDrop();
}
