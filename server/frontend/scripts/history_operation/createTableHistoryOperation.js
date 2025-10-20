// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_cell').style.display = state
    document.getElementById('membrane').style.display = state
}

export function createTableHistoryOperation(containerId, jsonHistoryOperation) {

    const container = document.getElementById(containerId);

    console.log('createTableHistoryOperation')
    const data = jsonHistoryOperation["operation"];
    console.log(data)

    if (data != undefined) {
        $('#table').bootstrapTable('load', data);
        $('#table').bootstrapTable('hideLoading');
    }


//    let table = document.createElement("table");
//    table.style.width = "100%";
//
//    let thead = document.createElement("thead");
//    let headerRow = document.createElement("tr");
//    ["Дата", "Название операции", "Инструмент", "Чертёж", "Пользователь", "Аппарат"].forEach(text => {
//        let th = document.createElement("th");
//        th.textContent = text;
//        th.style.border = "1px solid"
//        headerRow.appendChild(th);
//    });
//    thead.appendChild(headerRow);
//    table.appendChild(thead);
//
//    let tbody = document.createElement("tbody");
//
//    // Должны проходить итерацию по jsonHistoryOperation.operation, а не по jsonHistoryOperation
//    Object.values(jsonHistoryOperation.operation).forEach(operation => {
//        let row = document.createElement("tr");
//
//        [operation.date, operation.name_operation, operation.tool, operation.plan, operation.user, operation.device].forEach(value => {
//            let td = document.createElement("td");
//            td.textContent = value;
//            td.style.border = "1px solid"
//            row.appendChild(td);
//        });
//
//        tbody.appendChild(row);
//    });
//
//    if (Object.keys(jsonHistoryOperation.operation).length === 0) {
//        let emptyRow = document.createElement("tr");
//        let emptyTd = document.createElement("td");
//        emptyTd.colSpan = 6;
//        emptyTd.textContent = "История операций пуста";
//        emptyTd.style.textAlign = "center";
//        emptyTd.style.fontStyle = "italic";
//        emptyTd.style.border = "1px solid"
//        emptyRow.appendChild(emptyTd);
//        tbody.appendChild(emptyRow);
//    }
//
//    table.appendChild(tbody);
//    container.appendChild(table);
}

export function DoOnCellHtmlData(cell, row, col, data) {
    var result = "";

    if(typeof data !== 'undefined' && data != "")
    {
        var html = $.parseHTML(data);

        $.each( html, function() {
            if ( typeof $(this).html() === 'undefined' )
                result += $(this).text();
            else if ( typeof $(this).attr('class') === 'undefined' || $(this).hasClass('th-inner') === true )
                result += $(this).html();
        });
    }
    return result;
}


// Функция для открытия модального окна
function openModalTools() {
    // Заполняем данные в модальном окне (это может быть динамическое содержимое)
    //document.querySelector('.cell_number').textContent = 'Ячейка № ' + cellNumber;
    //document.querySelector('img').src = 'image_' + cellNumber + '.jpg'; // Изменить путь к изображению
    //document.querySelector('.tool_group').textContent = 'Группа: Группа ' + cellNumber;
    //document.querySelector('.tool_name').textContent = 'Инструмент: ' + toolName;
    //document.querySelector('.plan_name').textContent = 'Чертёж: ' + planName;

    show('flex');  // Открываем модальное окно
}
