
import { generateTableHistoryDrop } from './generateTableHistoryDrop.js';
import { generatePrintTable, printElement } from './generate_print_table.js';


import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.appData = window.appData ?? {};
window.appData.history_drops = window.appData.history_drops || {};

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
function initData(url) {
    return fetchData(url)
      .then(data => {
        return data;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
}
window.initData = initData;

function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);

    $('#history_drop_table').bootstrapTable({
        exportOptions: {
            fileName: 'История загрузок',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#history_drop_div").height()
    });
    $('#history_drop_table').bootstrapTable('showLoading');

    $('#random_drop_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список загрузки',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#random_drop_div").height()
    });
    $('#random_drop_table').bootstrapTable('showLoading');

    const url = "../backend/history_drops";
// ?device_number=+device_number
    initData(url).then(data => {
        if (data) {
            window.appData.history_drops = data;
            generateTableHistoryDrop(window.appData.history_drops, 'column-1');
        }
    });
}

// Делаем функцию доступной глобально
window.initialization = initialization;

function printMassDrop(e) {
//    e.stopPropagation();

    // Генерируем таблицу
    generatePrintTable();

    // Печатаем только содержимое printArea
    let print_area = document.getElementById('printArea')
    console.log(print_area);
    printElement(print_area);
}

window.printMassDrop = printMassDrop;
window.printMassLoad = printMassDrop; // Для совместимости с HTML