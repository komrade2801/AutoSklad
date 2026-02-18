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
//    const allToolNames = new Set();
//    allPlans.forEach(plan => {
//        plan.tools.forEach(tool => {
//            allToolNames.add(tool.name); // Или другое поле, например, tool.type + " " + tool.size
//        });
//    });

    // 2. Формируем итоговый объект
    const jsonAllPlans = [];
    allPlans.forEach((plan, index) => {
        console.log(plan, " - ", index)
        // Создаем объект tools с динамическими ключами
//        const tools = {};
//        plan.tools.forEach(tool => {
//            console.log(tool)
//            tools[tool.name] = tool.tool_types_count; // Логика может быть сложнее
//        });
//        allToolNames.forEach(toolName => {
//            // Проверяем, есть ли инструмент в текущем плане
//            const toolInPlan = plan.tools.find(t => t.name === toolName);
//            tools[toolName] = toolInPlan ? "1" : "None"; // Логика может быть сложнее
//        });

        // Формируем запись плана
        jsonAllPlans.push({
            id: plan.id,
            enterprise: plan.enterprise,
            barcode: plan.barcode,
            designation: plan.designation,
            name: plan.name,
            description: plan.description,
            tools: plan.tools
        });
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

    $('#plans_table').bootstrapTable({
        toolbar: '#customToolsToolbar',
        exportOptions: {
            fileName: 'Список чертежей',
            pdfmake: {
                enabled: true,
                docDefinition: {
                    pageMargins: [ 20, 20, 20, 20 ]
                }
            }
        },
        height: $("#plans_div").height()
    });
    $('#plans_table').bootstrapTable('showLoading');

    // Выравниваем тулбар после загрузки данных
    $('#plans_table').on('load-success.bs.table', function() {
        if (window.alignToolbar) {
            window.alignToolbar('#plans_table');
        }
        // Перемещаем кастомные кнопки в fixed-table-toolbar
        moveCustomToolbar('#plans_table', '#customToolsToolbar');
    });

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

    if (!allPlansArray || allPlansArray.length === 0) {
      createTableAllPlans('column-1', []);
      return;
    }

    jsonAllPlans = processAllPlans(allPlansArray); // ✅ Теперь можно перезаписать
    if (jsonAllPlans !== null){
      console.log(jsonAllPlans);
      createTableAllPlans('column-1', jsonAllPlans);
    } else {
      createTableAllPlans('column-1', []);
    }
  } catch (error) {
    console.error('Ошибка при получении данных с API:', error);
    $('#plans_table').bootstrapTable('hideLoading');
  }
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