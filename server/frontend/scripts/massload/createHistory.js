// import { jsonObjectTools } from './init.js';
// import { jsonObjectCells } from './init.js';
import { deleteLoad } from './deleteLoad.js';

// Функция для создания строк истории на основе JSON-данных
export function createHistory(containerId, jsonObjectHistory, groupIndex) {
    let jsonObjectCells = window.appData.сells
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек
    // Проходим по строкам в JSON
    for (const operationKey in jsonObjectHistory.operation) {
        const operationData = jsonObjectHistory.operation[operationKey];

        // Parse tool to group and tool name
        const toolParts = operationData.tool.split(' ');
        const groupName = toolParts[0];
        const toolName = toolParts.slice(1).join(' ');

        // Find description from tools data
        let toolDescription = "Нет описания";
        const toolsData = window.appData.tools;
        outer: for (const planKey in toolsData.plans) {
            const plan = toolsData.plans[planKey];
            for (const gKey in plan.groups) {
                const group = plan.groups[gKey];
                if (group.name !== groupName) continue;
                for (const vKey in group.value) {
                    const val = group.value[vKey];
                    if (val.name === toolName) {
                        toolDescription = val.description || "Нет описания";
                        break outer;
                    }
                }
            }
        }
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
        nameDiv.title = toolDescription;
        nameDiv.setAttribute('data-group-index', groupIndex);
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
        // Создаём скрытые кнопки "Удалить" и "Отмена"
        const confirmDiv = document.createElement('div');
        confirmDiv.style.display = 'none';
        confirmDiv.style.flexDirection = 'row';
        confirmDiv.style.zIndex = '10';
        confirmDiv.style.width = '100%';
        // Стили для уточнающей кнопки "Удалить"
        const confirmDeleteButton = document.createElement('button');
        confirmDeleteButton.textContent = 'Удалить';
        confirmDeleteButton.style.width = '50%';
        confirmDeleteButton.style.height = '30px';
        confirmDeleteButton.style.backgroundColor = '#FF5248';
        confirmDeleteButton.style.border = '2px solid #003172';
        confirmDeleteButton.style.color = '#003172';
        confirmDeleteButton.style.fontWeight = 'bold';
        confirmDeleteButton.style.fontSize = '14px';
        confirmDeleteButton.style.alignItems = 'center';
        confirmDeleteButton.style.justifyContent = 'center';
        confirmDeleteButton.style.margin = '1px';
        // Стили для уточнающей кнопки "Отмена"
        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Отмена';
        cancelButton.style.width = '50%';
        cancelButton.style.height = '30px';
        cancelButton.style.backgroundColor = '#56b358';
        cancelButton.style.border = '2px solid #003172';
        cancelButton.style.color = '#003172';
        cancelButton.style.fontWeight = 'bold';
        cancelButton.style.fontSize = '14px';
        cancelButton.style.alignItems = 'center';
        cancelButton.style.justifyContent = 'center';
        cancelButton.style.margin = '1px';
        confirmDiv.appendChild(confirmDeleteButton);
        confirmDiv.appendChild(cancelButton);
        // Добавляем обработчик события для deleteButton
        deleteButton.addEventListener('click', () => {
            nameDiv.style.display = 'none';
            cellDiv.style.display = 'none';
            planDiv.style.display = 'none';
            deleteButton.style.display = 'none';
            confirmDiv.style.display = 'flex';
        });
        // Добавляем обработчики событий для скрытых кнопок
        cancelButton.addEventListener('click', () => {
            nameDiv.style.display = 'flex';
            cellDiv.style.display = 'flex';
            planDiv.style.display = 'flex';
            deleteButton.style.display = 'flex';
            confirmDiv.style.display = 'none';
        });
        // Вызываем функцию редактирования JSON-файлов
        confirmDeleteButton.addEventListener('click', () => {
            const planName = operationData.plan; // Значение из JSON
            const toolName = operationData.tool; // Значение из nameDiv
            const cellId = operationData.cell;  // Значение из cellDiv
            // Вызов функции deleteLoad с нужными параметрами
            // jsonObjectTools = window.appData.tools
            deleteLoad(jsonObjectHistory, jsonObjectCells, window.appData.tools, planName, groupIndex, toolName, cellId);
        });
        // Добавляем все составляющие в строку инструмента
        operationDiv.appendChild(nameDiv);
        operationDiv.appendChild(cellDiv);
        operationDiv.appendChild(planDiv);
        operationDiv.appendChild(deleteButton);
        operationDiv.appendChild(confirmDiv);
        container.appendChild(operationDiv); // Добавляем строку в контейнер
    }
}
