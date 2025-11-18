//import { jsonObjectTools } from './init.js';
// Функция для создания строк инструмента на основе JSON-данных
import { updateToolsJSONMass, updateCellsJSON, updateJsonHistory, initializeDragAndDrop } from './drag_and_drop.js';
import { createCells } from './createCells.js';
import { createHistory } from './createHistory.js';
import { jsonObjectHistory } from './init.js';

let currentInputRow = null; // Глобальная переменная для текущей строки с вводом

export function createTools(containerId, jsonObjectTools) {
//    console.log(jsonObjectTools)
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
                if (parseInt(tool.sum) <= 0) continue;
                const toolDiv = document.createElement('div');
                // Устанавливаем флекс-контейнер для строки и класс
                toolDiv.style.display = 'flex';
                toolDiv.style.flexDirection = 'row';
                toolDiv.style.flexWrap = 'nowrap';
                toolDiv.className = 'draggable';
                toolDiv.draggable = "true";
                toolDiv.style.width = '100%';
                toolDiv.style.cursor = 'pointer';
//                toolDiv.content = planData['name'];
                toolDiv.setAttribute('data-tool-id', tool.id);
//                toolDiv.setAttribute('data-plan-name', planData.name);
//                toolDiv.setAttribute('data-group-name', groupData.name);
                toolDiv.setAttribute('data-tool-name', tool.name);
//                toolDiv.setAttribute('data-group-name', groupData.name);
                // Устанавливаем стили для строки инструмента
                toolDiv.style.height = '64px';
                toolDiv.style.alignItems = 'center';
                //Создаем название и количество инструмента
                const nameDiv = document.createElement('div');
                const sumDiv = document.createElement('div');
                // Устанавливаем стили для названия инструмента
                nameDiv.className = 'toolName';
//                nameDiv.textContent = groupData.name + " " + tool.name;
                nameDiv.textContent = tool.name;
                nameDiv.title = tool.description || "Нет описания";
                nameDiv.style.display = 'flex';
                nameDiv.style.width = '100%';
                nameDiv.style.height = '62px';
                nameDiv.style.backgroundColor = '#D3D3D3A0';
                nameDiv.style.border = '1px solid #ffffff';
                nameDiv.style.color = '#003172';
                nameDiv.style.fontWeight = 'bold';
                nameDiv.style.fontSize = '14px';
                nameDiv.style.alignItems = 'stretch';
                nameDiv.style.justifyContent = 'start';
                nameDiv.style.margin = '1px';
                // Добавляем всплывающую подсказку с полным наименованием инструмента
                //nameDiv.title = `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`;
                // Устанавливаем стили для количества инструмента
                sumDiv.textContent = tool.sum;
                sumDiv.className = 'sumTool';
                sumDiv.style.display = 'flex';
                sumDiv.style.width = '35px';
                sumDiv.style.height = '62px';
                sumDiv.style.marginRight = '0px'
                sumDiv.style.border = '1px solid #FFFFFF';
                sumDiv.style.backgroundColor = '#56b358';
                sumDiv.style.alignItems = 'center';
                sumDiv.style.justifyContent = 'center';
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
    inputRow.style.display = 'flex';
    inputRow.style.flexDirection = 'row';
    inputRow.style.width = '100%';
    inputRow.style.height = '32px';
    inputRow.style.alignItems = 'center';

    // Создаем div для поля ввода, копируя стили из nameDiv
    const inputDiv = document.createElement('div');
    inputDiv.className = 'toolName';
    inputDiv.style.display = 'flex';
    inputDiv.style.width = '100%';
    inputDiv.style.height = '30px';
    inputDiv.style.backgroundColor = '#ffffffff';
    inputDiv.style.border = '1px solid #ffffff';
    inputDiv.style.color = '#003172';
    inputDiv.style.fontWeight = 'bold';
    inputDiv.style.fontSize = '14px';
    inputDiv.style.alignItems = 'center';
    inputDiv.style.justifyContent = 'start';
    inputDiv.style.margin = '1px';

    // Входное поле внутри inputDiv
    const input = document.createElement('input');
    input.type = 'number';
    input.min = '0';
    input.value = '0';
    input.step = '1';
    input.pattern = '[0-9]*';
    input.inputMode = 'numeric';
    input.max = valueData.sum.toString();
    input.style.width = '100%';
    input.style.height = '100%';
    input.style.border = 'none';
    input.style.background = 'transparent';
    input.style.color = '#003172';
    input.style.fontWeight = 'bold';
    input.style.fontSize = '14px';
    input.style.textAlign = 'left';

    inputDiv.appendChild(input);

    // Создаем div для кнопки, копируя стили из sumDiv
    const buttonDiv = document.createElement('div');
    buttonDiv.className = 'sumTool';
    buttonDiv.style.display = 'flex';
    buttonDiv.style.width = '35px';
    buttonDiv.style.height = '30px';
    buttonDiv.style.marginRight = '0px';
    buttonDiv.style.border = '1px solid #FFFFFF';
    buttonDiv.style.backgroundColor = '#56b358';
    buttonDiv.style.alignItems = 'center';
    buttonDiv.style.justifyContent = 'center';

    // Кнопка внутри buttonDiv
    const button = document.createElement('button');
    button.textContent = '+';
    button.style.width = '30px';
    button.style.height = '30px';
    button.style.border = 'none';
    button.style.backgroundColor = 'transparent';
    button.style.color = '#ffff'
    button.style.fontWeight = 'bold';
    button.style.fontSize = '16px';
    button.style.cursor = 'pointer';

    buttonDiv.appendChild(button);

    // Обработчик для кнопки +
    button.addEventListener('click', (event) => {
        event.stopPropagation();
        const amount = parseInt(input.value);
        if (validateInput(amount, valueData.sum)) {
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
        updateJsonHistory(window.appData.history, planName, toolId, combinedToolName, parseInt(cell.id), parseInt(cell.number));
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
