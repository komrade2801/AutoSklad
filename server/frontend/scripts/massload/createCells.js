    // Функция для создания ячеек на основе JSON-данных
    const BLOCKED_CELL_IDS = new Set([1, 36, 71, 106, 141, 176]);

    export function createCells(containerId, jsonObjectCells) {
        const container = document.getElementById(containerId);
        container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек

        console.log('createCells');
        console.log(jsonObjectCells.rows);

        // Проходим по строкам в JSON
        for (const rowKey in jsonObjectCells.rows) {
            const rowData = jsonObjectCells.rows[rowKey];
            const rowDiv = document.createElement('div');
            rowDiv.style.display = 'flex'; // Устанавливаем флекс-контейнер для строки
            rowDiv.style.overflow = 'visible';

            // Проходим по ячейкам в строке
            for (const cellKey in rowData.cells) {
                const cellData = rowData.cells[cellKey];
                const cellDiv = document.createElement('div');

                // Устанавливаем класс и уникальный ID для ячейки
                cellDiv.className = 'droppable';
                cellDiv.setAttribute("droppable", true);
                cellDiv.id = cellData.id;
                cellDiv.setAttribute('data-tooltip', `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`);

                // Устанавливаем стили для ячейки
                cellDiv.style.display = 'flex'; // Включает Flexbox
                cellDiv.style.overflow = 'visible';
                cellDiv.style.width = '44px';
                cellDiv.style.height = cellData.type === 'big' ? '70px' : '50px';
                cellDiv.style.border = '1px solid #FFFFFF';
                cellDiv.style.backgroundColor = cellData.backgroundColor;
                cellDiv.style.alignItems = 'center';
                cellDiv.style.justifyContent = 'center';
                cellDiv.style.margin = '1px';

                if (BLOCKED_CELL_IDS.has(Number(cellData.id))) {
                    cellDiv.classList.add('cell-blocked');
                    cellDiv.style.opacity = '0.4';
                    cellDiv.setAttribute('data-blocked', 'true');
                    cellDiv.setAttribute('data-tooltip', 'Ячейка недоступна');
                    cellData.block = true;
                }

                // Добавляем текстовое содержимое (номер ячейки)
                cellDiv.textContent = cellData.id;

                // Добавляем всплывающую подсказку с информацией о содержимом
                //cellDiv.title = `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`;

                rowDiv.appendChild(cellDiv); // Добавляем ячейку в строку
            }

            container.appendChild(rowDiv); // Добавляем строку в контейнер
        }
    }
