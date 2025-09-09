import { jsonObjectTools } from './init.js';
import { jsonObjectCells } from './init.js';
import { jsonObjectHistory } from './init.js';
import { createTools } from './createTools.js';
import { createCells } from './createCells.js';
import { createHistory } from './createHistory.js';
import { searchCellById } from './searchCellById.js';
import { initializeDragAndDrop } from './drag_and_drop.js';


export function deleteLoad(jsonObjectHistory, jsonObjectCells, jsonObjectTools, planName, groupIndex, toolName, cellId) {
    //console.log(planName)
    //console.log(toolName)
    //console.log(cellId)

    // Вносим изменения в ячейку
    const cell = searchCellById(cellId)

    cell.content.plan = "None";
    cell.content.tool = "None";

    cell.backgroundColor = '#69696910';

    cell.block = false;


    // Вносим изменения в инструмент
    // Перебираем все планы в JSON
    for (const planKey in jsonObjectTools.plans) {
        const plan = jsonObjectTools.plans[planKey];

        // Проверяем совпадение имени плана
        if (plan.name == planName) {
            const group = plan.groups[groupIndex];
            let toolFound = false; // Флаг для отслеживания, найден ли инструмент

            // Группа с заданным индексом существует, выполняем логику
            for (const valueKey in group.value) {
                const value = group.value[valueKey];

                // Проверяем совпадение инструмента
                if (value.tools == toolName) {
                    // Увеличиваем sum на 1, если совпадение найдено
                    value.sum = (parseInt(value.sum, 10) + 1).toString();
                    toolFound = true; // Устанавливаем флаг, что инструмент найден
                    break; // Прерываем цикл, так как инструмент найден
                    //return jsonObjectTools;
                }
            }

            if (!toolFound) {
            // Если совпадение инструмента не найдено, добавляем новый
                const newToolIndex = (Math.max(...Object.keys(group.value).map(Number)) + 1).toString();
                group.value[newToolIndex] = {
                    tools: toolName,
                    sum: "1"
                };
            }
        }
    }


    // Вносим изменения в историю
    // Ищем индекс операции, которую нужно удалить
    let targetIndex = null;

    for (const operationKey in jsonObjectHistory.operation) {
        const operationData = jsonObjectHistory.operation[operationKey];
        if ( operationData.cell == cellId) {
            targetIndex = parseInt(operationKey, 10); // Сохраняем индекс для удаления
            break;
        }
    }
//console.log("после брейка")
    if (targetIndex !== null) {
        // Удаляем операцию с указанным индексом
        delete jsonObjectHistory.operation[targetIndex];

        // Сдвигаем оставшиеся индексы на 1 вверх
        //const updatedOperations = {};
        //let newIndex = 1;

        for (const operationKey in jsonObjectHistory.operation) {
            var currentKey = parseInt(operationKey, 10);
            if (currentKey > targetIndex) {
                currentKey = currentKey -= 1;
                String(currentKey);
            }
        }
    }

    console.log(jsonObjectTools)
    //console.log(toolName)
    //console.log(cellId)
    //console.log("Это конец удаления")
    createCells('cells-container', jsonObjectCells);
    createTools('tools-container', jsonObjectTools);
    createHistory('history', jsonObjectHistory, groupIndex);
    initializeDragAndDrop();
}