function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

//     // Info button
//     let infoButton = document.createElement("i");
//     infoButton.className = "bi bi-info-square action-button";
//     infoButton.title = "Информация об инструменте";
//
//     infoButton.addEventListener('click', async function () {
//        openModalCell(row.tool, row.group, row.number, row.cell, row.plan)
//     });
//
//     actionsDiv.appendChild(infoButton);

     // Drop button
     let dropButton = document.createElement("i");
     dropButton.className = "bi bi-arrow-right-square action-button";
     dropButton.title = "Выгрузить";

     dropButton.addEventListener('click', async function () {
        handleUnloadClick(row.tool, row.group, row.number, row.cell, row.plan)
     });

     actionsDiv.appendChild(dropButton);

     return actionsDiv;
}

function actionStoryFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Drop button
     let unDropButton = document.createElement("i");
     unDropButton.className = "bi bi-x-circle action-button";
     unDropButton.title = "Отменить выгрузку";

     unDropButton.addEventListener('click', async function () {
        deleteDrop(row.operation);
     });

     actionsDiv.appendChild(unDropButton);

     return actionsDiv;
}

// Функция для открытия модального окна
function openModalCell(toolName, groupName, cellNumber, cellId, planName) {
    // Заполняем данные в модальном окне (это может быть динамическое содержимое)
    document.querySelector('.cell_number').textContent = 'Ячейка № ' + cellNumber;
    //document.querySelector('img').src = 'image_' + cellNumber + '.jpg'; // Изменить путь к изображению
    document.querySelector('.tool_group').textContent = 'Группа: ' + groupName;
    document.querySelector('.tool_name').textContent = 'Инструмент: ' + toolName;
    document.querySelector('.plan_name').textContent = 'Чертёж: ' + planName;


    const unloadBtn = document.querySelector('.btn_vending.upload');

    unloadBtn.dataset.cellId = cellId;
    unloadBtn.dataset.cellNumber = cellNumber;
    unloadBtn.dataset.groupName = groupName;
    unloadBtn.dataset.toolName = toolName;
    unloadBtn.dataset.planName = planName;

    show('flex');  // Открываем модальное окно
}

// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_cell').style.display = state;
    document.getElementById('membrane').style.display = state;
}

window.show = show;

function dropAllRows() {

    while (window.appData.tools.length > 0) {
        const row = window.appData.tools[0];
        console.log(row);
        handleUnloadClick(row.tool, row.group, row.number, row.cell, row.plan)
    }
}