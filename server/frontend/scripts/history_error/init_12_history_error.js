//alert(1);
import { generateTableHistoryError } from './generateTableHistoryError.js';
import { jsonHistoryError } from '../../JSONs/history_error.js';
//import { createTools } from './createTools.js';
//import { createHistory } from './createHistory.js';
//import { createCells } from '../screen_2_mass_load/createCells.js';
//import { generateJsonCellsDrop } from '../screen_3_mass_drop/JSON_drop_generators.js';
//import { createToolForDrop } from './createToolForDrop.js'
//import { generateJsonToolsDrop } from './JSON_drop_generators.js'

import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

//export const jsonObjectTools = generateJsonTool(8, 4, 2);
//export const jsonCellsDrop = generateJsonCellsDrop(32, 32, jsonObjectTools);
//export const jsonToolForDrop = generateJsonToolsDrop(jsonCellsDrop)
//export const jsonHistoryDrop = {};

function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    //createCells('cells-container', jsonCellsDrop);
    //alert(2);
    generateTableHistoryError(jsonHistoryError, 'column-1');
    //createHistory('history', jsonHistoryDrop);
}

// Делаем функцию доступной глобально
window.initialization = initialization;