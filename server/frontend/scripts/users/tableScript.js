function passwordFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Info button
     let passwordButton = document.createElement("button");
     passwordButton.className = "btn btn_vending";
     passwordButton.title = "Посмотреть и редактировать пароль";
     passwordButton.textContent = "Пароль";

     passwordButton.addEventListener('click', async function () {
        openModalPassword({
            index: row.index,
            name: row.name,
            login: row.login,
            password: row.password
          });
     });

     actionsDiv.appendChild(passwordButton);

     return actionsDiv;
}

function fullNameFormatter(value, row, index, field) {
     return row.family + ' ' + row.first_name + ' ' + row.second_name;
}

function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Info button
     let barcodeButton = document.createElement("i");
     barcodeButton.className = "bi bi-qr-code action-button";
     barcodeButton.title = "Показать штрихкод";

     barcodeButton.addEventListener('click', async function () {
        openModalBarcode(row.index);
     });

     actionsDiv.appendChild(barcodeButton);

     // Edit button
     let editButton = document.createElement("i");
     editButton.className = "bi bi-pencil-fill action-button";
     editButton.title = "Редактировать пользователя";

     editButton.addEventListener('click', async function () {
        openModalEdit(row);
     });

     actionsDiv.appendChild(editButton);

     // Delete button
     let deleteButton = document.createElement("i");
     deleteButton.className = "bi bi-x-circle action-button";
     deleteButton.title = "Удалить пользователя";

     deleteButton.addEventListener('click', async function () {
        prepareUserDeletion(row.index);
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
            alert('Пожалуйста, заполните все поля и выберите должность');
            return;
        }

        // Отправляем на сервер
        const created = saveUserData(userObj);
        console.log(created);

        loadUsers();
        show_edit('none');
    } catch (err) {
        console.error(err);
        alert('Ошибка при сохранении пользователя');
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