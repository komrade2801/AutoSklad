import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

window.jsonUsers = window.jsonUsers || {};

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
 * Функция загрузки и сохранения JSON.
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
    nav_btn_add(element_name);
    navbar_add(element_name);
    console.log($("#users_div").height());

    $('#users_table').bootstrapTable({
        exportOptions: {
            fileName: 'Список пользователей',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#users_div").height()
    });
    $('#users_table').bootstrapTable('showLoading');

    loadUsers();
}

function loadUsers() {
    initData("../backend/all_users/").then(data => {
        if (data) {
            window.jsonUsers = data['users'];

            console.log(data);
            generateTableUsers();
        }
    });
}
window.loadUsers = loadUsers;

// Делаем функцию доступной глобально
window.initialization = initialization;

function generateBarcode() {
    const inputBarcode      = document.getElementById('input-barcode');
    const inputCode         = document.getElementById('input-code');

    const barcode = Date.now();            // или любая ваша логика
    const code    = Math.floor(Math.random() * 9000) + 1000;
    inputBarcode.value = barcode;
    inputCode.value    = code;
}

window.generateBarcode = generateBarcode;