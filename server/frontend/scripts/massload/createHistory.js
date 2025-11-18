// import { jsonObjectTools } from './init.js';
// import { jsonObjectCells } from './init.js';
import { deleteLoad } from './deleteLoad.js';

// Функция для создания строк истории на основе JSON-данных
export function createHistory(containerId, jsonObjectHistory, groupIndex) {
    let jsonObjectCells = window.appData.cells
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек
    // Проходим по строкам в JSON
    for (const operationKey in jsonObjectHistory.operation) {
        const operationData = jsonObjectHistory.operation[operationKey];

        console.log(operationData)

        // Find tool by id
        let toolDescription = "Нет описания";
        let groupName = "Unknown";
        let toolName = operationData.tool;
        const toolsData = window.appData.tools;

        if (operationData.tool) {
            for (const [idx, tool] of Object.entries(toolsData.tools)) {
                if (tool.id == operationData.tool) {
                    toolDescription = tool.description || "Нет описания";
                    groupName = '';
                    toolName = tool.toolName || tool.name;
                    break;
                }
            }
        } else {
            for (const [idx, tool] of Object.entries(toolsData.tools)) {
                if (tool.id == operationData.tool) {
                    toolDescription = tool.description || "Нет описания";
                    groupName = '';
                    toolName = tool.toolName || tool.name;
                    break;
                }
            }
        }

//        if (operationData.toolId) {
//            outer: for (const planKey in toolsData.plans) {
//                const plan = toolsData.plans[planKey];
//                for (const gKey in plan.groups) {
//                    const group = plan.groups[gKey];
//                    for (const vKey in group.value) {
//                        const val = group.value[vKey];
//                        if (val.id == operationData.toolId) {
//                            toolDescription = val.description || "Нет описания";
//                            groupName = group.name;
//                            toolName = val.toolName || val.name;
//                            break outer;
//                        }
//                    }
//                }
//            }
//        } else {
//            // Fallback to old parsing
//            const toolParts = operationData.tool.split(' ');
//            groupName = toolParts[0];
//            toolName = toolParts.slice(1).join(' ');
//            outer: for (const planKey in toolsData.plans) {
//                const plan = toolsData.plans[planKey];
//                for (const gKey in plan.groups) {
//                    const group = plan.groups[gKey];
//                    if (group.name !== groupName) continue;
//                    for (const vKey in group.value) {
//                        const val = group.value[vKey];
//                        if (val.name === toolName) {
//                            toolDescription = val.description || "Нет описания";
//                            break outer;
//                        }
//                    }
//                }
//            }
//        }
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
        nameDiv.className = 'history-tool-name';
        nameDiv.textContent = toolName;
        nameDiv.title = toolDescription;
        nameDiv.setAttribute('data-group-index', groupIndex);
        // Устанавливаем стили для номера ячейки
        cellDiv.className = 'history-tool-cell';
        cellDiv.textContent = operationData.cell;
        //Создаём значок чертежа со всплывающей подсказкой
        const planDiv = document.createElement('div');
        //Устанавливаем стили для чертежа
        planDiv.className = 'history-tool-plan';
        //Добавляем изображение иконки
        const planImage = document.createElement('img');
        planImage.src = '../assets/img/btn_info.png';
        planImage.className = 'history-tool-plan-image';
        planDiv.appendChild(planImage);
        //Добавляем всплывающую подсказку
        planDiv.setAttribute('data-tooltipPlan', `Чертёж: ${operationData.plan}`);
        //Создаём кнопку для удаления операции
        const deleteButton = document.createElement('button');
        //Устанавливаем стили для кнопки удаления (кнопка с крестиком)
        deleteButton.className = "tool-delete-button";
        //Добавляем иконку на кнопку
        const deleteIcon = document.createElement('img');
        deleteIcon.src = '../assets/img/btn_cross_2.png';
        deleteIcon.className = "tool-delete-button-icon";
        deleteButton.appendChild(deleteIcon);
        // Создаём скрытые кнопки "Удалить" и "Отмена"
        const confirmDiv = document.createElement('div');
        confirmDiv.className = "tool-hidden-buttons";
        // Стили для уточнающей кнопки "Удалить"
        const confirmDeleteButton = document.createElement('button');
        confirmDeleteButton.textContent = 'Удалить';
        confirmDeleteButton.className = "tool-confirm-delete-button";
        // Стили для уточнающей кнопки "Отмена"
        const cancelButton = document.createElement('button');
        cancelButton.textContent = 'Отмена';
        cancelButton.className = "tool-confirm-cancel-button";
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
            const toolId = operationData.tool; // ID инструмента
            const cellId = operationData.cell;  // Значение из cellDiv
            // Вызов функции deleteLoad с нужными параметрами
            deleteLoad(jsonObjectHistory, jsonObjectCells, window.appData.tools, planName, toolId, cellId);
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
