//alert(1);
//import { generateToolsSelection } from './generate_tools_selection.js';
//import { jsonObjectTools } from '../../JSONs/all_tools.js';
//import { createTools } from './createTools.js';
//import { createHistory } from './createHistory.js';
//import { createCells } from '../screen_2_mass_load/createCells.js';
//import { generateJsonCellsDrop } from '../screen_3_mass_drop/JSON_drop_generators.js';
//import { createToolForDrop } from './createToolForDrop.js'
//import { generateJsonToolsDrop } from './JSON_drop_generators.js'

import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

import { loadGroupsData } from '../groups/fillSelectGroups.js?v=3'


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

    var select_element = document.getElementById('select_parent_group');
    let device_number = 1;
    loadGroupsData(select_element, device_number);

    //createCells('cells-container', jsonCellsDrop);
    //alert(2);
    //generateToolsSelection(jsonObjectTools);
    //createHistory('history', jsonHistoryDrop);
}

// Делаем функцию доступной глобально
window.initialization = initialization;