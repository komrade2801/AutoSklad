//alert(1);
//import { generateToolsSelection } from './generate_tools_selection.js';
import { generateTools } from './generateTools.js?v=1';
import { createHistory } from './selected_tools.js';
//import { jsonToolLibrary } from '../../JSONs/tool_library.js';
//import { jsonObjectTools } from '../../JSONs/all_tools.js';
import { initializeDragAndDrop } from './drag_and_drop.js';
//import { createHistory } from './createHistory.js';
//import { createCells } from '../screen_2_mass_load/createCells.js';
//import { generateJsonCellsDrop } from '../screen_3_mass_drop/JSON_drop_generators.js';
//import { createToolForDrop } from './createToolForDrop.js'
//import { generateJsonToolsDrop } from './JSON_drop_generators.js'
import { nav_btn_add } from '../nav_btn_load.js';
// import { loadToolLibraryTable } from './createTableToolLibrary.js?v=2';
// import { fetchToolLibraryData } from './createTableToolLibrary.js?v=2';

import { navbar_add } from '../navbar.js';


//export const jsonObjectTools = generateJsonTool(8, 4, 2);
//export const jsonCellsDrop = generateJsonCellsDrop(32, 32, jsonObjectTools);
//export const jsonToolForDrop = generateJsonToolsDrop(jsonCellsDrop)
window.tool_library = {}
window.jsonLibrary = {};           // turn0search0
window.jsonPlan = {};

window.appData = window.appData || {};
window.appData.history = window.appData.history || {};
window.appData.history.operation = window.appData.history.operation || {};  // словарь со всеми операциями
window.appData.history.table = window.appData.history.table || [];  // список для таблицы в интерфейсе
window.appData.history.list = window.appData.history.list || [];  // список для передачи в бэкенд
window.appData.tools = window.appData.tools || [];

// Функция для получения JSON-данных через эндпоинт
export async function fetchToolLibraryData(device_number) {
    console.log('fetchToolLibraryData');
    const url = "../backend/get_tool_types_from_db?device_number="+device_number;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        console.log('window.tool_library');
        console.log(jsonData);
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

export function initToolsData(device_number) {
    return fetchToolLibraryData(device_number)
      .then(data => {
//        window.tool_library = data;               // turn1search0
//        window.jsonLibrary = data;
        window.appData.tools = data.tools;
        return data;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
  }

async function initialization(element_name) {
    console.log('initialization');
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    await Promise.allSettled([
        nav_btn_add(element_name),
        navbar_add(element_name)
    ]);

    $('#loadable_tools_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список инструментов из библиотеки',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#loadable_tools_div").height()
    });
    $('#loadable_tools_table').bootstrapTable('showLoading');

    $('#selected_tools_table').bootstrapTable({
        exportOptions: {
            fileName: 'История текущей загрузки',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#selected_tools_div").height()
    });
    $('#selected_tools_table').bootstrapTable('load', []);

    let device_number = 1;
    initToolsData(device_number).then(data => {
//        jsonToolLibrary = await fetchToolLibraryData();
        generateTools();
        initializeDragAndDrop();
    });

    $("#customToolsToolbar").width($("#column-2").width());
    //alert(2);
    // const jsonObjectTools = await fetchToolLibraryData();
    //generateToolsSelection(jsonObjectTools);
}

// Делаем функцию доступной глобально
window.initialization = initialization;