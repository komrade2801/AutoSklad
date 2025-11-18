// import { generateJsonTool } from './JSON_generators.js';
// import { generateJsonOperations } from './JSON_generators.js';

import { generateJsonCells } from './JSON_generators.js';
import { createTools } from './createTools.js';
import { createHistory } from './createHistory.js';
import { createCells } from './createCells.js';
import { initializeDragAndDrop } from './drag_and_drop.js';
import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.appData = window.appData || {};           // turn0search0

// export const jsonObjectCells = generateJsonCells(32, 32);
//plansCount, groupsPerPlanCount, valuesPerGroupCount
// export let jsonObjectTools = {};// generate_json_tool();// generateJsonTool(1, 1, 1);//await fetchToolLibraryData();// 
export let jsonObjectHistory = {};
window.appData.history = jsonObjectHistory;

// function saveJsonLegacy(data, filename = 'data.json') {
//     const jsonStr = JSON.stringify(data, null, 2);
//     const blob = new Blob([jsonStr], { type: 'application/json' });
//     const url = URL.createObjectURL(blob);
  
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = filename;
//     document.body.appendChild(a);
//     a.click();
//     document.body.removeChild(a);
  
//     URL.revokeObjectURL(url);
//   }

// Функция для получения JSON-данных через эндпоинт
export async function fetchToolLibraryData(device_number) {
    const url = "../backend/mass_load_tools?device_number="+device_number;
    try {
        const response = await fetch(url, { redirect: "manual", credentials: "include" });
        if (response.type === "opaqueredirect") {
          // К сожалению, не можем узнать Location из JS из‑за CORS
          // Но можно догадаться: редирект всегда идёт на один и тот же URL
          window.location.href = "/mass_locked.html?token="+localStorage.getItem('token');
          return null;
        }

        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        window.appData.tools = jsonData;
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

// Функция для получения JSON-данных через эндпоинт
export async function fetchCellMapData() {
    const url = "../backend/cells_map/1";
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        window.appData.cells = jsonData;
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

/**
 * Функция загрузки и сохранения JSON-инструментов.
 * Возвращает Promise, чтобы можно было ждать результата.
 */
export function initToolsData(device_number) {
    return fetchToolLibraryData(device_number)
      .then(data => {
        // Стандартизация полей: добавить toolName, groupName, id к каждому инструменту
        if (data && data.plans) {
          for (const planKey in data.plans) {
            const plan = data.plans[planKey];
            for (const groupKey in plan.groups) {
              const group = plan.groups[groupKey];
              for (const valueKey in group.value) {
                const tool = group.value[valueKey];
                tool.toolName = tool.name;
                tool.groupName = group.name;
                // id уже есть из бэкенда
              }
            }
          }
        }
        window.appData.tools = data;               // turn1search0
        return data;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
  }

/**
 * Функция загрузки и сохранения JSON-ячеек.
 * Возвращает Promise, чтобы можно было ждать результата.
 */
export function initCellsData() {
    return fetchCellMapData()
      .then(сells => {
        window.appData.cells = сells;               // turn1search0
        return сells;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
  }

export async function loadToolTable(containerId, device_number) {
    jsonObjectTools = await fetchToolLibraryData(device_number);

    // saveJsonLegacy(jsonObjectTools);
    if (jsonObjectTools) {
        createTools(containerId, jsonObjectTools);
        createHistory('history', window.appData.history);
        initializeDragAndDrop(jsonObjectTools);
    } else {
        console.error("Не удалось загрузить данные для таблицы.");
    }
}


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    let device_number = 1;
    navbar_add(element_name);
    initToolsData(device_number).then(data => {
      if (data) {
        initCellsData().then(cells => {
            if (cells) {
                nav_btn_add(element_name);
                createCells('cells-container', window.appData.cells);
                createTools('tools-container', window.appData.tools);
                initializeDragAndDrop();
                createHistory('history', window.appData.history);
            }
        });
      }
    });
}

// Делаем функцию доступной глобально
window.initialization = initialization;
