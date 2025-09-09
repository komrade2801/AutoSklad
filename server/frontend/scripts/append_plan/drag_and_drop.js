import { generateToolsSelection } from './generate_tools_selection.js';
// import { jsonToolLibrary } from '../../JSONs/tool_library.js';
import { generateTools } from './generateTools.js';
//import { createTools } from './createTools.js';
//import { createCells } from './createCells.js';
//import { createHistory } from './createHistory.js';
//import { searchCellById } from './searchCellById.js';
//import { deleteLoad } from './deleteLoad.js';


// Функция для генерации JSON-Plan со списком инструментов к добавляемому чертежу
export function updateJsonPlan(toolName) {
    console.log(toolName);
    if (!window.jsonPlan) 
      window.jsonPlan = {};
    if (!window.jsonPlan.tools) 
      window.jsonPlan.tools = {};
    // Если уже добавлен — ничего не делаем
    if(window.jsonPlan.tools.hasOwnProperty(toolName)) 
      return;
    window.jsonPlan.tools[toolName] = "1";
    console.log(window.jsonPlan);
    generateToolsSelection(); // пересобираем интерфейс выбора
}



//Функция для удаления инструмента из списка при перетаскивании
export function deleteTool(toolNameToDelete, containerId, jsonToolLibrary) {
  for (const groupKey in jsonToolLibrary.groups) {
    const groupData = jsonToolLibrary.groups[groupKey];
    for (const subgroupKey in groupData.subgroup) {
      const subgroupData = groupData.subgroup[subgroupKey];
      const values = subgroupData.value;
      for (const valueKey in values) {
        const valueData = values[valueKey];
        if (valueData.tools === toolNameToDelete) {
            // Удаляем инструмент
            delete values[valueKey];
            // Обновляем интерфейс
            window.tool_library = jsonToolLibrary;
            generateTools(containerId, jsonToolLibrary);
            initializeDragAndDrop();
            return; // Прерываем, как только нашли и удалили инструмент
        }
      }
    }
  }
}



//функция Dragg-and-Dropp с проверкой инициализации перед привязкой обработчиков
export function initializeDragAndDrop() {
  
  const draggableElements = document.querySelectorAll(".draggable");
  draggableElements.forEach(draggable => {
    if (!draggable.dataset.initialized) {
      draggable.setAttribute("draggable", true);
      draggable.addEventListener("dragstart", (event) => {
        const toolName = draggable.querySelector(".toolName").textContent;
        if (toolName) {
          event.dataTransfer.setData("toolName", toolName);
        }
      });
      draggable.dataset.initialized = "true";
    }
  });
  const selectionContainer = document.getElementById("selection_tools");
  if (selectionContainer && !selectionContainer.dataset.initialized) {
    selectionContainer.addEventListener("dragover", (event) => {
      event.preventDefault(); // разрешаем сброс
    });
    selectionContainer.addEventListener("drop", (event) => {
      event.preventDefault();
      const toolName = event.dataTransfer.getData("toolName");
      updateJsonPlan(toolName); // добавит, если ещё не было
      let jsonToolLibrary = window.tool_library;
      deleteTool(toolName, "tools", jsonToolLibrary); // удаляет из оригинального списка
    });
    selectionContainer.dataset.initialized = "true";
  }
}

