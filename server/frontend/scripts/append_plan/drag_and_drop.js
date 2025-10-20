import { generateToolsSelection } from './generate_tools_selection.js';
// import { jsonToolLibrary } from '../../JSONs/tool_library.js';
import { generateTools } from './generateTools.js';
//import { createTools } from './createTools.js';
//import { createCells } from './createCells.js';
//import { createHistory } from './createHistory.js';
//import { searchCellById } from './searchCellById.js';
//import { deleteLoad } from './deleteLoad.js';


// Функция для генерации JSON-Plan со списком инструментов к добавляемому чертежу
export function updateJsonPlan(toolId) {
    console.log(toolId);
    const tool = window.tool_library.tools[toolId]
    console.log(tool);
    if (!window.jsonPlan) 
      window.jsonPlan = {};
    if (!window.jsonPlan.tools) 
      window.jsonPlan.tools = {};
    // Если уже добавлен — ничего не делаем
    if(window.jsonPlan.tools.hasOwnProperty(toolId))
      return;
    window.jsonPlan.tools[toolId] = tool;
    console.log(window.jsonPlan);
    generateToolsSelection(); // пересобираем интерфейс выбора
}



//Функция для удаления инструмента из списка при перетаскивании
export function deleteTool(toolNameToDelete, containerId, jsonToolLibrary) {

    const elementToDelete = document.querySelector("#" + toolNameToDelete);
    console.log(elementToDelete)
//    elementToDelete.remove();

    for (const toolId in jsonToolLibrary.tools) {
        const toolData = jsonToolLibrary.tools[toolId];

        if (toolData.name === toolNameToDelete) {
            // Удаляем инструмент
            delete jsonToolLibrary.tools[toolId]
            console.log('deleted: ' + toolId)
            // Обновляем интерфейс
            window.jsonLibrary = jsonToolLibrary;
            generateTools(containerId, jsonToolLibrary);
            initializeDragAndDrop();
            return; // Прерываем, как только нашли и удалили инструмент
        }
    }

//  for (const groupKey in jsonToolLibrary.groups) {
//    const groupData = jsonToolLibrary.groups[groupKey];
//    for (const subgroupKey in groupData.subgroup) {
//      const subgroupData = groupData.subgroup[subgroupKey];
//      const values = subgroupData.value;
//      for (const valueKey in values) {
//        const valueData = values[valueKey];
//        if (valueData.tools === toolNameToDelete) {
//            // Удаляем инструмент
//            delete values[valueKey];
//            // Обновляем интерфейс
//            window.tool_library = jsonToolLibrary;
//            generateTools(containerId, jsonToolLibrary);
//            initializeDragAndDrop();
//            return; // Прерываем, как только нашли и удалили инструмент
//        }
//      }
//    }
//  }
}



//функция Dragg-and-Dropp с проверкой инициализации перед привязкой обработчиков
export function initializeDragAndDrop() {
  
  const draggableElements = document.querySelectorAll(".draggable");
  draggableElements.forEach(draggable => {
    if (!draggable.dataset.initialized) {
      draggable.setAttribute("draggable", true);
      draggable.addEventListener("dragstart", (event) => {
        const toolName = draggable.querySelector(".toolName").textContent;
        const toolId = draggable.getAttribute('data-value-index');
        if (toolName) {
          event.dataTransfer.setData("toolName", toolName);
          event.dataTransfer.setData("toolId", toolId);
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
      const toolId = event.dataTransfer.getData("toolId");
      updateJsonPlan(toolId); // добавит, если ещё не было
      let jsonToolLibrary = window.jsonLibrary;
      deleteTool(toolName, "tools", jsonToolLibrary); // удаляет из оригинального списка
    });
    selectionContainer.dataset.initialized = "true";
  }
}

