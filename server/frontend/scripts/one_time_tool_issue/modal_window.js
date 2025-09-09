var showModalBarcode = function (state) {
    document.getElementById('modal_window_barcode').style.display = state
    document.getElementById('membrane').style.display = state
}

var showModalToolIssuing = function (state) {
    document.getElementById('modal_window_issuing').style.display = state
    document.getElementById('membrane').style.display = state
}

var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}


    // Переменная для хранения выбранного действия
    let selectedAction = "Выдать со склада"; // Значение по умолчанию

document.addEventListener("DOMContentLoaded", function () {
    // Получаем элементы по их ID
    const selectButton = document.getElementById("select_position");
    const dropdownStock = document.getElementById("dropdown_stock");
    const dropdownBarcode = document.getElementById("dropdown_barcode");

    // Назначаем обработчики кликов на пункты выпадающего меню
    dropdownStock.addEventListener("click", function (event) {
        event.preventDefault();
        selectedAction = "Выдать со склада";
        selectButton.textContent = selectedAction;
    });

    dropdownBarcode.addEventListener("click", function (event) {
        event.preventDefault();
        selectedAction = "Сгенерировать штрих-код";
        selectButton.textContent = selectedAction;
    });
});

    // Функция, вызываемая при нажатии на "Подтвердить"
window.openModal = function () {
    if (selectedAction === "Сгенерировать штрих-код") {
        showModalBarcode('flex');  // Открываем модальное окно
    } else {
        showModalToolIssuing('flex');
    }
};

// Функция, вызываемая при нажатии на "Отмена"
function openModalConf() {
    show_conf('flex');  // Открываем модальное окно
}




// Делаем функцию доступной глобально
window.openModal = openModal;
window.showModalBarcode = showModalBarcode;
window.showModalToolIssuing = showModalToolIssuing;
window.openModalConf = openModalConf;
window.show_conf = show_conf;
