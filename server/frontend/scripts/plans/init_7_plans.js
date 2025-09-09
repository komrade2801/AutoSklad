//import { createTableAllPlans } from './createTableAllPlans.js'
//import { jsonAllPlans } from '../../JSONs/all_plans.js'
//import { nav_btn_add } from '../nav_btn_load.js';

//import { AllPlansApi } from '../cruds/api/AllPlansApi.js'
//import { ApiClient } from '../cruds/ApiClient.js'
//
//function initialization() {
////    console.log("Зашли в initialization")
////    // Создаем экземпляр API-клиента
////    const apiClient = new ApiClient('http://192.168.0.10/'); // Укажите базовый URL вашего API
////    const allPlansApi = new AllPlansApi(apiClient);
////
////    // Укажите номер устройства (deviceNumber), для которого загружаются планы
////    const deviceNumber = 1; // Здесь должен быть реальный номер устройства
////
////    // Выполняем запрос к API
////    allPlansApi.getAllPlansBackendAllPlansDeviceNumberGet(deviceNumber, (error, data) => {
////        if (error) {
////            console.error('Ошибка при загрузке планов:', error);
////            return;
////        }
////
////        // Сохраняем данные в jsonAllPlans и создаем таблицу
////        const jsonAllPlans = data; // Данные уже имеют структуру PlanResponse
//        createTableAllPlans('column-1', jsonAllPlans);
////    });
//}
//// Делаем функцию доступной глобально
//window.initialization = initialization;

import { createTableAllPlans } from './createTableAllPlans.js';
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

/**
 * Обрабатывает массив планов, формируя jsonAllPlans.
 * @param {Array} allPlans - Массив всех планов от эндпоинта.
 * @returns {Object} Результат в требуемом формате.
 */
function processAllPlans(allPlans) {
  if (!allPlans){
    return null;
  }
  else{
    // 1. Собираем ВСЕ уникальные имена инструментов из всех планов
    const allToolNames = new Set();
    allPlans.forEach(plan => {
        plan.tools.forEach(tool => {
            allToolNames.add(tool.name); // Или другое поле, например, tool.type + " " + tool.size
        });
    });

    // 2. Формируем итоговый объект
    const jsonAllPlans = {};
    allPlans.forEach((plan, index) => {
        // Создаем объект tools с динамическими ключами
        const tools = {};
        allToolNames.forEach(toolName => {
            // Проверяем, есть ли инструмент в текущем плане
            const toolInPlan = plan.tools.find(t => t.name === toolName);
            tools[toolName] = toolInPlan ? "1" : "None"; // Логика может быть сложнее
        });

        // Формируем запись плана
        jsonAllPlans[index] = {
            enterprise: plan.enterprise,
            barcode: plan.barcode,
            numberPlan: plan.designation,
            name: plan.name,
            description: plan.description,
            tools: tools
        };
    });

    return jsonAllPlans;
  }
}

async function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    nav_btn_add(element_name);
    navbar_add(element_name);
  try {
    const deviceNumber = 1; // можно изменить, если нужно другое устройство
    const response = await fetch(`/backend/get_all_plans/${deviceNumber}`,
//    const response = await fetch("/backend/all_plans/${deviceNumber}");
    {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Ошибка сервера: ${response.status}`);
    }


    // Теперь вызываем функцию, передавая полученные данные

    let jsonAllPlans = await response.json(); // Объявление через let
    let allPlansArray = jsonAllPlans.plans
    console.log(allPlansArray)
    jsonAllPlans = processAllPlans(allPlansArray); // ✅ Теперь можно перезаписать
    if (jsonAllPlans !== null){
      console.log(jsonAllPlans);
      createTableAllPlans('column-1', jsonAllPlans);
    }
  } catch (error) {
    console.error('Ошибка при получении данных с API:', error);
  }
}

// Делаем функцию доступной глобально
window.initialization = initialization;
