//alert(1);
//import { generateJsonTool } from '../screen_2_mass_load/JSON_generators.js';
import { jsonHistoryWriteOff } from '../../JSONs/history_write_off.js';
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

//export const jsonHistoryWriteOff = ;

function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    //createCells('cells-container', jsonCellsDrop);
    //alert(2);
    //createToolForDrop('tools-container', jsonToolForDrop);
    //createHistory('history', jsonHistoryDrop);
    console.log("Завелось")
}

// Делаем функцию доступной глобально
window.initialization = initialization;