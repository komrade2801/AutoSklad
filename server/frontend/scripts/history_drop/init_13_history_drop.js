import { generateTableHistoryDrop } from './generateTableHistoryDrop.js';
import { jsonHistoryLoads } from '../../JSONs/history_loads.js';

import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    generateTableHistoryDrop(jsonHistoryLoads, 'column-1');
}

// Делаем функцию доступной глобально
window.initialization = initialization;