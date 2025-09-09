import { fetchToolLibraryData } from './init_8_append_plan.js';


// Функция для создания строк инструмента на основе JSON-данных
export function generateTools(containerId, jsonToolLibrary) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек

    // Проходим по группам в JSON
    for (const groupKey in jsonToolLibrary.groups) {
        const groupData = jsonToolLibrary.groups[groupKey];

        for (const subgroupKey in groupData.subgroup) {
            const subgroupData = groupData.subgroup[subgroupKey];

            // Проходим по инструментам в подгруппе
            for (const valueKey in subgroupData.value) {
                const valueData = subgroupData.value[valueKey];
                const toolDiv = document.createElement('div');

                // Устанавливаем флекс-контейнер для строки и класс
                toolDiv.style.display = 'flex';
                toolDiv.style.flexDirection = 'row';
                toolDiv.style.flexWrap = 'nowrap';
                toolDiv.className = 'draggable';
                toolDiv.draggable = "true";
                toolDiv.style.width = '100%';
                toolDiv.style.cursor = 'pointer';
                toolDiv.style.borderRadius = '5px';
                toolDiv.style.backgroundColor = '#D3D3D3A0';

                toolDiv.setAttribute('data-group-index', groupKey);
                toolDiv.setAttribute('data-subgroup-index', subgroupKey);
                toolDiv.setAttribute('data-value-index', valueKey);
                toolDiv.setAttribute('data-group-name', groupData.name);
                toolDiv.setAttribute('data-subgroup-name', subgroupData.SGName);

                // Устанавливаем стили для строки инструмента
                toolDiv.style.height = '32px';
                toolDiv.style.alignItems = 'center';

                // Создаем название и количество инструмента
                const nameDiv = document.createElement('div');

                // Устанавливаем стили для названия инструмента
                nameDiv.className = 'toolName';
                nameDiv.textContent = `${valueData.tools}`;
                nameDiv.style.display = 'flex';
                nameDiv.style.width = '100%';
                nameDiv.style.height = '30px';
                nameDiv.style.border = '1px solid #ffffff';
                nameDiv.style.color = '#003172';
                nameDiv.style.fontWeight = 'bold';
                nameDiv.style.fontSize = '14px';
                nameDiv.style.alignItems = 'center';
                nameDiv.style.justifyContent = 'start';
                nameDiv.style.margin = '1px';
                nameDiv.title = `Группа: ${groupData.name}\nПодгруппа: ${subgroupData.SGName}`;

                toolDiv.appendChild(nameDiv);
                container.appendChild(toolDiv); // Добавляем строку в контейнер


            }
        }
    }
}
