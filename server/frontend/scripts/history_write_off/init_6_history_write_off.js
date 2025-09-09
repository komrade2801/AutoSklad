
import { createHistoryWriteOff } from './create_table_history_write_off.js'
import { jsonHistoryWriteOff } from '../../JSONs/history_write_off.js'
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
    createHistoryWriteOff('column-1', jsonHistoryWriteOff);
}

// Делаем функцию доступной глобально
window.initialization = initialization;