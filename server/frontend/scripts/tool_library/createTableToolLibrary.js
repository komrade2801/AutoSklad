var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf() {
    show_conf('flex');  // Открываем модальное окно
}

window.openModalConf = openModalConf;
window.show_conf = show_conf;

export function createTableToolLibrary(containerId, jsonToolLibrary) {
    let container = document.getElementById(containerId);
    if (!container) {
        console.error("Container not found");
        return;
    }

    let table = document.createElement("table");
    table.style.width = "100%";
    table.border = "1";
    table.style.borderCollapse = "collapse";

    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");

    const headers = ["Группа инструмента", "Подгруппа", "Номенклатура", "В наличии", "", ""];
    headers.forEach((text, index) => {
        let th = document.createElement("th");
        th.textContent = text;
        if (index >= 4) {
            th.style.width = "37px";
        }
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");

    Object.values(jsonToolLibrary.groups).forEach(group => {
        Object.values(group.subgroup).forEach(subgroup => {
            Object.values(subgroup.value).forEach(item => {
                let row = document.createElement("tr");

                // Группа
                let groupCell = document.createElement("td");
                groupCell.textContent = group.name;
                row.appendChild(groupCell);

                // Подгруппа
                let subgroupCell = document.createElement("td");
                subgroupCell.textContent = subgroup.SGName;
                row.appendChild(subgroupCell);

                // Название инструмента
                let itemCell = document.createElement("td");
                itemCell.textContent = item.tools;
                row.appendChild(itemCell);

                // В наличии (sum)
                let stockCell = document.createElement("td");
                stockCell.textContent = item.sum;
                row.appendChild(stockCell);

                // Edit button
                let editCell = document.createElement("td");
                let editButton = document.createElement("button");
                editButton.style.width = "35px";
                editButton.style.height = "35px";
                editButton.innerHTML = "✏️";
                editButton.title = "Редактировать";
                editCell.appendChild(editButton);
                row.appendChild(editCell);

                // Delete button
                let deleteCell = document.createElement("td");
                let deleteButton = document.createElement("button");
                deleteButton.style.width = "35px";
                deleteButton.style.height = "35px";
                deleteButton.innerHTML = "❌";
                deleteButton.title = "Удалить";

                deleteButton.addEventListener('click', function () {
                    openModalConf();
                    console.log("Клик был");
                });

                deleteCell.appendChild(deleteButton);
                row.appendChild(deleteCell);

                tbody.appendChild(row);
            });
        });
    });

    table.appendChild(tbody);
    container.appendChild(table);
}


// Функция для получения JSON-данных через эндпоинт
export async function fetchToolLibraryData(device_number) {
    // 1
    const url = "../backend/get_groups_from_db/?device_number=" + device_number;
    console.log(url);
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: " + response.status);
        }
        const jsonData = await response.json();
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}


// Функция для загрузки данных и создания таблицы
export async function loadToolLibraryTable(containerId, device_number) {
    const jsonToolLibrary = await fetchToolLibraryData(device_number);
    if (jsonToolLibrary) {
        createTableToolLibrary(containerId, jsonToolLibrary);
    } else {
        console.error("Не удалось загрузить данные для таблицы.");
    }
}



// Пример вызова: запуск функции после загрузки DOM
//document.addEventListener("DOMContentLoaded", () => {
//    // Замените 'toolLiSbraryContainer' на id элемента, в котором нужно отобразить таблицу
//    loadToolLibraryTable("toolLibraryContainer");
//});


// Вызов функции
// createTableToolLibrary(jsonToolLibrary, 'yourContainerId');
