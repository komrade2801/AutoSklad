
import { generateTableHistoryLoad } from './generateTableHistoryLoad.js';


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
    const url = "../backend/history_loads";
// ?device_number=+device_number
    initData(url).then(data => {
        if (data) {
            window.appData.history_loads = data;
            nav_btn_add(element_name);
            navbar_add(element_name);
            generateTableHistoryLoad(window.appData.history_loads, 'column-1');
        }
    });
    
}

// Делаем функцию доступной глобально
window.initialization = initialization;