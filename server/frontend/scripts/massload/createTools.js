//import { jsonObjectTools } from './init.js';
// Функция для создания строк инструмента на основе JSON-данных
import { updateToolsJSONMass, updateCellsJSON, updateJsonHistory, initializeDragAndDrop } from './drag_and_drop.js';
import { createCells } from './createCells.js';
import { createHistory } from './createHistory.js';
import { jsonObjectHistory } from './init.js';

let currentInputRow = null; // Глобальная переменная для текущей строки с вводом

export function createTools(containerId, jsonObjectTools) {
    console.log('createTools');
    console.log(jsonObjectTools.tools);
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек
    // Проходим по строкам в JSON
//    for (const planKey in jsonObjectTools.plans) {
//        const planData = jsonObjectTools.plans[planKey];
//        for (const groupKey in planData.groups) {
//            const groupData = planData.groups[groupKey];
//            // Проходим по ячейкам в строке
//            for (const valueKey in groupData.value) {
//                const valueData = groupData.value[valueKey];
    for (const [idx, tool] of Object.entries(jsonObjectTools.tools)) {
//    console.log(idx + ' - ' + tool)
                // Пропускаем инструменты с sum <= 0
                var count = parseInt(tool.sum);
                if (count <= 0) {
                    count = '-'
                }
                const toolDiv = document.createElement('div');
                // Устанавливаем флекс-контейнер для строки и класс
                toolDiv.className = 'draggable library-tool-div';
                toolDiv.draggable = "true";
//                toolDiv.content = planData['name'];
                toolDiv.setAttribute('data-tool-id', tool.id);
//                toolDiv.setAttribute('data-plan-name', planData.name);
//                toolDiv.setAttribute('data-group-name', groupData.name);
                toolDiv.setAttribute('data-tool-name', tool.name);
//                toolDiv.setAttribute('data-group-name', groupData.name);
                // Устанавливаем стили для строки инструмента
                //Создаем название и количество инструмента
                const nameDiv = document.createElement('div');
                const sumDiv = document.createElement('div');
                // Устанавливаем стили для названия инструмента
                nameDiv.className = 'toolName';
//                nameDiv.textContent = groupData.name + " " + tool.name;
                nameDiv.textContent = tool.name;
                nameDiv.title = tool.name || "Нет описания";
                nameDiv.className = 'library-tool-name-div';
                // Добавляем всплывающую подсказку с полным наименованием инструмента
                //nameDiv.title = `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`;
                // Устанавливаем стили для количества инструмента
                sumDiv.textContent = count;
                sumDiv.className = 'sumTool library-tool-sum-div';
                // Добавляем название и количество в строку инструмента
                toolDiv.appendChild(nameDiv);
                toolDiv.appendChild(sumDiv);

                // Добавляем обработчик клика для массовой загрузки
                toolDiv.addEventListener('click', (event) => {
                    event.stopPropagation(); // Предотвращаем bubble
                    openMassLoadInput(toolDiv, tool, '', tool.id, '', tool.name);
                });

                container.appendChild(toolDiv); // Добавляем строку в контейнер
//            }
//        }
    }
}

// Функция для открытия строки ввода массовой загрузки
function openMassLoadInput(toolDiv, valueData, planName, toolId, groupName, toolName) {
    // Закрываем предыдущую строку ввода, если есть
    closeCurrentInputRow();

    // Создаем новую строку ввода
    const inputRow = document.createElement('div');
    inputRow.className = 'library-tool-row';

    // Создаем div для поля ввода, копируя стили из nameDiv
    const inputDiv = document.createElement('div');
    inputDiv.className = 'toolName library-tool-input-div';

    // Входное поле внутри inputDiv
    const input = document.createElement('input');
    input.type = 'number';
    input.min = '0';
    input.value = '0';
    input.step = '1';
    input.pattern = '[0-9]*';
    input.inputMode = 'numeric';
    var max = valueData.sum;
    if (max <= 0) {
        max = 99999999;
    }
    input.max = max.toString();
    input.className = 'library-tool-input';

    inputDiv.appendChild(input);

    // Создаем div для кнопки, копируя стили из sumDiv
    const buttonDiv = document.createElement('div');
    buttonDiv.className = 'sumTool library-tool-button-div';

    // Кнопка внутри buttonDiv
    const button = document.createElement('button');
    button.className = 'sumTool library-tool-button';
    button.textContent = '+';

    buttonDiv.appendChild(button);

    // Обработчик для кнопки +
    button.addEventListener('click', (event) => {
        event.stopPropagation();
        const amount = parseInt(input.value);
        if (validateInput(amount, max)) {
            performMassLoad(amount, planName, toolId, groupName, toolName);
        }
    });

    inputRow.appendChild(inputDiv);
    inputRow.appendChild(buttonDiv);

    // Вставляем строку после toolDiv
    toolDiv.parentNode.insertBefore(inputRow, toolDiv.nextSibling);

    // Фокус на input
    input.focus();

    currentInputRow = inputRow;

    // Добавляем глобальные обработчики для закрытия
    const handleClickOutside = (event) => {
        if (currentInputRow && !currentInputRow.contains(event.target) && !currentInputRow.parentNode.contains(event.target)) {
            closeCurrentInputRow();
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('contextmenu', handleRMB);
            window.removeEventListener('keydown', handleEsc);
        }
    };

    const handleRMB = (event) => {
        if (currentInputRow) {
            event.preventDefault(); // Prevent context menu
            closeCurrentInputRow();
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('contextmenu', handleRMB);
            window.removeEventListener('keydown', handleEsc);
        }
    };

    const handleEsc = (event) => {
        if (event.key === 'Escape' && currentInputRow) {
            closeCurrentInputRow();
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('contextmenu', handleRMB);
            window.removeEventListener('keydown', handleEsc);
        }
    };

    // Задержка для предотвращения немедленного срабатывания
    setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('contextmenu', handleRMB);
        window.addEventListener('keydown', handleEsc);
    }, 0);
}

// Функция валидации ввода
function validateInput(value, maxSum) {
    if (!Number.isInteger(value) || value <= 0 || value > maxSum) {
        alert('Введено некорректное число. Должно быть целое положительное число, не превышающее доступное количество.');
        return false;
    }
    return true;
}

// Функция для массовой загрузки
function performMassLoad(amount, planName, toolId, groupName, toolName) {

    const combinedToolName = toolName;

    console.log(`🔄 Starting mass load: ${amount} units of "${combinedToolName}" for plan "${planName}"`);
    console.log('📊 Pre-load tool inventory state:', getToolInventoryState());

    const freeCells = getFreeCells();
    if (freeCells.length < amount) {
        console.warn(`❌ Mass load failed: Requested ${amount} cells, only ${freeCells.length} free cells available`);
        alert('Не хватает свободных ячеек.');
        return;
    }

    const cellsToLoad = freeCells.slice(0, amount);
    console.log(`✅ Loading ${cellsToLoad.length} tools into cells: [${cellsToLoad.join(', ')}]`);

    console.log(cellsToLoad)
    cellsToLoad.forEach((cell, index) => {
        console.log(`   ${index + 1}. Loading "${combinedToolName}" into cell #${cell.id}`);
        // Имитируем выборку инструмента (уменьшаем sum на 1)
        updateToolsJSONMass(window.appData.tools, toolId, 1);
        updateCellsJSON(window.appData.cells, planName, combinedToolName, parseInt(cell.id));
        updateJsonHistory(window.appData.history, 0, toolId, combinedToolName, parseInt(cell.id), parseInt(cell.number));
    });

    console.log('📊 Post-load tool inventory state:', getToolInventoryState());
    console.log('📝 Current load history state:', getHistoryState());
    console.log('📝 Final window.appData.history:', window.appData.history);
    console.log('window.appData.history === init.companyHistory:', window.appData.history === jsonObjectHistory);

    // Обновляем UI
    createTools('tools-container', window.appData.tools);
    createCells('cells-container', window.appData.cells);
    createHistory('history', window.appData.history, toolId);
    initializeDragAndDrop();

    // Закрываем строку ввода
    closeCurrentInputRow();
}

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
