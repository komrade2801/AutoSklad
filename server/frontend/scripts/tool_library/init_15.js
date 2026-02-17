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
        toolbar: '#customToolsToolbar',
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
        toolbar: '#customGroupsToolbar',
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

    // Выравниваем тулбар после загрузки данных
    $('#tool_library_table').on('load-success.bs.table', function() {
        if (window.alignToolbar) {
            window.alignToolbar('#tool_library_table');
        }
        // Перемещаем кастомные кнопки в fixed-table-toolbar
        moveCustomToolbar('#tool_library_table', '#customToolsToolbar');
    });

    $('#group_library_table').on('load-success.bs.table', function() {
        if (window.alignToolbar) {
            window.alignToolbar('#group_library_table');
        }
        // Перемещаем кастомные кнопки в fixed-table-toolbar
        moveCustomToolbar('#group_library_table', '#customGroupsToolbar');
    });

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

// Функция для выравнивания тулбара по заголовку таблицы
function alignToolbar(tableSelector) {
    const $table = $(tableSelector);
    const $bootstrapTable = $table.closest('.bootstrap-table');
    const $toolbar = $bootstrapTable.find('.fixed-table-toolbar');
    const $container = $bootstrapTable.find('.fixed-table-body');

    if ($container.length && $toolbar.length) {
        // Проверяем, есть ли скроллбар
        const tableHeight = $container.find('.table').height();
        const containerHeight = $container.height();
        const hasScrollbar = tableHeight > containerHeight;

        if (hasScrollbar) {
            $toolbar.css('margin-right', '17px');
        } else {
            $toolbar.css('margin-right', '0');
        }
    }
}

// Функция для перемещения кастомного тулбара в fixed-table-toolbar
function moveCustomToolbar(tableSelector, toolbarSelector) {
    const $table = $(tableSelector);
    const $bootstrapTable = $table.closest('.bootstrap-table');
    const $fixedToolbar = $bootstrapTable.find('.fixed-table-toolbar');
    const $customToolbar = $(toolbarSelector);

    if ($fixedToolbar.length && $customToolbar.length) {
        // Перемещаем кастомный тулбар в fixed-table-toolbar
        $fixedToolbar.append($customToolbar);
        $customToolbar.show();
    }
}

// Делаем функцию доступной глобально
window.initialization = initialization;
window.alignToolbar = alignToolbar;
window.moveCustomToolbar = moveCustomToolbar;


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