import { createTableAllDevice } from './createTableAllDevice.js'

function deleteDevice(serialNumber) {
  const deviceDeleteNumber = serialNumber;

  if (deviceDeleteNumber == null) {
    console.error("Серийный номер не задан");
    return;
  }

//  const devicePos = window.jsonAllDevice.findIndex(user => user.index === userIndex);
//
//  if (devicePos === -1) {
//    console.error("Устройство не найдено");
//    return;
//  }

  // Отправляем запрос на удаление
  fetch(`/backend/delete_device/{deviceDeleteNumber}`, {
    method: 'DELETE',
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Ошибка удаления устройства: ${response.statusText}`);
    }

    // Удаляем из локального массива и обновляем таблицу
    //window.jsonAllDevice.splice(userPos, 1);
    createTableAllDevice('column-1', window.jsonAllDevice);
    show_conf('none');
    serialNumber = null;
  })
  .catch(error => {
    console.error("Ошибка при удалении устройства:", error);
  });
}

window.deleteDevice = deleteDevice;
