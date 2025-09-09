var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf(device, serialNumber) {
  // Парсим details для получения номера
  //serialNumber = '—';
  //try {
  //  const parsedDetails = typeof device.details === 'string' ? JSON.parse(device.details) : device.details;
  //  serialNumber = parsedDetails?.signature?.serial_number ?? '—';
  //} catch (e) {
  //  console.error('Ошибка при разборе details в openModalConf:', e);
  //}

  // Устанавливаем текст в модальное окно
  document.getElementById('number_device').textContent = `Аппарат №${serialNumber}`;
  document.getElementById('name_device').textContent = `Название: ${device.name || '-'}`;

  show_conf('flex');  // Показываем модальное окно
}


window.openModalConf = openModalConf;
window.show_conf = show_conf;