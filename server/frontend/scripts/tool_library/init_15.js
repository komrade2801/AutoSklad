import { createTableToolLibrary } from './createTableToolLibrary.js?v=3';
import { loadToolLibraryTable } from './createTableToolLibrary.js?v=3';
import { fetchToolLibraryData } from './createTableToolLibrary.js?v=3';

//import { jsonToolLibrary } from '../../JSONs/tool_library.js';
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

//export const jsonObjectCells = generateJsonCells(32, 32);
//export const jsonObjectHistory = {};


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    let device_number = 1;
    nav_btn_add(element_name);
    navbar_add(element_name);
    loadToolLibraryTable("column-1", device_number);

    $('#tool_library_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список инструментов',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
    });
    $('#tool_library_table').bootstrapTable('showLoading');

    $('#group_library_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список групп',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
    });
    $('#group_library_table').bootstrapTable('showLoading');
}

// Делаем функцию доступной глобально
window.initialization = initialization;