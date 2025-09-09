//import { jsonHistoryDrop } from './init_drop.js';
//import { jsonCellsDrop } from './init_drop.js';
//import { jsonToolForDrop } from './init_drop.js';
import { createCells } from './createCells.js';
import { createToolForDrop } from './createToolForDrop.js'
import { deleteDrop } from './deleteDrop.js'


// Функция для генерации JSON-History с историей текущей загрузки
export function updateJsonHistoryDrop(jsonHistoryDrop, planName, groupIndex, toolName, cellId) {
    // Убедимся, что jsonHistoryDrop.operation существует
    if (!jsonHistoryDrop.operation) {
        jsonHistoryDrop.operation = {}; // Инициализируем, если это null или undefined
    }

    // Создаем новый объект для операций с новой записью под первым номером
    const newOperation = {
        1: {
            cell: String(cellId), // Преобразуем в строку, чтобы соответствовать образцу
            tool: toolName,
            plan: planName
        }
    };

    // Сдвигаем существующие операции вниз, увеличивая их индексы на 1
    const updatedOperations = Object.fromEntries(
        Object.entries(jsonHistoryDrop.operation).map(([key, value]) => [Number(key) + 1, value])
    );

    // Объединяем новую операцию и сдвинутые операции
    jsonHistoryDrop.operation = { ...newOperation, ...updatedOperations };

    createHistory('history', jsonHistoryDrop);
}


function handleUnloadClick(button) {
    const cellId = button.dataset.cellId;
    const toolName = button.dataset.toolName;
    const planName = button.dataset.planName;
    let jsonCellsDrop = window.appData.сells;
    let jsonToolForDrop = window.appData.tools;
    let jsonHistoryDrop = window.appData.story;

    // Ничего не делаем, если содержимое пустое
    if (toolName === 'None') return;

    // Если у тебя есть способ определить groupIndex — добавь сюда.
    // Пока поставим заглушку:
    const groupIndex = null;

    updateJsonHistoryDrop(jsonHistoryDrop, planName, groupIndex, toolName, cellId);

    // Находим нужную ячейку в jsonCellsDrop и обнуляем содержимое
    //let jsonObjectCellsDrop = window.appData.cellsDrop;
    for (const rowKey in jsonCellsDrop.rows) {
        const row = jsonCellsDrop.rows[rowKey];
        for (const cellKey in row.cells) {
            const cell = row.cells[cellKey];
            if (cell.id == cellId) {
                cell.content.tool = "None";
                cell.content.plan = "None";
                cell.backgroundColor = "#69696910";
                break;
            }
        }
    }

    // Убираем инструмент из jsonToolForDrop, НЕ трогая группы и планы
    for (const planKey in jsonToolForDrop.plans) {
        const plan = jsonToolForDrop.plans[planKey];
        for (const groupKey in plan.groups) {
            const group = plan.groups[groupKey];
            group.value = group.value.filter(item => item.cell !== Number(cellId));
        }
    }

    createCells('cells-container', jsonCellsDrop);
    createToolForDrop('tools-container', jsonToolForDrop);

    show('none');
}

window.handleUnloadClick = handleUnloadClick;



// Функция для создания строк истории на основе JSON-данных
export function createHistory(containerId, jsonHistoryDrop) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек

    // Проходим по строкам в JSON
    for (const operationKey in jsonHistoryDrop.operation) {
        const operationData = jsonHistoryDrop.operation[operationKey];


        // Генерируем контейнер для одной операции в истории
        const operationDiv = document.createElement('div');

        // Устанавливаем стили для строки операции
        operationDiv.style.display = 'flex';
        operationDiv.style.flexDirection = 'row';
        operationDiv.style.flexWrap = 'nowrap';
        operationDiv.style.height = '32px';
        operationDiv.style.alignItems = 'center';

        //Создаем название и номер ячейки
        const nameDiv = document.createElement('div');
        const cellDiv = document.createElement('div');

        // Устанавливаем стили для названия инструмента
        nameDiv.textContent = operationData.tool;
        //nameDiv.setAttribute('data-group-index', groupIndex);
        nameDiv.style.display = 'flex';
        nameDiv.style.width = '100%';
        nameDiv.style.height = '30px';
        nameDiv.style.backgroundColor = '#D3D3D3A0';
        nameDiv.style.border = '1px solid #ffffff';
        nameDiv.style.color = '#003172';
        nameDiv.style.fontWeight = 'bold';
        nameDiv.style.fontSize = '14px';
        nameDiv.style.alignItems = 'center';
        nameDiv.style.justifyContent = 'start';
        nameDiv.style.margin = '1px';

        // Устанавливаем стили для номера ячейки
        cellDiv.textContent = operationData.cell;
        cellDiv.style.display = 'flex';
        cellDiv.style.width = '52px';
        cellDiv.style.height = '30px';
        cellDiv.style.marginRight = '1px';
        cellDiv.style.border = '1px solid #FFFFFF';
        cellDiv.style.backgroundColor = '#56b358';
        cellDiv.style.alignItems = 'center';
        cellDiv.style.justifyContent = 'center';


        //Создаём значок чертежа со всплывающей подсказкой
        const planDiv = document.createElement('div');

        //Устанавливаем стили для чертежа
        planDiv.style.display = 'flex';
        planDiv.style.width = '30px';
        planDiv.style.height = '30px';
        planDiv.style.marginRight = '1px';
        planDiv.style.border = '1px solid #FFFFFF';
        planDiv.style.backgroundColor = '#56b358';
        planDiv.style.alignItems = 'center';
        planDiv.style.justifyContent = 'center';

        //Добавляем изображение иконки
        const planImage = document.createElement('img');
        planImage.src = '../assets/img/btn_info.png';
        planImage.style.width = '20px';
        planImage.style.height = '20px';
        planImage.style.objectFit = 'contain'; // Сохраняем пропорции
        planDiv.appendChild(planImage);

        //Добавляем всплывающую подсказку
        planDiv.setAttribute('data-tooltipPlan', `Чертёж: ${operationData.plan}`);


        //Создаём кнопку для удаления операции
        const deleteButton = document.createElement('button');
        deleteButton.onclick = function() {
            deleteDrop(operationKey);
        };


        //Устанавливаем стили для кнопки удаления (кнопка с крестиком)
        deleteButton.style.width = '30px';
        deleteButton.style.height = '30px';
        deleteButton.style.marginRight = '1px'
        deleteButton.style.border = '1px solid #FFFFFF';
        deleteButton.style.backgroundColor = '#56b358';
        deleteButton.style.display = 'flex';
        deleteButton.style.alignItems = 'center';
        deleteButton.style.justifyContent = 'center';

        //Добавляем иконку на кнопку
        const deleteIcon = document.createElement('img');
        deleteIcon.src = '../assets/img/btn_cross_2.png';
        deleteIcon.style.width = '20px'; // Размер иконки
        deleteIcon.style.height = '20px';
        deleteIcon.style.pointerEvents = 'none'; // Отключаем обработку кликов на изображении
        deleteButton.appendChild(deleteIcon);


        // Добавляем все составляющие в строку инструмента
        operationDiv.appendChild(nameDiv);
        operationDiv.appendChild(cellDiv);
        operationDiv.appendChild(planDiv);
        operationDiv.appendChild(deleteButton);
        //operationDiv.appendChild(confirmDiv);

        container.appendChild(operationDiv); // Добавляем строку в контейнер
    }
    
    window.appData.story = jsonHistoryDrop;
}