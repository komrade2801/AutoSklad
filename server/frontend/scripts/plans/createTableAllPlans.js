// Функция для отображения модального окна с инструментами
var showTool = function (state) {
    document.getElementById('modal_window_tool').style.display = state
    document.getElementById('membrane').style.display = state
}

window.showTool = showTool;

// Функция для отображения модального окна Штрихкода
var showBarcode = function (state) {
    document.getElementById('modal_window_barcode').style.display = state
    document.getElementById('membrane').style.display = state
}


/**
 * Устанавливает в модалку URL изображения и открывает её.
 * @param {number} planId 
 */
export function openModalBarcode(planId) {
  // Подставляем ID в текст
  document.getElementById('modal_plan_id').textContent = planId;

  // Формируем URL к вашему эндпоинту
  const img = document.getElementById('modal_barcode_img');
  img.src = `/backend/plan_barcode?barcode_index=${encodeURIComponent(planId)}`;

  // Очистим старое, если вдруг
  img.onerror = () => {
    console.error('Не удалось загрузить штрих‑код');
    img.alt = 'Ошибка загрузки';
  };

  // Открываем модалку
  showBarcode('flex');
}

/**
 * Печать содержимого модалки (только картинки).
 */
export function printBarcode() {
    const img = document.getElementById('modal_barcode_img');
    const w = window.open('');
    w.document.write(`<img src="${img.src}" onload="window. print();window.close()">`);
    w.document.close();
}

export function createTableAllPlans(containerId, jsonAllPlans) {

    console.log('createTableAllPlans');
    console.log(jsonAllPlans);
    const data = jsonAllPlans["plans"];
    console.log(data);

    if (jsonAllPlans != undefined) {
        $('#plans_table').bootstrapTable('load', jsonAllPlans);
        $('#plans_table').bootstrapTable('hideLoading');
    }

//    const container = document.getElementById(containerId);
//
//    let table = document.createElement("table");
//    table.width = "100%";
//    table.border = "1";
//
//    let thead = document.createElement("thead");
//    let headerRow = document.createElement("tr");
//    ["Название проекта", "Номер чертежа", "Название детали", "Список инструмента", "Штрих-код чертежа"].forEach(text => {
//        let th = document.createElement("th");
//        th.textContent = text;
//        headerRow.appendChild(th);
//    });
//    thead.appendChild(headerRow);
//    table.appendChild(thead);
//
//    let tbody = document.createElement("tbody");
//    Object.values(jsonAllPlans).forEach(plan => {
//        console.log(plan);
//        let row = document.createElement("tr");
//        // Исправлено: поменяны местами plan.name и plan.numberPlan
//        // Заголовки: "Название проекта", "Номер чертежа", "Название детали"
//        // Данные: enterprise, numberPlan (designation), name
//        [plan.enterprise, plan.numberPlan, plan.name].forEach(value => {
//        //[plan.nameProject, plan.numberPlan, plan.nameDetail].forEach(value => {, plan.description, plan.barcode
//            let td = document.createElement("td");
//            td.textContent = value;
//            row.appendChild(td);
//        });
//
//        let actionTd = document.createElement("td");
//        let buttonTools = document.createElement("button");
//        buttonTools.textContent = "Список инструмента";
//        buttonTools.addEventListener('click', function() {
//            openModalTools(plan.numberPlan, plan.tools);
//        });
//        actionTd.appendChild(buttonTools);
//
//        let barcode = document.createElement("td");
//        let buttonBarcode = document.createElement("button");
//        buttonBarcode.textContent = "Штрих-код чертежа";
//        buttonBarcode.addEventListener('click', function() {
//            openModalBarcode(plan.barcode);
//        });
//        barcode.appendChild(buttonBarcode);
//
//        row.appendChild(actionTd);
//        row.appendChild(barcode);
//
//        tbody.appendChild(row);
//    });
//
//    table.appendChild(tbody);
//    container.appendChild(table);
}

//
//    // Функция для открытия модального окна
//function openModalTools(plan_name, plan_tools) {
//    // Подставляем ID в текст
//    document.getElementById('modal_plan_tools_id').textContent = plan_name;
//
//    let tool_list_element = document.getElementById('tool_list');
//    tool_list_element.innerHTML = '';
//
//    plan_tools.forEach(tool => {
//        const tool_row = document.createElement('div');
//        tool_row.style = 'padding-top: 20px;'
//        tool_row.innerHTML = tool.name + '\t-\t' + tool.tool_types_count + ' шт.';
//        tool_list_element.appendChild(tool_row);
//    })
//
//    showTool('flex');  // Открываем модальное окно
//}


window.showBarcode = showBarcode;
