// import { jsonObjectTools } from './init.js?v=1';
// import { jsonObjectCells } from './init.js';
import { createTools } from './createTools.js';
import { createCells } from './createCells.js';
import { createHistory } from './createHistory.js';
import { searchCellById } from './searchCellById.js';
import { deleteLoad } from './deleteLoad.js';

// Экспортируем функции для использования в createTools.js
export function updateToolsJSON(toolsData, plansIndex, groupIndex, toolIndex) {
    updateToolsJSONMass(toolsData, plansIndex, groupIndex, toolIndex, 1);
}

export function updateToolsJSONMass(toolsData, plansIndex, groupIndex, toolIndex, subtractAmount) {
    //console.log("updateToolsJSONMass успешно вызвана")
    // Получаем группу и инструмент по индексу
    const group = toolsData.plans[plansIndex].groups[groupIndex];

    // Получаем инструмент по индексу
    const tool = group.value[toolIndex];

    // Уменьшаем значение sum на указанное количество
    tool.sum -= subtractAmount;

    // Если sum становится 0 или меньше, удаляем инструмент из списка
    if (tool.sum <= 0) {
        delete group.value[toolIndex];
    }

    // Обновляем отображение элементов на странице
    createTools('tools-container', toolsData);
    initializeDragAndDrop();
}

//функция для изменения JSON-Tools с инструментами при dragg-and-dropp (deprecated, use Mass)
function updateToolsJSONold(toolsData, plansIndex, groupIndex, toolIndex) {
    //console.log("updateToolsJSON успешно вызвана")
    // console.log(plansIndex)
    // console.log(groupIndex)
    // console.log(toolIndex)

    // Получаем группу и инструмент по индексу
    const group = toolsData.plans[plansIndex].groups[groupIndex];

    // const group = toolsData.plans[plansIndex].groups[groupIndex];
    const tool = group.value[toolIndex];

    // Если sum == 1, удаляем инструмент из списка
    if (tool.sum == 1) {
        delete group.value[toolIndex];
    } else {
        // Если sum > 1 уменьшаем значение sum на 1
        tool.sum -= 1;
    }

    // Обновляем отображение элементов на странице
    createTools('tools-container', toolsData);
    initializeDragAndDrop();
}


//функция для изменения JSON-Cells с ячейками при dragg-and-dropp
export function updateCellsJSON(jsonObjectCells, planName, toolName, cellId) {
  
    //console.log("updateCellsJSON успешно вызвана")
    //console.log(cellId)

    const cell = searchCellById(cellId);

    // Обновляем чертёж и название инструмента
    cell.content.plan = planName;
    cell.content.tool = toolName;

    //Изменяем цвет ячейки
      //Устанавливаем цвет для свободного инструмента
      if (planName == "None") {
          cell.backgroundColor = '#2C8822';
      } else {
      // Устанавливаем цвет для инструмента по чертежу
          cell.backgroundColor = '#ff4f00';
      }

    cell.block = true;

    // Обновляем отображение элементов на странице
    createCells('cells-container', jsonObjectCells);
    initializeDragAndDrop();
}


// Функция для генерации JSON-History с историей текущей загрузки
export function updateJsonHistory(jsonObjectHistory, planName, groupIndex, toolName, cellId) {
    // Убедимся, что jsonObjectHistory.operation существует
    if (!jsonObjectHistory.operation) {
        jsonObjectHistory.operation = {}; // Инициализируем, если это null или undefined
    }

    // Создаем новый объект для операций с новой записью под первым номером
    const newOperation = {
        1: {
            cell: String(cellId), // Преобразуем в строку, чтобы соответствовать образцу
            tool: toolName,
            plan: planName
        }
    };

    // Сдвигаем существующие операции вниз, увеличивая их индексы на 1
    const updatedOperations = Object.fromEntries(
        Object.entries(jsonObjectHistory.operation).map(([key, value]) => [Number(key) + 1, value])
    );

    // Объединяем новую операцию и сдвинутые операции
    jsonObjectHistory.operation = { ...newOperation, ...updatedOperations };

    createHistory('history', window.appData.history || {}, groupIndex);
    initializeDragAndDrop();
}


//функция Dragg-and-Dropp с проверкой инициализации перед привязкой обработчиков
export function initializeDragAndDrop() {
  const toolsData = window.appData.tools;
  const cellData = window.appData.сells;
  if (!toolsData) {
    console.warn('Данные инструментов ещё не загружены');
    return;
  }
  // jsonObjectTools = toolsData;
  const draggableElements = document.querySelectorAll(".draggable");
  draggableElements.forEach(draggable => {
    if (!draggable.dataset.initialized) {
      draggable.setAttribute("draggable", true);
      draggable.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/plain", draggable.querySelector(".toolName").textContent);
        event.dataTransfer.setData('plansIndex', draggable.dataset.plansIndex);
        event.dataTransfer.setData('groupIndex', draggable.dataset.groupIndex);
        event.dataTransfer.setData('valueIndex', draggable.dataset.valueIndex);
        event.dataTransfer.setData('planName', draggable.dataset.planName);
      });

      draggable.dataset.initialized = "true"; // Пометка, что обработчик добавлен
    }
  });

  const droppableElements = document.querySelectorAll(".droppable");
  droppableElements.forEach(droppable => {
    if (!droppable.dataset.initialized) {
      droppable.addEventListener("dragover", (event) => {

        const CursorCellId = droppable.id;  // Получаем ID ячейки, на которую навели курсор
        const CursorCell = searchCellById(CursorCellId);  // Ищем ячейку по ID

        if (CursorCell.block == false) {
            event.preventDefault(); // Разрешает сброс в эту область
        }
    });

      droppable.addEventListener("drop", (event) => {
        event.preventDefault();
        const toolName = event.dataTransfer.getData("text/plain");
        const planName = event.dataTransfer.getData("planName");
        const plansIndex = event.dataTransfer.getData('plansIndex');
        const groupIndex = event.dataTransfer.getData('groupIndex');
        const toolIndex = event.dataTransfer.getData('valueIndex');

        // Извлечение id ячейки
        const targetCell = event.target;
        const cellId = targetCell.id;

    // console.log(plansIndex)
    // console.log(groupIndex)
    // console.log(toolIndex)

        updateToolsJSON(toolsData, plansIndex, groupIndex, toolIndex);
        updateCellsJSON(cellData, planName, toolName, cellId);
        updateJsonHistory(window.appData.history || {}, planName, groupIndex, toolName, cellId);
        // console.log(toolsData);
      });

      droppable.dataset.initialized = "true"; // Пометка, что обработчик добавлен
    }
  });
}
