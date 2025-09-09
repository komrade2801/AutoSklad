//import { jsonObjectTools } from './init.js';
// Функция для создания строк инструмента на основе JSON-данных
export function createTools(containerId, jsonObjectTools) {
    console.log(jsonObjectTools)
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек
    // Проходим по строкам в JSON
    for (const planKey in jsonObjectTools.plans) {
        const planData = jsonObjectTools.plans[planKey];
        for (const groupKey in planData.groups) {
            const groupData = planData.groups[groupKey];
            // Проходим по ячейкам в строке
            for (const valueKey in groupData.value) {
                const valueData = groupData.value[valueKey];
                const toolDiv = document.createElement('div');
                // Устанавливаем флекс-контейнер для строки и класс
                toolDiv.style.display = 'flex';
                toolDiv.style.flexDirection = 'row';
                toolDiv.style.flexWrap = 'nowrap';
                toolDiv.className = 'draggable';
                toolDiv.draggable = "true";
                toolDiv.style.width = '100%';
                toolDiv.style.cursor = 'pointer';
                toolDiv.content = planData['name'];
                toolDiv.setAttribute('data-plans-index', planKey);
                toolDiv.setAttribute('data-group-index', groupKey);
                toolDiv.setAttribute('data-value-index', valueKey);
                toolDiv.setAttribute('data-plan-name', planData.name);
                // Устанавливаем стили для строки инструмента                
                toolDiv.style.height = '32px';
                toolDiv.style.alignItems = 'center';
                //Создаем название и количество инструмента
                const nameDiv = document.createElement('div');
                const sumDiv = document.createElement('div');
                // Устанавливаем стили для названия инструмента
                nameDiv.className = 'toolName';
                nameDiv.textContent = valueData.tools;
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
                // Добавляем всплывающую подсказку с полным наименованием инструмента
                //nameDiv.title = `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`;
                // Устанавливаем стили для количества инструмента
                sumDiv.textContent = valueData.sum;
                sumDiv.className = 'sumTool';
                sumDiv.style.display = 'flex';
                sumDiv.style.width = '35px';
                sumDiv.style.height = '30px';
                sumDiv.style.marginRight = '0px'
                sumDiv.style.border = '1px solid #FFFFFF';
                sumDiv.style.backgroundColor = '#56b358';
                sumDiv.style.alignItems = 'center';
                sumDiv.style.justifyContent = 'center';
                // Добавляем название и количество в строку инструмента
                toolDiv.appendChild(nameDiv);
                toolDiv.appendChild(sumDiv);
                container.appendChild(toolDiv); // Добавляем строку в контейнер
            }
        }
    }
}
