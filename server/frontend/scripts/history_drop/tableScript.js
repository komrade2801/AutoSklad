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
function openModalCell(massDropId) {

    if (isNaN(massDropId)) {
      console.error("Не удалось извлечь номер загрузки");
      return;
    }

    $('#random_drop_table').bootstrapTable('load', []);

    show('flex');  // Открываем модальное окно

    $('#random_drop_table').bootstrapTable('refreshOptions', {'height': $("#random_drop_div").height()});
    $('#random_drop_table').bootstrapTable('showLoading');

    initData(`../backend/random_drop?ID_drop=${massDropId}`)
      .then(data => {
        if (data) {
          window.jsonHistoryRandomdrop = data;
          createTableRandomLoad(data);
        }
      })
      .catch(err => console.error("Ошибка загрузки данных:", err));
}

function createTableRandomLoad(data) {
    console.log(data);

    if (data != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#random_drop_table').bootstrapTable('load', data.operation);
        $('#random_drop_table').bootstrapTable('hideLoading');
    }
}

// Функция для отображения модального окна
var show = function (state) {
    document.getElementById('modal_window_details').style.display = state;
    document.getElementById('membrane').style.display = state;
}

window.show = show;
