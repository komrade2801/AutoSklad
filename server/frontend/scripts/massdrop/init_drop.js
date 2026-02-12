import { generateJsonTool } from '../massload/JSON_generators.js';
import { createToolForDrop } from './createToolForDrop.js'
import { generateJsonToolsDrop } from './JSON_drop_generators.js'
import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.appData = window.appData || {};           // turn0search0
window.appData.story = window.appData.story || {};
window.appData.story.operation = window.appData.story.operation || {};  // словарь со всеми операциями
window.appData.story.table = window.appData.story.table || [];  // список для таблицы в интерфейсе
window.appData.story.list = window.appData.story.list || [];  // список для передачи в бэкенд
window.appData.tools = window.appData.tools || [];
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
        window.appData.cells = jsonData;
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
      .then(cells => {
        window.appData.cells = cells;               // turn1search0
        return cells;
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
    nav_btn_add(element_name);
    navbar_add(element_name);

    console.log($("#droppable_tools_div").height());

    $('#droppable_tools_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список загруженных инструментов',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#droppable_tools_div").height()
    });
    $('#droppable_tools_table').bootstrapTable('showLoading');

    $('#droppable_story_table').bootstrapTable({
        exportOptions: {
            fileName: 'История текущей выгрузки',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#droppable_story_div").height()
    });
    $('#droppable_story_table').bootstrapTable('load', []);

    initCellsData().then(cells => {
        if (cells) {

            window.appData.tools = generateJsonToolsDrop(cells); //export const jsonToolForDrop
//            createCells('cells-container', cells); //jsonCellsDrop
            createToolForDrop();
        }
    });
}

// Делаем функцию доступной глобально
window.initialization = initialization;