export function generateToolsSelection(jsonObjectTools) {
    const container = document.getElementById("selection_tools");
    container.innerHTML = ""; // Очищаем контейнер перед генерацией

    if (!jsonObjectTools.groups) {
        console.error("Некорректный формат данных");
        return;
    }

    Object.values(jsonObjectTools.groups).forEach(group => {
        // Создаем заголовок группы
        const groupTitle = document.createElement("h3");
        groupTitle.textContent = group.name;
        container.appendChild(groupTitle);

        // Создаем таблицу
        const table = document.createElement("table");
        table.border = "1";
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        const thTool = document.createElement("th");
        thTool.textContent = "Название инструмента";
        const thQuantity = document.createElement("th");
        thQuantity.textContent = "Количество";

        headerRow.appendChild(thTool);
        headerRow.appendChild(thQuantity);
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        Object.values(group.value).forEach(tool => {
            const row = document.createElement("tr");

            // Ячейка с названием инструмента
            const tdTool = document.createElement("td");
            tdTool.textContent = tool.tools;
            row.appendChild(tdTool);

            // Ячейка с полем ввода количества
            const tdQuantity = document.createElement("td");
            const select = document.createElement("select");

            // Опция "0" (по умолчанию)
            const optionZero = document.createElement("option");
            optionZero.value = "0";
            optionZero.textContent = "0";
            select.appendChild(optionZero);

            // Опции с количеством от 1 до stock
            for (let i = 1; i <= tool.stock; i++) {
                const option = document.createElement("option");
                option.value = i;
                option.textContent = i;
                select.appendChild(option);
            }

            // Опция "указать позже"
            const optionLater = document.createElement("option");
            optionLater.value = "later";
            optionLater.textContent = "Указать позже";
            select.appendChild(optionLater);

            tdQuantity.appendChild(select);
            row.appendChild(tdQuantity);

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        container.appendChild(table);
    });
}