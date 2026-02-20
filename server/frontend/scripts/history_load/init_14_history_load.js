
import { generateTableHistoryLoad } from './generateTableHistoryLoad.js';
import { generatePrintTable, printElement } from './generate_print_table.js';


import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';

window.appData = window.appData ?? {};
window.appData.history_loads = window.appData.history_loads || {};

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
    console.log('initialization');

    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);

    console.log('2');

    $('#history_load_table').bootstrapTable({
        exportOptions: {
            fileName: 'История загрузок',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#history_load_div").height()
    });
    $('#history_load_table').bootstrapTable('showLoading');

    $('#random_load_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список загрузки',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
//        height: $("#random_load_div").height()
    });
    $('#random_load_table').bootstrapTable('showLoading');

    const url = "../backend/history_loads";
// ?device_number=+device_number
    initData(url).then(data => {
        if (data) {
            window.appData.history_loads = data;
            generateTableHistoryLoad();
        }
    });
    
}

// Делаем функцию доступной глобально
window.initialization = initialization;

function printMassLoad(e) {
//    e.stopPropagation();

    // Генерируем таблицу
    generatePrintTable();

    // Печатаем только содержимое printArea
    let print_area = document.getElementById('printArea')
    console.log(print_area);
    printElement(print_area);
}

window.printMassLoad = printMassLoad;