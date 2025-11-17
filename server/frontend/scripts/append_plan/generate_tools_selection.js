import { generateTools } from './generateTools.js';
import { initializeDragAndDrop } from './drag_and_drop.js';


export function generateToolsSelection() {
  console.log('generateToolsSelection');
  const container = document.getElementById("selection_tools");
  container.innerHTML = "";

  if (!window.jsonPlan || !window.jsonPlan.tools) {
    console.error("Нет данных для отображения инструментов");
    return;
  }

  for (const toolId in window.jsonPlan.tools) {
    const toolData = window.jsonPlan.tools[toolId];
    if (toolData.name !== "groups") {

      console.log(toolData);
      
      const toolDiv = document.createElement("div");
      toolDiv.className = "tool-row-block";

      const toolNameDiv = document.createElement("div");
      toolNameDiv.className = "tool-name-block";
      toolNameDiv.setAttribute('data-tool-id', toolData.id);
      toolNameDiv.textContent = toolData.name;

      toolDiv.appendChild(toolNameDiv);

      //Создаём поле ввода количества инструмента
      const input = document.createElement("input");
      input.className = "form-control me-2 input_amount";
      input.type = "number";
      input.min = 1;
      input.max = toolData.count;
      input.value = toolData.amount;

      //Устанавливаем обработчик события ввода
      input.addEventListener("input", (e) => {
        console.log('input: ', e);
        let val = parseInt(e.target.value, 10);
        console.log(val);
        if (isNaN(val) || val < 1) val = 1;
        if (val > toolData.count) val = toolData.count;
        e.target.value = val;
        window.jsonPlan.tools[toolId].amount = val;
      });


      //Создаём кнопку для удаления инструмента
      const deleteButton = document.createElement('button');

      deleteButton.className = "tool-delete-button";

      //Добавляем иконку на кнопку
      const deleteIcon = document.createElement('img');
      deleteIcon.src = '../assets/img/btn_cross_2.png';
      deleteIcon.className = "tool-delete-button-icon";
      deleteButton.appendChild(deleteIcon);

      // Добавляем обработчик события для deleteButton
      deleteButton.addEventListener('click', () => {
            // Удаляем из jsonPlan
            delete window.jsonPlan.tools[toolId];

            window.jsonLibrary.tools[toolId] = toolData;

        // Обновляем интерфейс
        generateTools("tools", window.jsonLibrary);
        generateToolsSelection();
        initializeDragAndDrop();
      });

      toolDiv.appendChild(input);
      toolDiv.appendChild(deleteButton);
      container.appendChild(toolDiv);
    }
  }
}
