function passwordFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

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
     return [row.family, row.first_name, row.second_name].filter(Boolean).join(' ') || '';
}

function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     let barcodeButton = document.createElement("i");
     barcodeButton.className = "bi bi-qr-code action-button";
     barcodeButton.title = "Показать штрихкод";

     barcodeButton.addEventListener('click', async function () {
        openModalBarcode(row.index);
     });

     actionsDiv.appendChild(barcodeButton);

     let editButton = document.createElement("i");
     editButton.className = "bi bi-pencil-fill action-button";
     editButton.title = "Редактировать пользователя";

     editButton.addEventListener('click', async function () {
        openModalEdit(row);
     });

     actionsDiv.appendChild(editButton);

     let deleteButton = document.createElement("i");
     deleteButton.className = "bi bi-x-circle action-button";
     deleteButton.title = "Удалить пользователя";

     deleteButton.addEventListener('click', async function () {
        prepareUserDeletion(row.index);
     });

     actionsDiv.appendChild(deleteButton);

     return actionsDiv;
}

// --- Модальное окно редактирования пользователя (Bootstrap 5) ---
function getEditModalInstance() {
    const el = document.getElementById('modal_window_edit');
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
}

function show_edit(state) {
    const modal = getEditModalInstance();
    if (!modal) return;
    if (state === 'none') {
        modal.hide();
    } else {
        modal.show();
    }
}

window.show_edit = show_edit;

function openModalEdit(user) {
    if (user) {
        window.userIndexToEdit = user.index;
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
        };
    }

    document.getElementById("input-family").value = user.family || "";
    document.getElementById("input-first-name").value = user.first_name || "";
    document.getElementById("input-second-name").value = user.second_name || "";
    document.getElementById('input-role').value = String(user.role_id || 6);
    document.getElementById("input-barcode").value = user.barcode || "";
    document.getElementById("input-code").value = user.code || "";
    document.getElementById("input-password").value = user.password || "";
    document.getElementById("input-password").type = "password";
    const showCheck = document.getElementById("input-password-show");
    if (showCheck) showCheck.checked = false;

    show_edit('flex');
}

window.openModalEdit = openModalEdit;

function togglePasswordVisibility(inputId, show) {
    const input = document.getElementById(inputId);
    if (input) input.type = show ? 'text' : 'password';
}

window.togglePasswordVisibility = togglePasswordVisibility;

// Очистка формы редактирования (только поля модалки редактирования)
function clearEditForm() {
    const ids = ['input-family', 'input-first-name', 'input-second-name', 'input-barcode', 'input-code', 'input-password'];
    ids.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    const role = document.getElementById('input-role');
    if (role) role.value = '6';
    const showCheck = document.getElementById('input-password-show');
    if (showCheck) showCheck.checked = false;
    const pwd = document.getElementById('input-password');
    if (pwd) pwd.type = 'password';
    window.userIndexToEdit = 0;
}

// Кнопка «Очистить» в модалке — очищает только форму редактирования
function clearAllForm() {
    clearEditForm();
}

// --- Модальное окно подтверждения удаления (Bootstrap 5) ---
function getConfModalInstance() {
    const el = document.getElementById('modal_window_confirmation');
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
}

function show_conf(state) {
    const modal = getConfModalInstance();
    if (!modal) return;
    if (state === 'none') {
        modal.hide();
    } else {
        modal.show();
    }
}

function openModalConf(index) {
    window.userIndexToDelete = index;
    show_conf('flex');
}

window.openModalConf = openModalConf;
window.show_conf = show_conf;

// --- Модальное окно пароля (Bootstrap 5) ---
function getPasswordModalInstance() {
    const el = document.getElementById('modal_window_password');
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
}

function show_password(state) {
    const modal = getPasswordModalInstance();
    if (!modal) return;
    if (state === 'none') {
        modal.hide();
    } else {
        modal.show();
    }
}

function openModalPassword(user) {
    window.userIndexToDelete = user.index;
    document.getElementById('user').textContent = user.name || '';
    document.getElementById('login').textContent = 'Логин: ' + (user.login || '');
    document.getElementById('password_input').value = user.password || '';
    show_password('flex');
}

window.openModalPassword = openModalPassword;
window.show_password = show_password;

function clearPasswordForm() {
    const input = document.getElementById('password_input');
    if (input) input.value = '';
}

function savePassword() {
    const userIndex = window.userIndexToDelete;
    const newPassword = document.getElementById('password_input').value.trim();
    if (userIndex == null) return;
    const user = window.jsonUsers && window.jsonUsers.find(u => u.index === userIndex);
    if (!user) {
        if (typeof showToast === 'function') showToast('Данные пользователя не найдены', 'danger');
        return;
    }
    // Бэкенд PUT /update_user/{user_id} принимает полный UserUpdate (all_users.py)
    const userObj = {
        index:      user.index,
        barcode:    Number(user.barcode) || 0,
        code:       Number(user.code) || 0,
        first_name: user.first_name || '',
        second_name: user.second_name || '',
        family:     user.family || '',
        password:   newPassword,
        role_id:    Number(user.role_id) || 6
    };
    const token = localStorage.getItem('token');
    sendData('../backend/update_user/' + userIndex, token, 'PUT', userObj)
        .then((data) => {
            if (data != null) {
                if (typeof showToast === 'function') showToast('Пароль сохранён', 'success');
                show_password('none');
                loadUsers();
            } else {
                if (typeof showToast === 'function') showToast('Ошибка при сохранении пароля', 'danger');
            }
        })
        .catch(() => {
            if (typeof showToast === 'function') showToast('Ошибка при сохранении пароля', 'danger');
        });
}

window.savePassword = savePassword;

// --- Инициализация: очистка при закрытии модалок ---
function initUsersModalHandlers() {
    const editEl = document.getElementById('modal_window_edit');
    const confEl = document.getElementById('modal_window_confirmation');
    const pwdEl = document.getElementById('modal_window_password');
    if (editEl) {
        editEl.addEventListener('hidden.bs.modal', clearEditForm);
    }
    if (pwdEl) {
        pwdEl.addEventListener('hidden.bs.modal', clearPasswordForm);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUsersModalHandlers);
} else {
    initUsersModalHandlers();
}

// --- Проверка уникальности логина и штрихкода по списку пользователей ---
function checkUserUniqueness(code, barcode, excludeIndex) {
    const users = window.jsonUsers;
    if (!Array.isArray(users)) return { duplicate: false };
    const others = users.filter(function (u) { return u.index !== excludeIndex; });
    const codeNum = Number(code);
    const barcodeNum = Number(barcode);
    for (let i = 0; i < others.length; i++) {
        const u = others[i];
        if (Number(u.code) === codeNum) return { duplicate: true, field: 'code', value: code };
        if (Number(u.barcode) === barcodeNum) return { duplicate: true, field: 'barcode', value: barcode };
    }
    return { duplicate: false };
}

// --- Сохранение пользователя ---
function saveUser() {
    try {
        const inputFamily       = document.getElementById('input-family');
        const inputFirstName    = document.getElementById('input-first-name');
        const inputSecondName   = document.getElementById('input-second-name');
        const inputRole         = document.getElementById('input-role');
        const inputBarcode      = document.getElementById('input-barcode');
        const inputCode         = document.getElementById('input-code');
        const inputPassword     = document.getElementById('input-password');

        const familyTrimmed     = inputFamily.value.trim();
        const firstNameTrimmed  = inputFirstName.value.trim();
        const secondNameTrimmed = inputSecondName.value.trim();
        const barcodeTrimmed    = inputBarcode.value.trim();
        const codeTrimmed       = inputCode.value.trim();
        const passwordVal       = inputPassword.value;

        const codeNum = codeTrimmed === '' ? NaN : parseInt(codeTrimmed, 10);
        const codeValid = !isNaN(codeNum) && codeNum >= 0 && /^\d+$/.test(codeTrimmed);
        const code = codeValid ? codeNum : (Math.floor(Math.random() * 9000) + 1000);

        const barcodeNum = barcodeTrimmed === '' ? NaN : parseInt(barcodeTrimmed, 10);
        const barcodeValid = barcodeTrimmed === '' ? false : !isNaN(barcodeNum) && barcodeNum >= 0 && /^\d+$/.test(barcodeTrimmed);

        const isCreate = window.userIndexToEdit == 0;

        // Валидация обязательных полей (отчество опционально)
        if (!familyTrimmed || !firstNameTrimmed) {
            showToast('Заполните фамилию и имя', 'warning');
            return;
        }
        if (!inputRole.value || !Number(inputRole.value)) {
            showToast('Выберите должность', 'warning');
            return;
        }
        if (!barcodeTrimmed) {
            showToast('Введите штрихкод', 'warning');
            inputBarcode.focus();
            return;
        }
        if (!barcodeValid) {
            showToast('Штрихкод должен быть целым неотрицательным числом', 'warning');
            inputBarcode.focus();
            return;
        }
        if (codeTrimmed !== '' && !codeValid) {
            showToast('Логин должен быть целым неотрицательным числом', 'warning');
            inputCode.focus();
            return;
        }
        if (isCreate && (!passwordVal || !passwordVal.trim())) {
            showToast('Введите пароль для нового пользователя', 'warning');
            inputPassword.focus();
            return;
        }

        const userObj = {
            index:      Number(window.userIndexToEdit),
            barcode:    barcodeValid ? barcodeNum : 0,
            code:       code,
            first_name: firstNameTrimmed,
            second_name: secondNameTrimmed,
            family:     familyTrimmed,
            password:   passwordVal,
            role_id:    Number(inputRole.value)
        };

        // Проверка уникальности на клиенте
        const uniqueness = checkUserUniqueness(userObj.code, userObj.barcode, window.userIndexToEdit);
        if (uniqueness.duplicate) {
            if (uniqueness.field === 'code') {
                showToast('Такой логин уже используется другим пользователем', 'warning');
                inputCode.focus();
            } else {
                showToast('Такой штрихкод уже используется другим пользователем', 'warning');
                inputBarcode.focus();
            }
            return;
        }

        saveUserData(userObj).then(function (data) {
            if (data != null) {
                if (typeof loadUsers === 'function') loadUsers();
                show_edit('none');
                showToast(isCreate ? 'Пользователь создан' : 'Данные пользователя сохранены', 'success');
            } else {
                showToast('Ошибка при сохранении пользователя', 'danger');
            }
        }).catch(function () {
            showToast('Ошибка при сохранении пользователя', 'danger');
        });
    } catch (err) {
        console.error(err);
        showToast('Ошибка при сохранении пользователя', 'danger');
    }
}

function saveUserData(userObj) {
    const token = localStorage.getItem('token');
    const url = window.userIndexToEdit == 0
        ? '../backend/create_user?token=' + encodeURIComponent(token)
        : '../backend/update_user/' + window.userIndexToEdit + '?token=' + encodeURIComponent(token);
    const method = window.userIndexToEdit == 0 ? 'POST' : 'PUT';
    const payload = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify(userObj),
    };
    return fetch(url, payload)
        .then(function (response) {
            if (response.status === 409) {
                if (typeof showToast === 'function') {
                    showToast('Логин или штрихкод уже заняты. Выберите другие значения.', 'warning');
                }
                return null;
            }
            if (!response.ok) {
                return response.json().then(function (body) {
                    if (typeof showToast === 'function' && body && body.detail) {
                        showToast(body.detail, 'danger');
                    }
                    return null;
                }).catch(function () {
                    if (typeof showToast === 'function') {
                        showToast('Ошибка сети, статус: ' + response.status, 'danger');
                    }
                    return null;
                });
            }
            return response.json();
        })
        .catch(function (error) {
            console.error('Ошибка сохранения пользователя:', error);
            if (typeof showToast === 'function') {
                showToast('Ошибка при сохранении пользователя', 'danger');
            }
            return null;
        });
}

async function fetchSendData(url, payload) {
    try {
        const response = await fetch(url, payload);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: " + response.status);
        }
        return await response.json();
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

function sendData(url, token, method, userObj) {
    const payload = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(userObj),
    };
    url = url + '?token=' + token;
    return fetchSendData(url, payload);
}
