
  export function createTableDB(containerId, jsonTablesDB) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Контейнер с ID "${containerId}" не найден.`);
      return;
    }

    const table = document.createElement('table');
    table.width = '70%';

    // Заголовки
    const headers = ['Таблицы Базы Данных', 'Импорт', 'Экспорт'];
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
    (jsonTablesDB || []).forEach((tableDB) => {
      const row = document.createElement('tr');

      //Наименоварие таблицы из БД
      const nameTableDB = document.createElement('td');
      nameTableDB.textContent = jsonTablesDB.nameTableDB;
      row.appendChild(nameTableDB);

      //Кнопка Импортировать
      const tdImport = document.createElement('td');
      const buttonImport = document.createElement('button');
      buttonImport.textContent = 'Импортировать';
      buttonImport.className = 'btn_vending';
      buttonImport.onclick = () => importTable(tableDB);
      tdImport.appendChild(buttonImport);
      row.appendChild(tdImport);

      // Кнопка Экспортировать
      const tdExport = document.createElement('td');
      const buttonExport = document.createElement('button');
      buttonExport.textContent = 'Экспортировать';
      buttonExport.className = 'btn_vending';
      buttonExport.onclick = () => exportTable(tableDB);
      tdExport.appendChild(buttonExport);
      row.appendChild(tdExport);

      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.innerHTML = '';
    container.appendChild(table);
  }

