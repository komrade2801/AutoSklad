//import { generateJsonTool } from './JSON_generators.js';
//import { generateJsonOperations } from './JSON_generators.js';
//import { generateJsonCells } from './JSON_generators.js';
//import { createTools } from './createTools.js';
//import { createHistory } from './createHistory.js';
//import { createCells } from './createCells.js';
//import { initializeDragAndDrop } from './drag_and_drop.js';
import { generateJsonAllTool } from './JSON_generate_all_tools.js'
import { generateTableAllTools } from './createTableAllTools.js'
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

//export const jsonObjectCells = generateJsonCells(32, 32);
export const jsonObjectAllTools = generateJsonAllTool(3);
//export const jsonObjectHistory = {};


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    generateTableAllTools('column-1', jsonObjectAllTools);
    //createCells('cells-container', jsonObjectCells);
    //createTools('tools-container', jsonObjectTools);
    //createHistory('history', jsonObjectHistory);
    //initializeDragAndDrop()
}

// Делаем функцию доступной глобально
window.initialization = initialization;