import { createTableToolLibrary } from './createTableToolLibrary.js?v=3';
//import { loadToolLibraryTable } from './createTableToolLibrary.js?v=3';
import { fetchToolLibraryData } from './createTableToolLibrary.js?v=3';

//import { jsonToolLibrary } from '../../JSONs/tool_library.js';
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

import { loadGroupsData } from './fillSelectGroups.js?v=3'

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
        height: $("#tool_library_div").height()
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
        height: $("#group_library_div").height()
    });
    $('#group_library_table').bootstrapTable('showLoading');

    loadToolLibraryTable(device_number);
    loadGroupsData(device_number);

    // Восстанавливаем выбранную вкладку из localStorage
    // Используем setTimeout, чтобы убедиться, что все элементы DOM готовы
    setTimeout(() => {
        const savedTab = localStorage.getItem('toolLibraryActiveTab');
        if (savedTab === 'groups') {
            // Устанавливаем radio button на "Группы"
            $('#tab2').prop('checked', true);
            // Переключаем отображение
            if (typeof window.changeTab === 'function') {
                window.changeTab("#group_library_div", "#tool_library_div");
            }
        } else {
            // По умолчанию "Инструменты"
            $('#tab1').prop('checked', true);
            if (typeof window.changeTab === 'function') {
                window.changeTab("#tool_library_div", "#group_library_div");
            }
        }
    }, 100);
}

// Делаем функцию доступной глобально
window.initialization = initialization;


// Функция для загрузки данных и создания таблицы
async function loadToolLibraryTable(device_number) {
    const jsonToolLibrary = await fetchToolLibraryData(device_number);
    if (jsonToolLibrary) {
        createTableToolLibrary(jsonToolLibrary);
    } else {
        console.error("Не удалось загрузить данные для таблицы.");
    }
}
window.loadToolLibraryTable = loadToolLibraryTable;