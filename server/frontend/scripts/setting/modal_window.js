var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf() {
    show_conf('flex');  // Открываем модальное окно
}

window.openModalConf = openModalConf;
window.show_conf = show_conf;



var show_factory_reset = function (state) {
    document.getElementById('modal_window_factory_reset').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalFactoryReset() {
    show_factory_reset('flex');  // Открываем модальное окно
}

window.openModalFactoryReset = openModalFactoryReset;
window.show_factory_reset = show_factory_reset;



var show_modal_finish = function (state) {
    document.getElementById('modal_window_finish').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalFinish() {
    show_modal_finish('flex');  // Открываем модальное окно
}

window.openModalFinish = openModalFinish;
window.show_modal_finish = show_modal_finish;