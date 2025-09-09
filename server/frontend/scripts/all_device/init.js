import { createTableAllDevice } from './createTableAllDevice.js';
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';



window.jsonAllDevice = window.jsonAllDevice || {};

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


async function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
        return;
    }
    nav_btn_add(element_name);
    navbar_add(element_name);

   initData("../backend/all_device/").then(data => {
        if (data) {
            window.jsonAllDevice = data['devices'];
            createTableAllDevice('column-1', window.jsonAllDevice);
        }
    });
}

// Делаем функцию доступной глобально
window.initialization = initialization;
