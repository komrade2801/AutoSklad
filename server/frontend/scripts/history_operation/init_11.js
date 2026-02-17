//import { populateUserDropdown } from './filter_handler.js'
//import { populatePlanDropdown } from './filter_handler.js'
//import { populateOperationTypeDropdown } from './filter_handler.js'
import { createTableHistoryOperation } from './createTableHistoryOperation.js'
import { DoOnCellHtmlData } from './createTableHistoryOperation.js'
import { generatePrintTable, printElement } from './generate_print_table.js'

// import { jsonHistoryOperation } from '../../JSONs/history_operation.js'

import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.appData = window.appData ?? {};
window.appData.jsonHistoryOperation = window.appData.jsonHistoryOperation || {};

// Функция для получения JSON-данных через эндпоинт
export async function fetchData(url) {
    try {

        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

/*
 * Функция загрузки JSON.
 * Возвращает Promise, чтобы можно было ждать результата.
 */
export function initData(url) {
    return fetchData(url)
      .then(data => {
        return data;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
}


function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    const url = "../backend/history-operation/1";
    const url_status = "../backend/status";

    $('#operation_history_table').bootstrapTable({
        exportOptions: {
            fileName: 'История операций',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            },
            onCellHtmlData: DoOnCellHtmlData
        },
//        height: $("#history_operation_div").height()
    });
    $('#operation_history_table').bootstrapTable('showLoading');

    // Выравниваем тулбар после загрузки данных
    $('#operation_history_table').on('load-success.bs.table', function() {
        if (window.alignToolbar) {
            window.alignToolbar('#operation_history_table');
        }
    });

    initData(url_status).then(data => {
        if (data) {
            window.appData.statusData = {};

            for (const status of data) {
                window.appData.statusData[status.id] = status.description;
            }

        }
    });

    initData(url).then(data => {
        if (data) {
            window.appData.jsonHistoryOperation = data;
            nav_btn_add(element_name);
            navbar_add(element_name);
            createTableHistoryOperation('column-1', window.appData.jsonHistoryOperation);
//            populateUserDropdown(window.appData.jsonHistoryOperation);
//            populatePlanDropdown(window.appData.jsonHistoryOperation);
//            populateOperationTypeDropdown(window.appData.jsonHistoryOperation);
        }
    });
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

// Делаем функцию доступной глобально
window.initialization = initialization;
window.alignToolbar = alignToolbar;

function printMassOperation(e) {
    // Генерируем таблицу
    generatePrintTable();

    // Печатаем только содержимое printArea
    let print_area = document.getElementById('printArea')
    console.log(print_area);
    printElement(print_area);
}

window.printMassOperation = printMassOperation;