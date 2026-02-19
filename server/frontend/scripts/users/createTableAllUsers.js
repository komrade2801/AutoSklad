


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
 * Показывает или скрывает модалку штрихкода (Bootstrap 5).
 * @param {'flex'|'none'} mode
 */
export function showBarcode(mode) {
  const el = document.getElementById('modal_window_barcode');
  if (!el) return;
  const modal = bootstrap.Modal.getOrCreateInstance(el);
  if (mode === 'none') {
    modal.hide();
  } else {
    modal.show();
  }
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

    const width = img.width;
    const height = img.height;

    const left = (window.screen.width / 2) - (width / 2);
    const top = (window.screen.height / 2) - (height / 2);

    const printWindow = window.open('', '_blank', 'width=${width},height=${height},top=${top},left=${left}');

    printWindow.document.write(`<img src="${img.src}" onload="window.print()">`);

    printWindow.document.close(); // Завершаем запись
    printWindow.focus(); // Фокусируем новое окно
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

function generateTableUsers() {
    if (window.jsonUsers != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#users_table').bootstrapTable('load', window.jsonUsers);
        $('#users_table').bootstrapTable('hideLoading');
    }
}
window.generateTableUsers = generateTableUsers;