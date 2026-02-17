function sumFormatter(value, row, index, field) {
    // Заменяем "-" на символ бесконечности
    return (value === '-' || value === 0 || value === '0') ? '∞' : value;
}

function sumToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";



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
    // ИСПРАВЛЕНО: обрабатываем случаи, когда sum отсутствует или null/undefined
    var max;
    if (row.sum === undefined || row.sum === null) {
        max = 99999999; // Бесконечный запас
    } else {
        const parsedSum = parseInt(row.sum, 10);
        if (isNaN(parsedSum) || parsedSum < 0) {
            max = 99999999; // Бесконечный запас
        } else {
            max = parsedSum;
        }
    }
    if (max > 0) {
        input.value = '1';
    }
    input.max = max.toString();
    input.className = 'library-tool-input';

    inputDiv.appendChild(input);
    inputRow.appendChild(inputDiv);

    currentInputRow = inputRow;

     // Load button
     let dropButton = document.createElement("i");
     dropButton.className = "bi bi-arrow-right-square action-button";
     dropButton.title = "Загрузить";

    dropButton.addEventListener('click', (event) => {
        event.stopPropagation();
        const amount = parseInt(input.value);
        if (validateInput(amount, max)) {
            // Проверяем доступность свободных ячеек перед загрузкой
            const currentLoadAmount = window.getTotalToolsToLoad();

            if (window.appData.freeCells < amount + currentLoadAmount) {
                alert(`Недостаточно свободных ячеек. Доступно: ${window.appData.freeCells}, требуется: ${amount + currentLoadAmount}`);
                return;
            }

            performMassLoad(row.id, row.name, max, amount);
        }
    });

     inputRow.appendChild(dropButton);

    actionsDiv.appendChild(inputRow);

     return actionsDiv;
}

// Функция валидации ввода
function validateInput(value, maxSum) {
    if (!Number.isInteger(value) || value <= 0 || value > maxSum) {
        alert('Введено некорректное число. Должно быть целое положительное число, не превышающее доступное количество.');
        return false;
    }
    return true;
}

function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Info button
     let infoButton = document.createElement("i");
     infoButton.className = "bi bi-info-square action-button";
     infoButton.title = "Информация об инструменте";

     infoButton.addEventListener('click', async function () {
        openModalCell(row.id, row.name, row.sum)
     });

     actionsDiv.appendChild(infoButton);

     return actionsDiv;
}

function actionStoryFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Drop button
     let unLoadButton = document.createElement("i");
     unLoadButton.className = "bi bi-x-circle action-button";
     unLoadButton.title = "Отменить загрузку";

     unLoadButton.addEventListener('click', async function () {
        deleteLoad(row.tool);
     });

     actionsDiv.appendChild(unLoadButton);

     return actionsDiv;
}

// Функция для открытия модального окна
function openModalCell(toolId, toolName, toolSum) {
    // Заполняем данные в модальном окне (это может быть динамическое содержимое)
    //document.querySelector('img').src = 'image_' + cellNumber + '.jpg'; // Изменить путь к изображению
    document.querySelector('.tool_name').textContent = 'Инструмент: ' + toolName;
    document.querySelector('.tool_sum').textContent = 'Количество: ' + (toolSum === '-' ? '∞' : toolSum);

    const input = document.getElementById('modal_amount_input');

    input.type = 'number';
    input.min = '0';
    input.value = '0';
    input.step = '1';
    input.pattern = '[0-9]*';
    input.inputMode = 'numeric';
    // ИСПРАВЛЕНО: обрабатываем случаи, когда sum отсутствует или null/undefined
    var max;
    if (toolSum === undefined || toolSum === null) {
        max = 99999999; // Бесконечный запас
    } else {
        const parsedSum = parseInt(toolSum, 10);
        if (isNaN(parsedSum) || parsedSum < 0) {
            max = 99999999; // Бесконечный запас
        } else {
            max = parsedSum;
        }
    }
    if (max > 0) {
        input.value = '1';
    }
    input.max = max.toString();

     const dropButton = document.getElementById('modal_drop_button');

    dropButton.addEventListener('click', (event) => {
        event.stopPropagation();
        const amount = parseInt(input.value);
        if (validateInput(amount, max)) {
            // Проверяем доступность свободных ячеек перед загрузкой
            const currentLoadAmount = window.getTotalToolsToLoad();

            if (window.appData.freeCells < amount + currentLoadAmount) {
                alert(`Недостаточно свободных ячеек. Доступно: ${window.appData.freeCells}, требуется: ${amount + currentLoadAmount}`);
                return;
            }

            performMassLoad(toolId, toolName, toolSum, amount);
            show('none');  // Закрыть модальное окно
        }
    });

    show('flex');  // Открываем модальное окно
}

// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_cell').style.display = state;
    document.getElementById('membrane').style.display = state;
}

window.show = show;

// Функция для открытия модального окна
function openModalConfirmation() {
    show('flex');  // Открываем модальное окно
}

window.openModalConfirmation = openModalConfirmation