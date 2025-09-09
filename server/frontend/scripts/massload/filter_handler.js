//import { jsonObjectTools } from './init.js';

  document.addEventListener("DOMContentLoaded", () => {
      // Получаем ссылки на элементы
      const dropdownItems = document.querySelectorAll("#plan-or-free .dropdown-item");
      const currentPlanDiv = document.querySelector("#plan-or-free .btn_vending");
      const toolsGroupDiv = document.getElementById("tools-group");
      const numberPlanDiv = document.getElementById("number-plan");

      // Устанавливаем начальное состояние
      currentPlanDiv.textContent = "Свободный";
      toolsGroupDiv.style.display = "flex";
      numberPlanDiv.style.display = "none";

      // Добавляем обработчики событий для dropdown items
      dropdownItems.forEach(item => {
        item.addEventListener("click", (event) => {
          const selectedText = event.target.textContent;

          // Меняем текст текущего выбора
          currentPlanDiv.textContent = selectedText;

          // Управляем отображением div'ов
          if (selectedText === "Свободный") {
            toolsGroupDiv.style.display = "flex";
            numberPlanDiv.style.display = "none";
          } else if (selectedText === "По чертежу") {
            toolsGroupDiv.style.display = "none";
            numberPlanDiv.style.display = "flex";
          }
        });
      });
    });


