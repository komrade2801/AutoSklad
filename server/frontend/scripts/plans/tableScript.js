// Универсальная функция для модального подтверждения удаления
function showDeleteConfirm(message) {
    return new Promise((resolve) => {
        // Устанавливаем текст сообщения
        document.getElementById('deleteConfirmMessage').textContent = message;

        // Показываем модальное окно
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();

        // Обработчики кнопок
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        const cancelBtn = document.getElementById('cancelDeleteBtn');

        const handleConfirm = () => {
            modal.hide();
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            modal.hide();
            cleanup();
            resolve(false);
        };

        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };

        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);

        // Обработчик закрытия модального окна по крестику или клику вне
        document.getElementById('deleteConfirmModal').addEventListener('hidden.bs.modal', () => {
            cleanup();
            resolve(false);
        }, { once: true });
    });
}


function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Tool list button
     let toolListButton = document.createElement("i");
     toolListButton.className = "bi bi-list-ol action-button";
     toolListButton.title = "Показать список инструментов";

     toolListButton.addEventListener('click', async function () {
        openModalRandomPlan(row);
     });

     actionsDiv.appendChild(toolListButton);

     // Barcode button
     let barcodeButton = document.createElement("i");
     barcodeButton.className = "bi bi-qr-code action-button";
     barcodeButton.title = "Показать штрихкод";

     barcodeButton.addEventListener('click', async function () {
        openModalBarcode(row.id, row.designation);
     });

     actionsDiv.appendChild(barcodeButton);

     // Edit button
     let editButton = document.createElement("i");
     editButton.className = "bi bi-pencil-fill action-button";
     editButton.title = "Редактировать чертеж";

     editButton.addEventListener('click', async function () {
         const toolTypeId = row.id;
         if (!toolTypeId) {
             console.error("ID чертежа не найден");
             return;
         }

         // Проверяем, занят ли инструмент
         try {
             const checkResponse = await fetch(`../backend/check_tool_busy/${toolTypeId}`);
             if (!checkResponse.ok) {
                 throw new Error("Ошибка проверки чертежа");
             }
             const checkData = await checkResponse.json();

             if (checkData.is_busy) {
                 showToast("Данный инструмент используется в вендинге. Редактировать можно только свободный инструмент. " + checkData.message, 'warning');
                 return;
             }

             // Переходим на страницу редактирования с параметром tool_type_id
             let url = '../screen_16_add_tool.html';
             let targetUrl = new URL(url, window.location.origin).href;
             let token = localStorage.getItem('token');
             let full_url = targetUrl + "?token=" + token + "&tool_type_id=" + toolTypeId;
             window.location.href = full_url;
         } catch (error) {
             console.error('Ошибка при проверке инструмента:', error);
             showToast('Ошибка при проверке инструмента', 'danger');
         }
     });

     actionsDiv.appendChild(editButton);

     // Delete button
     let deleteButton = document.createElement("i");
     deleteButton.className = "bi bi-x-circle action-button";
     deleteButton.title = "Удалить чертеж";

     deleteButton.addEventListener('click', async function () {
         const toolTypeId = row.id;
         if (!toolTypeId) {
             console.error("ID инструмента не найден");
             return;
         }

         // Подтверждение удаления
         const confirmed = await showDeleteConfirm("Вы уверены, что хотите удалить этот инструмент?");
         if (!confirmed) {
             return;
         }

         // Удаляем инструмент (endpoint сам проверит занятость)
         try {
             const deleteResponse = await fetch(`../backend/delete_tool_type/${toolTypeId}`, {
                 method: 'DELETE'
             });

             if (!deleteResponse.ok) {
                 const errorData = await deleteResponse.json();
                 showToast(errorData.detail || "Ошибка при удалении инструмента", 'danger');
                 return;
             }

             const result = await deleteResponse.json();
             showToast(result.message || "Инструмент успешно удален", 'success');

             // Перезагружаем страницу для обновления таблицы
             let url = '../screen_15_tool_library.html';
             let targetUrl = new URL(url, window.location.origin).href;
             let token = localStorage.getItem('token');
             let full_url = targetUrl + "?token=" + token;
             window.location.href = full_url;
         } catch (error) {
             console.error('Ошибка при удалении инструмента:', error);
             showToast('Ошибка при удалении инструмента', 'danger');
         }
     });

     actionsDiv.appendChild(deleteButton);

     return actionsDiv;
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

//функции для работы с модальным окном подтверждения
var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf(index) {
    window.userIndexToDelete = index; // сохраняем индекс глобально
    show_conf('flex');  // Открываем модальное окно
}

window.openModalConf = openModalConf;
window.show_conf = show_conf;


//функции для работы с модальным окном пароля
var show_password = function (state) {
    document.getElementById('modal_window_password').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalPassword(user) {
  window.userIndexToDelete = user.index; // сохраняем индекс глобально

  // Заполняем данные в модалке
  document.getElementById('user').textContent = user.name || '';
  document.getElementById('login').textContent = 'Логин: ' + (user.login || '');
  document.getElementById('password_input').value = user.password || '';

  show_password('flex'); // Открываем модальное окно
}


window.openModalPassword = openModalPassword;
window.show_password = show_password;

// Функция для отображения модального окна
var show_edit = function (state) {
    document.getElementById('modal_window_edit').style.display = state;
    document.getElementById('membrane').style.display = state;
}

window.show_edit = show_edit;

function openModalEdit(user) {
    if (user) {
        window.userIndexToEdit = user.index; // сохраняем индекс глобально
    } else {
        window.userIndexToEdit = 0;
        user = {
            index:    0,
            barcode:  '',
            code:     '',
            first_name:  '',
            second_name: '',
            family:      '',
            password:    '',
            role_id:     6
        }
    }

  console.log(user);

    // Заполнение ФИО
    document.getElementById("input-family").value = user.family || "";
    document.getElementById("input-first-name").value = user.first_name || "";
    document.getElementById("input-second-name").value = user.second_name || "";

    // Заполнение роли
    document.getElementById('input-role').value = user.role_id || 6;

    // Заполнение штрихкода, логина и пароля
    document.getElementById("input-barcode").value = user.barcode || "";
    document.getElementById("input-code").value = user.code || "";
    document.getElementById("input-password").value = user.password || "";

    console.log("функция автозаполнения сработала");



  // Заполняем данные в модалке
  document.getElementById('user').textContent = user.name || '';
  document.getElementById('login').textContent = 'Логин: ' + (user.login || '');
  document.getElementById('password_input').value = user.password || '';

  show_edit('flex'); // Открываем модальное окно
}

window.openModalEdit = openModalEdit;

function saveUser() {
    try {
        const inputFamily       = document.getElementById('input-family');
        const inputFirstName    = document.getElementById('input-first-name');
        const inputSecondName   = document.getElementById('input-second-name');
        const inputRole         = document.getElementById('input-role');
        const inputBarcode      = document.getElementById('input-barcode');
        const inputCode         = document.getElementById('input-code');
        const inputPassword     = document.getElementById('input-password');

        // Собираем данные
        const userObj = {
            index:    Number(window.userIndexToEdit),            // или другой логики генерации
            barcode:  Number(inputBarcode.value),
            code:     Number(inputCode.value),
            first_name:  inputFirstName.value.trim(),
            second_name: inputSecondName.value.trim(),
            family:      inputFamily.value.trim(),
            password:    inputPassword.value,
            role_id:     Number(inputRole.value)                // заменяем role на role_id
        };

        // Валидация
        if (!userObj.family || !userObj.first_name || !userObj.second_name || !userObj.role_id) {
            showToast('Пожалуйста, заполните все поля и выберите должность', 'warning');
            return;
        }

        // Отправляем на сервер
        const created = saveUserData(userObj);
        console.log(created);

        loadUsers();
        show_edit('none');
    } catch (err) {
        console.error(err);
        showToast('Ошибка при сохранении пользователя', 'danger');
    }
}

async function saveUserData(userObj) {
    const token = localStorage.getItem('token');
    console.log(window.userIndexToEdit);
    console.log(userObj);
    var response;
    if (window.userIndexToEdit == 0) {
        response = await sendData('../backend/create_user', token, 'POST', userObj);
    } else {
        response = await sendData('../backend/update_user/' + window.userIndexToEdit, token, 'PUT', userObj);
    }

    return response;
  }

// Функция для получения JSON-данных через эндпоинт
async function fetchSendData(url, payload) {
    try {
        console.log('fetchData '+ url + ' ' + payload);
        const response = await fetch(url, payload);
        console.log(response);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        console.log(jsonData);
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

/*
 * Функция загрузки и сохранения JSON.
 * Возвращает Promise, чтобы можно было ждать результата.
 */
function sendData(url, token, method, userObj) {
    console.log('sendData '+ url + ' ' + token + ' ' + method + ' ' + userObj);
    const payload = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userObj),
    }
    url = url + '?token=' + token;
    return fetchSendData(url, payload)
    .then(data => {
        console.log('sendData 1');
        return data;
    })
    .catch(err => {
        console.log('sendData 2');
        console.error('Не удалось отправить данные', err);
        return null;
    });
}

// Функция для очистки полей ввода и сброса значений select
function clearAllForm() {
    document.querySelectorAll(".form-control").forEach(input => {
        input.value = "";
    });

    document.querySelectorAll("#selection_tools select").forEach(select => {
        select.value = "0";
    });
}


/**
 * Устанавливает в модалку URL изображения и открывает её.
 * @param {number} planId
 */
function openModalBarcode(planId, planDesignation) {

    console.log(planId)
  // Подставляем ID в текст
  document.getElementById('modal_plan_id').textContent = planDesignation;

  // Формируем URL к вашему эндпоинту
  const img = document.getElementById('modal_barcode_img');
  img.src = `/backend/plan_barcode?plan_index=${encodeURIComponent(planId)}`;
  console.log(img.src);

  // Очистим старое, если вдруг
  img.onerror = () => {
    console.error('Не удалось загрузить штрих‑код');
    img.alt = 'Ошибка загрузки';
  };

  // Открываем модалку
  showBarcode('flex');
}


// Функция для отображения модального окна Штрихкода
var showBarcode = function (state) {
    document.getElementById('modal_window_barcode').style.display = state
    document.getElementById('membrane').style.display = state
}

window.showBarcode = showBarcode;

// Функция для открытия модального окна
function openModalRandomPlan(data) {

    console.log(data);
    if (data.tools != undefined) {

        $('#random_plan_id').text(data.designation);

        show_random_plan('flex');  // Открываем модальное окно
        $('#random_plan_table').bootstrapTable('showLoading');
        $('#random_plan_table').bootstrapTable('refreshOptions', {'height': $("#random_plan_div").height()});
        $('#random_plan_table').bootstrapTable('load', data.tools);
        $('#random_plan_table').bootstrapTable('hideLoading');
    }


}

function createTableRandomPlan(data) {
    console.log(data);
}

// Функция для отображения модального окна
var show_random_plan = function (state) {
    document.getElementById('modal_window_details').style.display = state;
    document.getElementById('membrane').style.display = state;
}

window.show_random_plan = show_random_plan;