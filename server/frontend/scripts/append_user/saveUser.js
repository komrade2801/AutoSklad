// init_save_user.js

export function setupUserForm() {
  // Выбор элементов
  const inputFamily       = document.getElementById('input-family');
  const inputFirstName    = document.getElementById('input-first-name');
  const inputSecondName   = document.getElementById('input-second-name');
  const btnRole           = document.getElementById('btn-role');
  const roleSelectItems   = document.querySelectorAll('#role_select .dropdown-item');
  const inputBarcode      = document.getElementById('input-barcode');
  const inputCode         = document.getElementById('input-code');
  const inputPassword     = document.getElementById('input-password');
  const btnGenerateBarcode= document.getElementById('btn-generate-barcode');
  const btnSave           = document.getElementById('btn-save-user');

  let selectedRoleId = null;
  let selectedRoleName = 'Должность';

  // Выбор роли
  roleSelectItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      selectedRoleId = Number(item.dataset.roleId);
      selectedRoleName = item.textContent;
      btnRole.textContent = selectedRoleName;
    });
  });

  // Генерация штрихкода и кода (например, случайные числа)
  btnGenerateBarcode.addEventListener('click', () => {
    const barcode = Date.now();            // или любая ваша логика
    const code    = Math.floor(Math.random() * 9000) + 1000;
    inputBarcode.value = barcode;
    inputCode.value    = code;
  });

  // Сохранение пользователя
  btnSave.addEventListener('click', async () => {
    try {
      // Собираем данные
      const userObj = {
        index:    0,                                // или другой логики генерации
        barcode:  Number(inputBarcode.value),
        code:     Number(inputCode.value),
        first_name:  inputFirstName.value.trim(),
        second_name: inputSecondName.value.trim(),
        family:      inputFamily.value.trim(),
        password:    inputPassword.value,
        role_id:     selectedRoleId                // заменяем role на role_id
      };

      // Валидация
      if (!userObj.family || !userObj.first_name || !userObj.second_name || !userObj.role_id) {
        alert('Пожалуйста, заполните все поля и выберите должность');
        return;
      }

      // Отправляем на сервер
      const created = await saveUserData(userObj);
      // alert(`Пользователь ${created.first_name} ${created.family} сохранён (ID=${created.index})`);
      // Можно очистить форму или перенаправить
      window.location.href = "/screen_19_users.html?token=" + localStorage.getItem("token");
    } catch (err) {
      console.error(err);
      alert('Ошибка при сохранении пользователя');
    }
  });
}

// При загрузке страницы
window.addEventListener('DOMContentLoaded', () => {
  setupUserForm();
});
