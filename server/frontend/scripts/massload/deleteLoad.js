// import { jsonObjectTools } from './init.js';
// import { jsonObjectCells } from './init.js';
import { jsonObjectHistory } from './init.js';
import { createTools } from './createTools.js';
import { createCells } from './createCells.js';
import { createHistory } from './createHistory.js';
import { searchCellById } from './searchCellById.js';
import { initializeDragAndDrop } from './drag_and_drop.js';


export function deleteLoad(jsonObjectHistory, jsonObjectCells, jsonObjectTools, planName, toolId, cellId) {
    //console.log(planName)
    //console.log(toolId)
    //console.log(cellId)

    // Вносим изменения в ячейку
    const cell = searchCellById(cellId)

    cell.content.plan = "None";
    cell.content.tool = "None";

    cell.backgroundColor = '#69696910';

    cell.block = false;

    // Вносим изменения в инструмент: найти по id и увеличить sum
    let toolFound = false;
    for (const planKey in jsonObjectTools.plans) {
        const plan = jsonObjectTools.plans[planKey];
        for (const groupKey in plan.groups) {
            const group = plan.groups[groupKey];
            for (const valueKey in group.value) {
                const value = group.value[valueKey];
                if (value.id == toolId) {
                    value.sum = (parseInt(value.sum, 10) + 1).toString();
                    toolFound = true;
                    break;
                }
            }
            if (toolFound) break;
        }
        if (toolFound) break;
    }

    // Вносим изменения в историю
    // Ищем индекс операции, которую нужно удалить
    let targetIndex = null;

    for (const operationKey in jsonObjectHistory.operation) {
        const operationData = jsonObjectHistory.operation[operationKey];
        if (operationData.cell == cellId && operationData.tool == toolId) {
            targetIndex = parseInt(operationKey, 10); // Сохраняем индекс для удаления
            break;
        }
    }

    if (targetIndex !== null) {
        // Удаляем операцию с указанным индексом
        delete jsonObjectHistory.operation[targetIndex];

        // Сдвигаем оставшиеся индексы на 1 вверх
        for (const operationKey in jsonObjectHistory.operation) {
            var currentKey = parseInt(operationKey, 10);
            if (currentKey > targetIndex) {
                const newKey = (currentKey - 1).toString();
                jsonObjectHistory.operation[newKey] = jsonObjectHistory.operation[operationKey];
                delete jsonObjectHistory.operation[operationKey];
            }
        }
    }

    console.log(jsonObjectTools)
    //console.log(toolId)
    //console.log(cellId)
    //console.log("Это конец удаления")
    createCells('cells-container', jsonObjectCells);
    createTools('tools-container', jsonObjectTools);
    createHistory('history', jsonObjectHistory, toolId);
    initializeDragAndDrop();
}
