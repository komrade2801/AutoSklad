function sumFormatter(value, row, index, field) {
    // Заменяем "-" на символ бесконечности
    return (value === '-' || value === 0 || value === '0') ? '∞' : value;
}

// Функция для загрузки данных инструмента при редактировании
async function loadToolData(toolTypeId) {
    try {
        const response = await fetch(`../backend/get_tool_type_by_id/${toolTypeId}`);
        if (!response.ok) {
            throw new Error("Ошибка загрузки данных инструмента");
        }
        const toolData = await response.json();

        // Заполняем форму данными инструмента
        document.getElementById("tool_name").value = toolData.name || "";
        document.getElementById("tool_description").value = toolData.description || "";

        // Устанавливаем группу
        const groupSelect = document.getElementById("select_group");
        if (toolData.group_id && toolData.group_id > 0) {
            groupSelect.value = toolData.group_id;
        } else {
            groupSelect.value = 0;
        }

        // Устанавливаем количество
        if (toolData.count && toolData.count > 0) {
            document.getElementById("useToolCount").checked = true;
            document.getElementById("tool_count").value = toolData.count;
            showToolCount(); // Показываем блок с количеством
            // Обновляем таблицу с количеством инструментов
            updateTable();
        } else {
            document.getElementById("useToolCount").checked = false;
            document.getElementById("tool_count").value = 1;
        }

        // Сохраняем ID инструмента для обновления
        window.currentToolTypeId = toolTypeId;
    } catch (error) {
        console.error('Ошибка при загрузке данных инструмента:', error);
        alert('Ошибка при загрузке данных инструмента');
    }
}

//// Проверяем наличие параметра tool_type_id в URL при загрузке страницы
//// Используем setTimeout, чтобы дать время для загрузки групп через init_16_add_tool.js
//window.addEventListener('DOMContentLoaded', function() {
//    const urlParams = new URLSearchParams(window.location.search);
//    const toolTypeId = urlParams.get('tool_type_id');
//    if (toolTypeId) {
//        // Ждем загрузки групп (примерно 500мс должно хватить)
//        setTimeout(() => {
//            loadToolData(parseInt(toolTypeId));
//        }, 500);
//    }
//});

function showToolCount() {
    const elem = document.getElementById("ToolCountBlock");
    console.log(elem);

    if (elem.style.display == 'none') {
        elem.style.display = 'block';
    } else {
        elem.style.display = 'none';
    }
}

// Функция, собирающая данные из формы и таблицы, формирующая JSON и отправляющая его на сервер
function collectDataAndSend() {
    // Получение значений из полей формы
    const groupInput = document.getElementById("select_group");
    const toolNameInput = document.getElementById("tool_name");
    const countInput = document.getElementById("tool_count");
    const useCount = document.getElementById("useToolCount").checked;

    const groupId = parseInt(groupInput.value);
    // const group = groupInput.value.trim();
    // const subgroup = document.getElementById("search_subgroup").value.trim();
    const toolName = toolNameInput.value.trim();
    const description = document.getElementById("tool_description").value.trim();

    // Инициализация count в зависимости от useCount
    let count;
    if (useCount) {
        count = parseInt(countInput.value, 10);
    } else {
        count = 0;
    }

    // Валидация обязательных полей
    if (isNaN(groupId)) {
        alert('Выбрана некорректная группа инструментов');
        return;
    }

    if (groupId === 0) {
        alert('Необходимо выбрать группу инструмента');
        groupInput.focus();
        return;
    }

    if (toolName === '') {
        alert('Наименование инструмента не может быть пустым');
        toolNameInput.focus();
        return;
    }

    if (useCount) {
        if (isNaN(count) || count <= 0) {
            alert('Количество инструмента должно быть положительным числом');
            countInput.focus();
            return;
        }
    }

    const tableRows = document.querySelectorAll("#tools_table tbody tr");
    const tools = {};

    Array.from(tableRows).forEach(row => {
        const cells = row.querySelectorAll("td");
        const number = cells[0].textContent.trim();
        const inventoryInput = cells[1].querySelector("input");
        let inventory = inventoryInput.value.trim();
        if (inventory === '') {
            inventory = 'None';
        }
        tools[number] = inventory;
    });

    const data = {
        group_id: groupId,
        tool_name: toolName,
        img: "",
        description: description,
        count: count,
        tools: tools
    };

    // Если редактируем существующий инструмент, добавляем tool_type_id
    if (window.currentToolTypeId) {
        data.tool_type_id = window.currentToolTypeId;
    }

    const endpointUrl = '../backend/create_tools';

    fetch(endpointUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error('Ошибка сети: ' + JSON.stringify(errData));
            });
        }
        return response.json();
    })
    .then(result => {
        console.log('Успешно:', result);
//        let url = '../screen_15_tool_library.html';
//        let targetUrl = new URL(url, window.location.origin).href;
//        let token = localStorage.getItem('token');
//        let full_url = targetUrl + "?token=" + token;
//        window.location.href = full_url;

        show_create('none');
        let device_number = 1;
        loadToolLibraryTable(device_number);

        // Дополнительные действия
    })
    .catch(error => {
        console.error('Ошибка при сохранении данных:', error);
        // Обработка ошибок
    });
}

// Функция валидации ввода
function validateInput(value, maxSum) {
    if (!Number.isInteger(value) || value <= 0 || value > maxSum) {
        alert('Введено некорректное число. Должно быть целое положительное число, не превышающее доступное количество.');
        return false;
    }
    return true;
}

async function editTool(row) {
     const toolTypeId = row.id;
     if (!toolTypeId) {
         console.error("ID инструмента не найден");
         return;
     }

     // Проверяем, занят ли инструмент
     try {
         const checkResponse = await fetch(`../backend/check_tool_busy/${toolTypeId}`);
         if (!checkResponse.ok) {
             throw new Error("Ошибка проверки инструмента");
         }
         const checkData = await checkResponse.json();

         if (checkData.is_busy) {
             alert("Данный инструмент используется в вендинге.\nРедактировать можно только свободный инструмент.\n" + checkData.message);
             return;
         }

         // Переходим на страницу редактирования с параметром tool_type_id
//         let url = '../screen_16_add_tool.html';
//         let targetUrl = new URL(url, window.location.origin).href;
//         let token = localStorage.getItem('token');
//         let full_url = targetUrl + "?token=" + token + "&tool_type_id=" + toolTypeId;
//         window.location.href = full_url;

            loadToolData(parseInt(toolTypeId));
            openModalCreate();

     } catch (error) {
         console.error('Ошибка при проверке инструмента:', error);
         alert('Ошибка при проверке инструмента');
     }
}

async function deleteTool(row) {
    const toolTypeId = row.id;
    if (!toolTypeId) {
        console.error("ID инструмента не найден");
        return;
    }

    // Подтверждение удаления
    if (!confirm("Вы уверены, что хотите удалить этот инструмент?")) {
        return;
    }

    // Удаляем инструмент (endpoint сам проверит занятость)
    try {
        const deleteResponse = await fetch(`../backend/delete_tool_type/${toolTypeId}`, {
         method: 'DELETE'
        });

        if (!deleteResponse.ok) {
            const errorData = await deleteResponse.json();
            alert(errorData.detail || "Ошибка при удалении инструмента");
            return;
        }

        const result = await deleteResponse.json();
        alert(result.message || "Инструмент успешно удален");

        // Перезагружаем страницу для обновления таблицы
        let device_number = 1;
        loadToolLibraryTable(device_number);

//        let url = '../screen_15_tool_library.html';
//        let targetUrl = new URL(url, window.location.origin).href;
//        let token = localStorage.getItem('token');
//        let full_url = targetUrl + "?token=" + token;
//        window.location.href = full_url;
    } catch (error) {
        console.error('Ошибка при удалении инструмента:', error);
        alert('Ошибка при удалении инструмента');
    }
}

function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Edit button
     let editButton = document.createElement("i");
     editButton.className = "bi bi-pencil-fill action-button";
     editButton.title = "Редактировать инструмент";

     editButton.addEventListener('click', async function () {
        editTool(row)
     });

     actionsDiv.appendChild(editButton);

     // Delete button
     let deleteButton = document.createElement("i");
     deleteButton.className = "bi bi-x-circle action-button";
     deleteButton.title = "Удалить инструмент";

     deleteButton.addEventListener('click', async function () {
        deleteTool(row)
     });

     actionsDiv.appendChild(deleteButton);

     return actionsDiv;
}

// Функция для загрузки данных группы при редактировании
async function loadGroupData(groupId) {
    try {
        const response = await fetch(`../backend/get_group_by_id/${groupId}`);
        if (!response.ok) {
            throw new Error("Ошибка загрузки данных группы");
        }
        const groupData = await response.json();

        // Заполняем форму данными группы
        document.getElementById("group_name").value = groupData.name || "";
        document.getElementById("group_description").value = groupData.description || "";

        // Устанавливаем родительскую группу
        const parentGroupSelect = document.getElementById("select_parent_group");
        if (groupData.parent_group && groupData.parent_group > 0) {
            parentGroupSelect.value = groupData.parent_group;
        } else {
            parentGroupSelect.value = 0;
        }

        // Сохраняем ID группы для обновления
        window.currentGroupId = groupId;
    } catch (error) {
        console.error('Ошибка при загрузке данных группы:', error);
        alert('Ошибка при загрузке данных группы');
    }
}

//// Проверяем наличие параметра group_id в URL при загрузке страницы
//window.addEventListener('DOMContentLoaded', function() {
//    const urlParams = new URLSearchParams(window.location.search);
//    const groupId = urlParams.get('group_id');
//    if (groupId) {
//        loadGroupData(parseInt(groupId));
//    }
//});

// Функция, собирающая данные из формы и таблицы, формирующая JSON и отправляющая его на сервер
function collectDataAndSendGroup() {
    // Получение значений из полей формы
    const groupNameInput = document.getElementById("group_name");
    const parentGroupInput = document.getElementById("select_parent_group");
    const descriptionInput = document.getElementById("group_description");

    const groupName = groupNameInput.value.trim();
    const description = descriptionInput.value.trim();
    const parentGroupId = parseInt(parentGroupInput.value);

    // Валидация обязательных полей
    if (isNaN(parentGroupId)) {
        alert('Выбрана некорректная родительская группа инструментов');
        return;
    }

    if (groupName === '') {
        alert('Наименование группы не может быть пустым');
        groupNameInput.focus();
        return;
    }

    const data = {
        group_name: groupName,
        parent_group: parentGroupId,
        description: description,
        img: "",
    };

    // Если редактируем существующую группу, добавляем group_id
    if (window.currentGroupId) {
        data.group_id = window.currentGroupId;
    }

    const endpointUrl = '../backend/create_groups';

    fetch(endpointUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error('Ошибка сети: ' + JSON.stringify(errData));
            });
        }
        return response.json();
    })
    .then(result => {
        console.log('Успешно:', result);

        show_create('none');
        let device_number = 1;
        loadToolLibraryTable(device_number);


//        let url = '../screen_15_tool_library.html';
//        let targetUrl = new URL(url, window.location.origin).href;
//        let token = localStorage.getItem('token');
//        let full_url = targetUrl + "?token=" + token;
//        window.location.href = full_url;
        // Дополнительные действия
    })
    .catch(error => {
        console.error('Ошибка при сохранении данных:', error);
        // Обработка ошибок
    });
}

async function editGroup(row) {
     const groupId = row.id;
     if (!groupId) {
         console.error("ID группы не найден");
         return;
     }

     // Проверяем, занята ли группа
     try {
         const checkResponse = await fetch(`../backend/check_group_busy/${groupId}`);
         if (!checkResponse.ok) {
             throw new Error("Ошибка проверки группы");
         }
         const checkData = await checkResponse.json();

         if (checkData.is_busy) {
             alert("Данный инструмент используется в вендинге.\nРедактировать можно только свободный инструмент.");
             return;
         }

         loadGroupData(parseInt(groupId));
         openModalCreateGroup();

         // Переходим на страницу редактирования с параметром group_id
//         let url = '../screen_23_add_group.html';
//         let targetUrl = new URL(url, window.location.origin).href;
//         let token = localStorage.getItem('token');
//         let full_url = targetUrl + "?token=" + token + "&group_id=" + groupId;
//         window.location.href = full_url;
     } catch (error) {
         console.error('Ошибка при проверке группы:', error);
         alert('Ошибка при проверке группы');
     }
}

async function deleteGroup(row) {
    const groupId = row.id;
     if (!groupId) {
         console.error("ID группы не найден");
         return;
     }

     // Подтверждение удаления
     if (!confirm("Вы уверены, что хотите удалить эту группу?")) {
         return;
     }

     // Удаляем группу (endpoint сам проверит занятость)
     try {
         const deleteResponse = await fetch(`../backend/delete_group/${groupId}`, {
             method: 'DELETE'
         });

         if (!deleteResponse.ok) {
             const errorData = await deleteResponse.json();
             alert(errorData.detail || "Ошибка при удалении группы");
             return;
         }

         const result = await deleteResponse.json();
         alert(result.message || "Группа успешно удалена");


        let device_number = 1;
        loadToolLibraryTable(device_number);

         // Перезагружаем страницу для обновления таблицы
//         let url = '../screen_15_tool_library.html';
//         let targetUrl = new URL(url, window.location.origin).href;
//         let token = localStorage.getItem('token');
//         let full_url = targetUrl + "?token=" + token;
//         window.location.href = full_url;
     } catch (error) {
         console.error('Ошибка при удалении группы:', error);
         alert('Ошибка при удалении группы');
     }
}

function actionGroupsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Edit button
     let editButton = document.createElement("i");
     editButton.className = "bi bi-pencil-fill action-button";
     editButton.title = "Редактировать группу";

     editButton.addEventListener('click', async function () {
        editGroup(row)
     });

     actionsDiv.appendChild(editButton);

     // Delete button
     let deleteButton = document.createElement("i");
     deleteButton.className = "bi bi-x-circle action-button";
     deleteButton.title = "Удалить группу";

     deleteButton.addEventListener('click', async function () {
        deleteGroup(row)
     });

     actionsDiv.appendChild(deleteButton);

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

var show_create = function (state) {
    document.getElementById('modal_window_create').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalCreate() {
    show_create('flex');  // Открываем модальное окно
}

window.openModalCreate = openModalCreate;

var show_create_group = function (state) {
    document.getElementById('modal_window_create_group').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalCreateGroup() {
    show_create_group('flex');  // Открываем модальное окно
}

window.openModalCreateGroup = openModalCreateGroup;