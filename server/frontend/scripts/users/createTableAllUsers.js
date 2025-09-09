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


window.userIndexToDelete = null;


//функция для открытия модального окна пользователя на удаление
function prepareUserDeletion(index) {
  userIndexToDelete = index;

  const user = window.jsonUsers.find(u => u.index === index);
  if (user) {
    const fullName = `${user.family} ${user.first_name} ${user.second_name}`;
    const roleName = user.role || "Неизвестно";

    // Заполняем данные в модальном окне
    document.getElementById("name_user").textContent = `ФИО: ${fullName}`;
    document.getElementById("role").textContent = `Роль: ${roleName}`;
  } else {
    console.error("Пользователь не найден:", index);
  }

  openModalConf(userIndexToDelete); // Показываем модалку
}

window.prepareUserDeletion = prepareUserDeletion;


//функция для переключения на экран редактирования пользователя
window.editUser = function(index) {
  const user = window.jsonUsers.find(u => u.index === index);
  if (user) {
    localStorage.setItem("editUser", JSON.stringify(user));
    window.location.href = "./screen_19_1_append_user.html?token="+localStorage.getItem('token');
  } else {
    console.error("Пользователь не найден:", index);
  }
}


window.addUser = function() {
  localStorage.removeItem("editUser");
  window.location.href = "./screen_19_1_append_user.html?token="+localStorage.getItem('token');
}


/**
 * Показывает или скрывает модалку.
 * @param {'flex'|'none'} mode
 */
export function showBarcode(mode) {
  const overlay = document.getElementById('modal_window_barcode');
  overlay.style.display = mode;
}


/**
 * Устанавливает в модалку URL изображения и открывает её.
 * @param {number} userId 
 */
export function openModalBarcode(userId) {
  // Подставляем ID в текст
  document.getElementById('modal_user_id').textContent = userId;

  // Формируем URL к вашему эндпоинту
  const img = document.getElementById('modal_barcode_img');
  img.src = `/backend/user_barcode?user_id=${encodeURIComponent(userId)}`;

  // Очистим старое, если вдруг
  img.onerror = () => {
    console.error('Не удалось загрузить штрих‑код');
    img.alt = 'Ошибка загрузки';
  };

  // Открываем модалку
  showBarcode('flex');
}


//печать штрихкода
export function printBarcode() {
  const img = document.getElementById('modal_barcode_img');
  const w = window.open('');
  w.document.write(`<img src="${img.src}" onload="window. print();window.close()">`);
  w.document.close();
}


//функция генерации таблицы "Все пользователи"
export function generateTableUsers(containerId, jsonUsers) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Контейнер с ID "${containerId}" не найден.`);
    return;
  }

  // Очищаем предыдущий контент
  container.innerHTML = "";

  // Создаём таблицу
  const table = document.createElement("table");
  table.style.width = "100%";
  table.border = "1";

  // Заголовок
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  const headers = [
    "ID",
    "Штрихкод",
    "Логин",
    "Пароль",
    "ФИО",
    "Роль",
    "Печать штрихкода",
    "Редактировать",
    "Удалить"
  ];
  headers.forEach(text => {
    const th = document.createElement("th");
    th.textContent = text;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Тело
  const tbody = document.createElement("tbody");

  jsonUsers.forEach(user => {
    const tr = document.createElement("tr");

    // ID
    const tdId = document.createElement("td");
    tdId.textContent = user.index;
    tr.appendChild(tdId);

    // Штрихкод
    const tdBarcode = document.createElement("td");
    tdBarcode.textContent = user.barcode;
    tr.appendChild(tdBarcode);

    // Код
    const tdCode = document.createElement("td");
    tdCode.textContent = user.code;
    tr.appendChild(tdCode);

    // Пароль
    const tdPassword = document.createElement("td");
    const btnPassword = document.createElement("button");
    btnPassword.className = "btn_vending";
    btnPassword.textContent = "Пароль";
    btnPassword.style.width = "150px";
    btnPassword.title = "Посмотреть и редактировать пароль";
    btnPassword.addEventListener("click", () => {
      openModalPassword({
        index: user.index,
        name: user.name,
        login: user.login,
        password: user.password
      });
    });

    tdPassword.appendChild(btnPassword);
    tr.appendChild(tdPassword);

    // ФИО
    const tdFio = document.createElement("td");
    tdFio.textContent = `${user.family} ${user.first_name} ${user.second_name}`;
    tr.appendChild(tdFio);

    // Роль
    const tdRole = document.createElement("td");
    tdRole.textContent = user.role || "Неизвестно";
    tr.appendChild(tdRole);

    // Кнопка Штрихкод
    const tdMakeBarcode = document.createElement("td");
    const btnBarcode = document.createElement("button");
    btnBarcode.style.cssText = "width:35px;height:35px;border:none;background:none;cursor:pointer;";
    btnBarcode.title = "Штрихкод";

    btnBarcode.addEventListener("click", () => {
      openModalBarcode(user.index);
    });

    const imgBarcode = document.createElement("img");
    imgBarcode.src = "../assets/img/barcode.png";
    imgBarcode.width = 35; imgBarcode.height = 35;
    btnBarcode.appendChild(imgBarcode);

    tdMakeBarcode.appendChild(btnBarcode);
    tr.appendChild(tdMakeBarcode);

    // Кнопка Редактировать
    const tdEdit = document.createElement("td");
    const btnEdit = document.createElement("button");
    btnEdit.style.cssText = "width:35px;height:35px;border:none;background:none;cursor:pointer;";
    btnEdit.title = "Редактировать";
    btnEdit.addEventListener("click", () => {
      editUser(user.index);
    });
    const imgEdit = document.createElement("img");
    imgEdit.src = "../assets/img/pencil.png";
    imgEdit.alt = "edit";
    imgEdit.width = 35; imgEdit.height = 35;
    btnEdit.appendChild(imgEdit);
    tdEdit.appendChild(btnEdit);
    tr.appendChild(tdEdit);

    // Кнопка Удалить
    const tdDelete = document.createElement("td");
    const btnDelete = document.createElement("button");
    btnDelete.style.cssText = "width:35px;height:35px;border:none;background:none;cursor:pointer;";
    btnDelete.title = "Удалить";
    btnDelete.addEventListener("click", () => {
      prepareUserDeletion(user.index);
    });
    const imgDel = document.createElement("img");
    imgDel.src = "../assets/img/btn_cross_2.png";
    imgDel.alt = "delete";
    imgDel.width = 35; imgDel.height = 35;
    btnDelete.appendChild(imgDel);
    tdDelete.appendChild(btnDelete);
    tr.appendChild(tdDelete);

    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  container.appendChild(table);
}



// Функция для открытия модального окна
function openModalUser() {
    showTool('flex');  // Открываем модальное окно
}

//     // Функция для открытия модального окна
// function openModalBarcode() {
//     showBarcode('flex');  // Открываем модальное окно
// }

// window.showBarcode = showBarcode;

// Экспорт в глобальную область, если нужно
window.openModalBarcode = openModalBarcode;
window.showBarcode = showBarcode;
window.printBarcode = printBarcode;