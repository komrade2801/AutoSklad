var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf() {
    show_conf('flex');  // Открываем модальное окно
}

window.show_conf = show_conf;
window.openModalConf = openModalConf;

export function createTableActualNorms(containerId, jsonActualNorms) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error("Контейнер не найден");
        return;
    }

    // Создание таблицы и заголовка
    const table = document.createElement("table");
    table.border = "1";
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const headers = ["Пользователь", "Номенклатура", "Количество", "Количество периодов", "Тип периода", "Количество на руках не более", "Дата начала действия", "Действие"];

    headers.forEach(text => {
        const th = document.createElement("th");
        th.textContent = text;
        th.style.border = "1px solid black";
        th.style.padding = "5px";
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Создание тела таблицы
    const tbody = document.createElement("tbody");

    Object.values(jsonActualNorms.user).forEach(user => {
        Object.values(user.tools).forEach(tool => {
            const row = document.createElement("tr");

            const cells = [
                user.username,
                tool.tool_name,
                tool.sum,
                tool.sum_of_periods,
                tool.type_periods,
                tool.sum_of_use === "None" ? "" : tool.sum_of_use,
                tool.start_date
            ];

            cells.forEach((text, index) => {
                const td = document.createElement("td");
                td.textContent = text;
                td.style.border = "1px solid black";
                td.style.padding = "5px";
                if (index === 3) { // Количество периодов - выравнивание по правой стороне
                    td.style.textAlign = "right";
                }
                row.appendChild(td);
            });

            // Добавление кнопки "Удалить"
            const actionTd = document.createElement("td");
            actionTd.style.border = "1px solid black";
            actionTd.style.padding = "5px";
            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Удалить";
            deleteButton.addEventListener('click', function() {
                openModalConf();
            });
            actionTd.appendChild(deleteButton);
            row.appendChild(actionTd);

            tbody.appendChild(row);
        });
    });

    table.appendChild(tbody);
    container.innerHTML = "";
    container.appendChild(table);
}
