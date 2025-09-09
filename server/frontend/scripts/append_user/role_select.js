
  document.addEventListener("DOMContentLoaded", () => {
    // Получаем ссылки на элементы
    const dropdownItems = document.querySelectorAll(".dropdown-item");
    const roleSelectDiv = document.getElementById("role_select");
    const roleButton = roleSelectDiv.querySelector("button.btn_vending"); // Кнопка "Должность"

    // Добавляем обработчики событий для dropdown items
    dropdownItems.forEach(item => {
      item.addEventListener("click", (event) => {
        const selectedText = event.target.textContent;

        // Меняем текст кнопки "Должность"
        roleButton.textContent = selectedText;
      });
    });
  });




