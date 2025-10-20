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

      // Устанавливаем стили для строки инструмента
      toolDiv.style.height = "32px";
      toolDiv.style.display = 'flex';
      toolDiv.style.flexDirection = 'row';
      toolDiv.style.flexWrap = 'nowrap';
      toolDiv.style.alignItems = 'center';
      toolDiv.style.borderRadius = '5px';

      // Устанавливаем стили для имени инструмента
      const toolNameDiv = document.createElement("div");
      toolNameDiv.textContent = toolData.name;
      toolNameDiv.style.display = 'flex';
      toolNameDiv.style.width = '100%';
      toolNameDiv.style.height = '30px';
      toolNameDiv.style.backgroundColor = '#D3D3D3A0';
      toolNameDiv.style.border = '1.5px solid #FFFFFF';
      toolNameDiv.style.borderRadius = '5px';
      toolNameDiv.style.color = '#003172';
      toolNameDiv.style.fontWeight = 'bold';
      toolNameDiv.style.fontSize = '14px';
      toolNameDiv.style.alignItems = 'center';
      toolNameDiv.style.justifyContent = 'start';
      toolNameDiv.style.margin = '1px';
      toolNameDiv.style.paddingLeft = '5px';

      toolDiv.appendChild(toolNameDiv);

      //Создаём поле ввода количества инструмента
      const input = document.createElement("input");
      input.className = "form-control me-2 input_amount";
      input.type = "number";
      input.min = 1;
      input.max = toolData.count;
      input.value = 1;

      //Устанавливаем стили для ввода количества
      input.style.width = "70px";
      input.style.height = "30px";
      input.style.border = '1.5px solid #FFFFFF';
      input.style.backgroundColor = '#56b358';
      input.style.color = '#FFFFFF';

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

      //Устанавливаем стили для кнопки удаления (кнопка с крестиком)
      deleteButton.style.width = '30px';
      deleteButton.style.height = '30px';
      deleteButton.style.marginRight = '1px'
      deleteButton.style.border = '1px solid #FFFFFF';
      deleteButton.style.backgroundColor = '#56b358';
      deleteButton.style.display = 'flex';
      deleteButton.style.alignItems = 'center';
      deleteButton.style.justifyContent = 'center';
      deleteButton.style.borderRadius = '5px'

      //Добавляем иконку на кнопку
      const deleteIcon = document.createElement('img');
      deleteIcon.src = '../assets/img/btn_cross_2.png';
      deleteIcon.style.width = '20px'; // Размер иконки
      deleteIcon.style.height = '20px';
      deleteIcon.style.pointerEvents = 'none'; // Отключаем обработку кликов на изображении
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
