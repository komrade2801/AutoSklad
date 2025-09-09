export function generateTableAllTools(containerId, jsonObjectAllTools) {
    const container = document.getElementById(containerId);

    const table = document.createElement("table");
    table.width = "100%";
    table.border = "1";

    // Создание заголовков таблицы
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const headers = ["Название инструмента", "Группа инструмента", "На складе", "В аппарате", "На руках"];

    headers.forEach(text => {
        const th = document.createElement("th");
        th.textContent = text;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Создание строк с данными
    const tbody = document.createElement("tbody");

    Object.values(jsonObjectAllTools.groups).forEach(group => {
        Object.values(group.value).forEach(tool => {
            const row = document.createElement("tr");

            const toolName = document.createElement("td");
            toolName.textContent = tool.tools;
            row.appendChild(toolName);

            const groupName = document.createElement("td");
            groupName.textContent = group.name;
            row.appendChild(groupName);

            const stock = document.createElement("td");
            stock.textContent = tool.stock;
            row.appendChild(stock);

            const machine = document.createElement("td");
            machine.textContent = tool.machine;
            row.appendChild(machine);

            const inUse = document.createElement("td");
            inUse.textContent = tool.in_use;
            row.appendChild(inUse);

            tbody.appendChild(row);
        });
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

// Пример вызова с JSON-данными
// fetch('tools.json')
//     .then(response => response.json())
//     .then(data => generateTableFromJson(data));
