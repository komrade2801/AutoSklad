export function createHistoryWriteOff(containerId, jsonHistoryWriteOff) {
    console.log("Функция createHistoryWriteOff успешно вызвана.")
    console.log(jsonHistoryWriteOff)
    const container = document.getElementById(containerId);

    // Создаем таблицу
    const table = document.createElement("table");
    table.border = "1";
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";

    // Заголовок таблицы
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const headers = ["Дата", "Группа инструмента", "Название инструмента", "ID инструмента", "Количество", "Откуда списано", "Имя пользователя", "Причина списания"];

    headers.forEach(headerText => {
        const th = document.createElement("th");
        th.textContent = headerText;
        th.style.border = "1px solid black";
        th.style.padding = "5px";
        th.style.textAlign = "left";
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Тело таблицы
    const tbody = document.createElement("tbody");
    Object.values(jsonHistoryWriteOff.operation).forEach(operation => {
        const row = document.createElement("tr");

        const values = [
            operation.time || "-",
            operation.group || "-",
            operation.toolName || "-",
            operation.ID_tool || "-",
            operation.sum || "-",
            operation.toolPosition || "-",
            operation.username || "-",
            operation.reason || "-"
        ];

        values.forEach(value => {
            const td = document.createElement("td");
            td.textContent = value;
            td.style.border = "1px solid black";
            td.style.padding = "5px";
            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    // Очищаем контейнер перед добавлением новой таблицы
    container.innerHTML = "";
    container.appendChild(table);
}
