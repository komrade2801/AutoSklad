// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_cell').style.display = state;
    document.getElementById('membrane').style.display = state;
}

// Функция для создания ячеек на основе JSON-данных
export function createCells(containerId, jsonObjectCells) {
    const container = document.getElementById(containerId);
    container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек
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
            // Добавляем текстовое содержимое (номер ячейки)
            cellDiv.textContent = cellData.id;
            // При клике открывается модальное окно с данными для этой ячейки
            cellDiv.addEventListener('click', function() {
                openModalCell(cellDiv.id, cellData.content.tool, cellData.content.plan);
            });
            // Обработчик клика с захватом актуальных данных
            //cellDiv.addEventListener('click', (function(id, tool, plan) {
            //    return function() {
            //        openModalCell(id, tool, plan);
            //    }
            //})(cellDiv.id, cellData.content.tool, cellData.content.plan));
            // Добавляем всплывающую подсказку с информацией о содержимом
            //cellDiv.title = `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`;
            rowDiv.appendChild(cellDiv); // Добавляем ячейку в строку
        }
        container.appendChild(rowDiv); // Добавляем строку в контейнер
    }
}

// Функция для открытия модального окна
function openModalCell(cellNumber, toolName, planName) {
    // Заполняем данные в модальном окне (это может быть динамическое содержимое)
    document.querySelector('.cell_number').textContent = 'Ячейка № ' + cellNumber;
    //document.querySelector('img').src = 'image_' + cellNumber + '.jpg'; // Изменить путь к изображению
    //document.querySelector('.tool_group').textContent = 'Группа: Группа ' + cellNumber;
    document.querySelector('.tool_name').textContent = 'Инструмент: ' + toolName;
    document.querySelector('.plan_name').textContent = 'Чертёж: ' + planName;


    const unloadBtn = document.querySelector('.btn_vending.upload');

    unloadBtn.dataset.cellId = cellNumber;
    unloadBtn.dataset.toolName = toolName;
    unloadBtn.dataset.planName = planName;


    show('flex');  // Открываем модальное окно
}

window.show = show;