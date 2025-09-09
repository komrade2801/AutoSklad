//import { generateJsonTool } from './JSON_generators.js';
//import { generateJsonOperations } from './JSON_generators.js';
//import { generateJsonCells } from './JSON_generators.js';
//import { createTools } from './createTools.js';
//import { createHistory } from './createHistory.js';
//import { createCells } from './createCells.js';
//import { createTableAllPlans } from './createTableAllPlans.js'
//import { jsonAllPlans } from '../all_plans.js'
import { createTableActualNorms } from './createTableActualNorms.js'
import { jsonActualNorms } from '../../JSONs/actual_norms.js'

import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

//export const jsonObjectCells = generateJsonCells(32, 32);
//export const jsonObjectHistory = {};


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    //createCells('cells-container', jsonObjectCells);
    //createTools('tools-container', jsonObjectTools);
    //createTableAllPlans(, jsonAllPlans);
    //initializeDragAndDrop()
    createTableActualNorms('column-1', jsonActualNorms);
}

// Делаем функцию доступной глобально
window.initialization = initialization;