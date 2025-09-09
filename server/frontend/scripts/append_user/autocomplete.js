//
//window.addEventListener("DOMContentLoaded", () => {
//  const userData = localStorage.getItem("editUser");
//  if (userData) {
//    const user = JSON.parse(userData);
//
//    const inputs = document.querySelectorAll("input.form-control");
//
//    if (inputs.length >= 3) {
//      inputs[0].value = user.family || "";
//      inputs[1].value = user.first_name || "";
//      inputs[2].value = user.second_name || "";
//    }
//
//    // Установить роль (если у вас есть соответствие role_id -> текст)
//    const roleButton = document.querySelector("#role_select .btn_vending");
//    if (roleButton && user.role_id) {
//      roleButton.textContent = roleMap[user.role] || "Неизвестно";
//    }
//    console.log("функция автозаполнения сработала")
//  }
//});

window.addEventListener("DOMContentLoaded", () => {
  const userData = localStorage.getItem("editUser");
  if (userData) {
    const user = JSON.parse(userData);

    // Заполнение ФИО
    document.getElementById("input-family").value = user.family || "";
    document.getElementById("input-first-name").value = user.first_name || "";
    document.getElementById("input-second-name").value = user.second_name || "";

    // Заполнение роли
    const roleButton = document.getElementById("btn-role");
    const roleItems = document.querySelectorAll("#role_select .dropdown-item");

    if (user.role_id && roleButton && roleItems.length > 0) {
      roleItems.forEach(item => {
        if (parseInt(item.dataset.roleId) === user.role_id) {
          roleButton.textContent = item.textContent;
          roleButton.dataset.roleId = user.role_id; // сохранение выбранной роли, если нужно
        }
      });
    }

    // Заполнение штрихкода, логина и пароля
    document.getElementById("input-barcode").value = user.barcode || "";
    document.getElementById("input-code").value = user.code || "";
    document.getElementById("input-password").value = user.password || "";

    console.log("функция автозаполнения сработала");
  }
});
