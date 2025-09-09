function show_detail(state) {
  document.getElementById('modal_window_detail').style.display = state;
  document.getElementById('membrane').style.display = state;
}

function openModalDetail(device, number) {
  // Заголовки
  document.getElementById('device_number').textContent = `Аппарат №${number}`;
  document.getElementById('device_name').textContent = `Название: ${device.name || '-'}`;
  document.getElementById('device_description').textContent = `Описание: ${device.description || '-'}`;

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

  show_detail('flex');
}


window.openModalDetail = openModalDetail;
window.show_detail = show_detail;




  export function createTableAllDevice(containerId, jsonAllDevice) {
  console.log(jsonAllDevice)

    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Контейнер с ID "${containerId}" не найден.`);
      return;
    }

    const table = document.createElement('table');
    table.width = '100%';

    // Заголовки
    const headers = ['Номер', 'Название', 'Описание', 'Детали', 'Дата регистрации', 'Удалить'];
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headers.forEach(headerText => {
      const th = document.createElement('th');
      th.textContent = headerText;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Тело таблицы
    const tbody = document.createElement('tbody');
    (jsonAllDevice || []).forEach((device) => {
      const row = document.createElement('tr');

      // Парсим details
      let parsedDetails = {};
      let serialNumber = '—';
      try {
        parsedDetails = JSON.parse(device.details);
        serialNumber = parsedDetails?.signature?.serial_number ?? '—';
      } catch (e) {
        console.error('Ошибка при разборе details:', e);
      }

      const numberDevice = document.createElement('td');
      numberDevice.textContent = serialNumber;
      row.appendChild(numberDevice);

      const nameDevice = document.createElement('td');
      nameDevice.textContent = device.name || '';
      row.appendChild(nameDevice);

      const descDevice = document.createElement('td');
      descDevice.textContent = device.description || '';
      row.appendChild(descDevice);

      const detailsDevice = document.createElement('td');
      const button = document.createElement('button');
      button.textContent = 'Подробнее';
      button.className = 'btn_vending';
      button.onclick = () => openModalDetail(device, serialNumber);
      detailsDevice.appendChild(button);
      row.appendChild(detailsDevice);

      const dateDevice = document.createElement('td');
      dateDevice.textContent = device.registrationDate || '';
      row.appendChild(dateDevice);

      // Кнопка Удалить
      const tdDelete = document.createElement("td");
      const btnDelete = document.createElement("button");
      btnDelete.style.cssText = "width:35px;height:35px;border:none;background:none;cursor:pointer;";
      btnDelete.title = "Удалить";
      btnDelete.addEventListener("click", () => {
        openModalConf(device, serialNumber);
      });
      const imgDel = document.createElement("img");
      imgDel.src = "../assets/img/btn_cross_2.png";
      imgDel.alt = "delete";
      imgDel.width = 35; imgDel.height = 35;
      btnDelete.appendChild(imgDel);
      tdDelete.appendChild(btnDelete);
      row.appendChild(tdDelete);

      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.innerHTML = '';
    container.appendChild(table);
  }

