import { jsonDevices } from '../../JSONs/jsonDevices.js'
import { createDevices } from './createDevices.js'



        //Управление модальным окном подтверждения отмены
var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf() {
    show_conf('flex');
}

window.openModalConf = openModalConf;
window.show_conf = show_conf;



        //Управление модальным окном прогресс бара
var show_progress_bar = function (state) {
    document.getElementById('modal_progress_bar').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalProgressBar() {
    show_progress_bar('flex');
}

window.openModalProgressBar = openModalProgressBar;



        //Управление окном id="add_data_device"
var show_data_device = function (state) {
    document.getElementById('modal_data_device').style.display = state
    document.getElementById('membrane').style.display = state
}

function openDataDevice() {
    show_data_device('flex');
}

window.openDataDevice = openDataDevice;


        //Управление модальным окном с сигнатурами
function show_signature(state) {
  document.getElementById('modal_window_signature').style.display = state;
  document.getElementById('membrane').style.display = state;
}

function openModalSignature(device, number) {
  // Заголовки
  document.getElementById('device_number').textContent = `Аппарат №${number}`;

  // Детали
  const detailContainer = document.getElementById('device_details');
  detailContainer.innerHTML = ''; // Очищаем перед заполнением

  let details;
  try {
    details = typeof device.details === 'string' ? JSON.parse(device.details) : device.details;
  } catch (e) {
    detailContainer.innerHTML = '<span style="color: red;">Ошибка при разборе данных деталей.</span>';
    show_detail('flex');
    return;
  }

  // Сигнатура
  if (details.signature) {
    detailContainer.innerHTML += `
      <div style="display: flex; flex-direction: column; width: 80%; margin-top: 15px;">
        <span><strong>Сигнатура:</strong></span>
        <span style="margin-left: 15px;">Серийный номер: ${details.signature.serial_number}</span>
        <span style="margin-left: 15px;">Ячеек: ${details.signature.cells.length} (${details.signature.cells.columns} колонки × ${details.signature.cells.rows} строки)</span>
      </div>
    `;
  }

  // Сеть
  if (details.network) {
    detailContainer.innerHTML += `
      <div style="display: flex; flex-direction: column; width: 80%; margin-top: 15px;">
        <span><strong>Сеть:</strong></span>
        <span style="margin-left: 15px;">IP: ${details.network.ip}</span>
        <span style="margin-left: 15px;">Порт: ${details.network.port}</span>
      </div>
    `;
  }

  // Последовательный порт
  if (details.serial) {
    detailContainer.innerHTML += `
      <div style="display: flex; flex-direction: column; width: 80%; margin-top: 15px;">
        <span><strong>Последовательный порт:</strong></span>
        <span style="margin-left: 15px;">Порт: ${details.serial.port}</span>
        <span style="margin-left: 15px;">Скорость: ${details.serial.baudrate}</span>
      </div>
    `;
  }

  // Штрихкод
  if (details.barcode) {
    detailContainer.innerHTML += `
      <div style="display: flex; flex-direction: column; width: 80%; margin-top: 15px;">
        <span><strong>Сканер штрихкодов:</strong></span>
        <span style="margin-left: 15px;">Порт: ${details.barcode.port}</span>
        <span style="margin-left: 15px;">Скорость: ${details.barcode.baudrate}</span>
      </div>
    `;
  }

  // Замки
  if (details.locks) {
    detailContainer.innerHTML += `
      <div style="display: flex; flex-direction: column; width: 80%; margin-top: 15px;">
        <span><strong>Замки:</strong></span>
        <span style="margin-left: 15px;">Загрузка заблокирована: ${details.locks.load_locked ? 'да' : 'нет'}</span>
        <span style="margin-left: 15px;">Выгрузка заблокирована: ${details.locks.drop_locked ? 'да' : 'нет'}</span>
      </div>
    `;
  }

  // Логи
  if (details.logs) {
    const errors = details.logs.critical_errors || [];
    detailContainer.innerHTML += `
      <div style="display: flex; flex-direction: column; width: 80%; margin-top: 15px;">
        <span><strong>Критические ошибки:</strong></span>
        <span style="margin-left: 15px;">${errors.length > 0 ? errors.join('<br>') : 'Отсутствуют'}</span>
      </div>
    `;
  }

  show_signature('flex');
}

window.openModalSignature = openModalSignature;
window.show_signature = show_signature;



        //Управление переносом модального окна с сигнатурами и появлением дива id="add_data_device"
function onAddDeviceClick() {
  // Скрываем модалку
  show_signature('none');

  // Показываем форму добавления
  document.getElementById('add_data_device').style.display = 'flex';

    // Показываем кнопку "Назад"
  document.getElementById('btn_back').style.display = 'flex';

      // Скрываем заголовок "Доступные устройства
  document.getElementById('title_available_devices').style.display = 'none';

  // Переносим содержимое из модалки в #devices
  const modalContent = document.getElementById('device_details').innerHTML;

  const devicesContainer = document.getElementById('devices');
  devicesContainer.innerHTML = modalContent;
}

window.onAddDeviceClick = onAddDeviceClick;



        //Управление кнопкой id="back"
function backClick() {
  // Скрываем модалку
  //show_signature('none');

  // Скрываем форму добавления
  document.getElementById('add_data_device').style.display = 'none';

    // Скрываем кнопку "Назад"
  document.getElementById('btn_back').style.display = 'none';

      // Возвращаем заголовок "Доступные устройства
  document.getElementById('title_available_devices').style.display = 'flex';

  // Переносим содержимое из модалки в #devices
  createDevices('devices', jsonDevices);
}

window.backClick = backClick;



        //Управление модальным окном ручного ввода IP
var show_no_devices_found = function (state) {
    document.getElementById('modal_no_devices_found').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalNoDevicesFound() {
    show_no_devices_found('flex');
}

window.openModalNoDevicesFound = openModalNoDevicesFound;
window.show_no_devices_found = show_no_devices_found;



        //Функция, которая прячет модальное окно и запускает поиск устройства по IP
function readSignature() {
    // Скрываем модалку modal_no_devices_found
    show_no_devices_found('none');

    //открываем модальное окно ожидания
    openModalProgressBar();
}

window.readSignature = readSignature;


        //Управление модальным окном ошибки
var show_error = function (state) {
    document.getElementById('modal_window_error').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalError() {
    show_error('flex');
}

window.openModalError = openModalError;
window.show_error = show_error;