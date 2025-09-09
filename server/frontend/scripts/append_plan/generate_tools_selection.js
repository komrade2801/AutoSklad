import { generateTools } from './generateTools.js';
import { initializeDragAndDrop } from './drag_and_drop.js';


export function generateToolsSelection() {
  const container = document.getElementById("selection_tools");
  container.innerHTML = "";

  if (!window.jsonPlan || !window.jsonPlan.tools) {
    console.error("Нет данных для отображения инструментов");
    return;
  }

  Object.entries(window.jsonPlan.tools).forEach(([toolName, sum]) => {
    if (toolName !== "groups") {
      
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
      toolNameDiv.textContent = toolName;
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

      // Получаем максимально допустимое значение sum из jsonToolLibrary
      let maxSum = 1;
      let jsonToolLibrary = window.tool_library;
      for (const groupKey in jsonToolLibrary.groups) {
        const group = jsonToolLibrary.groups[groupKey];
        for (const subgroupKey in group.subgroup) {
          const subgroup = group.subgroup[subgroupKey];
          for (const valueKey in subgroup.value) {
            const item = subgroup.value[valueKey];
            if (item.tools === toolName) {
              maxSum = parseInt(item.sum, 10);
              break;
            }
          }
        }
      }

      //Создаём поле ввода количества инструмента
      const input = document.createElement("input");
      input.className = "form-control me-2 input_sum";
      input.type = "number";
      input.min = "1";
      input.max = maxSum.toString();
      input.value = sum || "1";

      //Устанавливаем стили для ввода количества
      input.style.width = "70px";
      input.style.height = "30px";
      input.style.border = '1.5px solid #FFFFFF';
      input.style.backgroundColor = '#56b358';
      input.style.color = '#FFFFFF';

      //Устанавливаем обработчик события ввода
      input.addEventListener("input", (e) => {
        let val = parseInt(e.target.value, 10);
        if (isNaN(val) || val < 1) val = 1;
        if (val > maxSum) val = maxSum;
        e.target.value = val;
        window.jsonPlan.tools[toolName] = val.toString();
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
        delete window.jsonPlan.tools[toolName];

        // Возвращаем в jsonToolLibrary
        for (const groupKey in window.tool_library.groups) {
          const group = window.tool_library.groups[groupKey];
          for (const subgroupKey in group.subgroup) {
            const subgroup = group.subgroup[subgroupKey];
            const values = subgroup.value;
            const keys = Object.keys(values);
            const nextIndex = keys.length ? Math.max(...keys.map(Number)) + 1 : 0;

            let restored = false;

            for (const valueKey in values) {
              const item = values[valueKey];
              if (item.tools === toolName) {
                restored = true;
                break;
              }
            }

            if (!restored) {
              // Восстанавливаем с суммой maxSum
              subgroup.value[nextIndex] = {
                tools: toolName,
                sum: maxSum.toString()
              };
              break;
            }
          }
        }

        // Обновляем интерфейс
        // let jsonToolLibrary = window.tool_library;
        generateTools("tools", window.tool_library);
        generateToolsSelection();
        initializeDragAndDrop();
      });

      toolDiv.appendChild(input);
      toolDiv.appendChild(deleteButton);
      container.appendChild(toolDiv);
    }
  });
}
