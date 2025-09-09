
import { generateJsonTool } from '../massload/JSON_generators.js';
//import { generateJsonOperations } from './JSON_generators.js';
//import { generateJsonCells } from './JSON_generators.js';
//import { createTools } from './createTools.js';
//import { createHistory } from './createHistory.js';
import { createCells } from './createCells.js';
import { generateJsonCellsDrop } from './JSON_drop_generators.js';
import { createToolForDrop } from './createToolForDrop.js'
import { generateJsonToolsDrop } from './JSON_drop_generators.js'
import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.appData = window.appData || {};           // turn0search0
window.appData.story = window.appData.story || {};
window.appData.tools = window.appData.tools || {};
//export const jsonObjectTools = generateJsonTool(8, 4, 2);
//export const jsonCellsDrop = generateJsonCellsDrop(32, 32, jsonObjectTools);
//export const jsonHistoryDrop = {};

// Функция для получения JSON-данных через эндпоинт
export async function fetchCellMapData() {
    const url = "../backend/cells_map/1";
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        window.appData.сells = jsonData;
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

/*
 * Функция загрузки и сохранения JSON-ячеек.
 * Возвращает Promise, чтобы можно было ждать результата.
 */
export function initCellsData() {
    return fetchCellMapData()
      .then(сells => {
        window.appData.сells = сells;               // turn1search0
        return сells;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
}


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    initCellsData().then(cells => {
        if (cells) {
            nav_btn_add(element_name);
            navbar_add(element_name);
            window.appData.tools = generateJsonToolsDrop(window.appData.сells); //export const jsonToolForDrop
            createCells('cells-container', window.appData.сells); //jsonCellsDrop
            createToolForDrop('tools-container', window.appData.tools);
        }
    });
}

// Делаем функцию доступной глобально
window.initialization = initialization;