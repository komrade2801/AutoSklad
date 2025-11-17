//import { jsonHistoryDrop } from './init_drop.js';
//import { jsonCellsDrop } from './init_drop.js';
//import { jsonToolForDrop } from './init_drop.js';
import { createCells } from './createCells.js';
import { createToolForDrop } from './createToolForDrop.js'
import { createHistory } from './history_drop.js'

export function deleteDrop(operationKeyToDelete) {
    let jsonHistoryDrop = window.appData.story;
    let jsonToolForDrop = window.appData.tools;
    // Получаем данные об операции, которую нужно удалить
    const operationData = jsonHistoryDrop.operation[operationKeyToDelete];
    if (!operationData) return; // Если вдруг операция не найдена, ничего не делаем

    const { cell, tool, plan } = operationData;
    const cellId = Number(cell);

    // 1. Удаляем запись из jsonHistoryDrop
    const updatedOperations = {};
    let newIndex = 1;
    for (const key of Object.keys(jsonHistoryDrop.operation).sort((a, b) => a - b)) {
        if (key !== operationKeyToDelete) {
            updatedOperations[newIndex++] = jsonHistoryDrop.operation[key];
        }
    }
    jsonHistoryDrop.operation = updatedOperations;
    let jsonCellsDrop = window.appData.cells;
    // 2. Возвращаем инструмент в jsonCellsDrop
    for (const rowKey in jsonCellsDrop.rows) {
        const row = jsonCellsDrop.rows[rowKey];
        for (const cellKey in row.cells) {
            const cellObj = row.cells[cellKey];
            if (cellObj.id == cellId) {
                cellObj.content.tool = tool;
                cellObj.content.plan = plan;

                // Условие цвета ячейки в зависимости от наличия плана
                if (plan === 'None') {
                    cellObj.backgroundColor = '#2C8822'; // зелёный если плана нет
                } else {
                    cellObj.backgroundColor = '#535353'; // оранжевый если план есть
                }
                break;
            }
        }
    }

    // 3. Возвращаем инструмент в jsonToolForDrop
    let toolInserted = false;
    for (const planKey in jsonToolForDrop.plans) {
        if (jsonToolForDrop.plans[planKey].name === plan) {
            const planEntry = jsonToolForDrop.plans[planKey];
            for (const groupKey in planEntry.groups) {
                const groupEntry = planEntry.groups[groupKey];

                // Если нужная группа найдена (иногда может быть больше условий по названию группы, если потребуется)
                groupEntry.value.push({
                    tools: tool,
                    cell: cellId
                });
                toolInserted = true;
                break;
            }
        }
        if (toolInserted) break;
    }

    // Если план не найден (например, его удалили) — можно добавить новый план/группу. (по необходимости)

    // 4. Обновляем интерфейсы
    createCells('cells-container', jsonCellsDrop);
    createToolForDrop('tools-container', jsonToolForDrop);
    createHistory('history', jsonHistoryDrop);
    window.appData.story = jsonHistoryDrop;
}
