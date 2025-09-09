export function generateTableHistoryError(jsonHistoryError, containerId) {

    const container = document.getElementById(containerId);

    const table = document.createElement("table");
    table.border = "1";
    table.style.width = "100%";

    // Заголовки
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const headers = ["Дата", "Ошибка", "Пользователь", "Устройство"];

    headers.forEach(headerText => {
        const th = document.createElement("th");
        th.textContent = headerText;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Преобразуем объект в массив
    const operationsArray = Object.values(jsonHistoryError.error);

    // Найдём самую свежую дату
    const latestDate = operationsArray
        .map(op => new Date(op.date.trim()))
        .reduce((max, curr) => (curr > max ? curr : max), new Date(0));

    // Тело таблицы
    const tbody = document.createElement("tbody");

    operationsArray.forEach(item => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${item.date.trim()}</td>
            <td>${item.name_error.trim()}</td>
            <td>${item.user.trim()}</td>
            <td>${item.device.trim()}</td>
        `;

        row.style.cursor = "pointer";

        row.addEventListener("click", () => openModal(item));

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    // Очищаем контейнер перед добавлением новой таблицы
    container.innerHTML = "";
    container.appendChild(table);
}