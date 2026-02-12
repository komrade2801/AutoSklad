function dateFormatter(value, row, index, field) {

    const [time, date] = row.date.split(" ");
    const [hour, minute, second] = time.split(":");
    const [day, month, year] = date.split(".");
    return new Date(year, month - 1, day, hour, minute, second);
}

//column custom formatter
function dateTimeSorter(a, b) {

    var a_number = datnum(a, "HH:mm:ss DD.MM.YYYY");
    var b_number = datnum(b, "HH:mm:ss DD.MM.YYYY");

    a = a_number;
    b = b_number;
    if (a > b) return 1;
    if (a < b) return -1;
    return 0;
}

//return integer
function datnum(dateString, format) {
    var date;
    try {
        date = moment(dateString, format);
        return date.valueOf();
    //    date = new Date(dateString)
    //    return date.getTime();
    }catch {
        return 0;
    }

    return 0;
}

function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Info button
     let infoButton = document.createElement("i");
     infoButton.className = "bi bi-info-square action-button";
     infoButton.title = "Информация об операции";

     infoButton.addEventListener('click', async function () {

        console.log(row);
        console.log(row.mass_id);
        openModalCell(row.mass_id)
     });

     actionsDiv.appendChild(infoButton);

     return actionsDiv;
}

// Функция для открытия модального окна
function openModalCell(massLoadId) {

    if (isNaN(massLoadId)) {
      console.error("Не удалось извлечь номер загрузки");
      return;
    }

    $('#random_load_table').bootstrapTable('load', []);

    show('flex');  // Открываем модальное окно

    $('#random_load_table').bootstrapTable('refreshOptions', {'height': $("#random_load_div").height()});
    $('#random_load_table').bootstrapTable('showLoading');

    initData(`../backend/random_load?ID_load=${massLoadId}`)
      .then(data => {
        if (data) {
          window.jsonHistoryRandomLoad = data;
          createTableRandomLoad(data);
        }
      })
      .catch(err => console.error("Ошибка загрузки данных:", err));
}

function createTableRandomLoad(data) {
    console.log(data);

    if (data != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#random_load_table').bootstrapTable('load', data.operation);
        $('#random_load_table').bootstrapTable('hideLoading');
    }
//
//    let table = '<table style="width: 100%;">';
//    table += '<tr><th>Ячейка</th><th>Инструмент</th><th>Группа</th><th>Чертёж</th></tr>';
//
//    // Сортировка по номеру ячейки
//    const sortedKeys = Object.keys(data.operation).sort((a, b) => a - b);
//
//    sortedKeys.forEach(key => {
//        const { cell, tool, plan, group } = data.operation[key];
//        table += `<tr>
//                    <td>${cell}</td>
//                    <td>${tool}</td>
//                    <td>${group}</td>
//                    <td>${plan}</td>
//                  </tr>`;
//    });
//
//    table += '</table>';
//
//    // Вставка в указанный контейнер
//    const container = document.getElementById(containerId);
//    if (container) {
//        container.innerHTML = table;
//    } else {
//        console.error(`Контейнер с id "${containerId}" не найден.`);
//    }
}

// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_details').style.display = state;
    document.getElementById('membrane').style.display = state;
}

window.show = show;
