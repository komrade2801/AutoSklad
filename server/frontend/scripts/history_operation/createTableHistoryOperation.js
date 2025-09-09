// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_cell').style.display = state
    document.getElementById('membrane').style.display = state
}

export function createTableHistoryOperation(containerId, jsonHistoryOperation) {
    const container = document.getElementById(containerId);

    let table = document.createElement("table");
    table.width = "100%";
    table.border = "1";

    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");
    ["Дата", "Название операции", "Инструмент", "Ячейка", "Чертёж", "Пользователь", "Аппарат"].forEach(text => {
        let th = document.createElement("th");
        th.textContent = text;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");

    // Должны проходить итерацию по jsonHistoryOperation.operation, а не по jsonHistoryOperation
    Object.values(jsonHistoryOperation.operation).forEach(operation => {
        let row = document.createElement("tr");

        [operation.date, operation.name_operation, operation.tool, operation.cell, operation.plan, operation.user, operation.device].forEach(value => {
            let td = document.createElement("td");
            td.textContent = value;
            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}


    // Функция для открытия модального окна
function openModalTools() {
    // Заполняем данные в модальном окне (это может быть динамическое содержимое)
    //document.querySelector('.cell_number').textContent = 'Ячейка № ' + cellNumber;
    //document.querySelector('img').src = 'image_' + cellNumber + '.jpg'; // Изменить путь к изображению
    //document.querySelector('.tool_group').textContent = 'Группа: Группа ' + cellNumber;
    //document.querySelector('.tool_name').textContent = 'Инструмент: ' + toolName;
    //document.querySelector('.plan_name').textContent = 'Чертёж: ' + planName;

    show('flex');  // Открываем модальное окно
}