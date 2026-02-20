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
        openModalDetails(row.mass_id, row.date)
     });

     actionsDiv.appendChild(infoButton);

     return actionsDiv;
}

// Функция для открытия модального окна
function openModalDetails(massLoadId, massLoadDate) {

    if (isNaN(massLoadId)) {
      console.error("Не удалось извлечь номер загрузки");
      return;
    }

    show_details('flex');  // Открываем модальное окно
    $('#modal_mass_load_id').text(massLoadId + ' от ' + massLoadDate);
    $('#random_load_table').bootstrapTable('load', []);
    $('#random_load_table').bootstrapTable('refreshOptions', {'height': 'undefined'});
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
        $('#random_load_table').bootstrapTable('load', data.operation);
        $('#random_load_table').bootstrapTable('refreshOptions', {'height': $(".modal-body").height()});
        $('#random_load_table').bootstrapTable('hideLoading');
    }
}

// --- Модальное окно редактирования пользователя (Bootstrap 5) ---
function getDetailsModalInstance() {
    const el = document.getElementById('modal_window_details');
    return el ? bootstrap.Modal.getOrCreateInstance(el) : null;
}

function show_details(state) {
    const modal = getDetailsModalInstance();
    if (!modal) return;
    if (state === 'none') {
        modal.hide();
    } else {
        modal.show();
    }
}

window.show_details = show_details;