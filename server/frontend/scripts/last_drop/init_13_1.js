import { jsonHistoryRandomLoad } from '../../JSONs/json_random_load.js';
//import { generateJsonOperations } from './JSON_generators.js';
import { generateJson } from './generateJSON_cells.js';
//import { createTools } from './createTools.js';
import { createHistory } from './createHistory.js';
import { createCells } from './createCells.js';
//import { initializeDragAndDrop } from './drag_and_drop.js';
//import { jsonObjectHistory } from '../../JSONs/history.js'
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';


export const jsonObjectCells = generateJson();
//export const jsonObjectTools = generateJsonTool(10, 5, 7);
//export const jsonObjectHistory = {};


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    console.log("Функция инициализатион успешно вызвана")
    createCells('cells-container', jsonObjectCells);
    //createTools('tools-container', jsonObjectTools);
    createHistory('history', jsonHistoryRandomLoad);
    //initializeDragAndDrop()
}

// Делаем функцию доступной глобально
window.initialization = initialization;

