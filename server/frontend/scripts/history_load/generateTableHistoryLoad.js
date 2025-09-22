import { openModal } from './modal_window_14.js'
import { generatePrintTable } from './generate_print_table.js'


function printElement(elem) {
    const width = 900;
    const height = 700;

    const left = (window.screen.width / 2) - (width / 2);
    const top = (window.screen.height / 2) - (height / 2);

    const printWindow = window.open('', '_blank', 'width=${width},height=${height},top=${top},left=${left}');

    printWindow.document.write(`
        <html>
            <head>
                <title>Просмотр перед печатью</title>
                <link rel="stylesheet" href="../../style/button_style.css">
                <link rel="stylesheet" href="../../assets/print/print.min.css">
                <script src="../../assets/print/print.min.js"></script>
                <style>
                    @media print {
                        .print-buttons {
                            display: none;
                        }
                        body {
                            margin: 0;
                        }
                    }

                    body {
                        font-family: Arial, sans-serif;
                        background: #ccc;
                        margin: 20px;
                    }

                    .logo {
                        display: flex;
                        align-items: center;
                    }

                    .a4 {
                        width: 210mm;
                        min-height: 297mm;
                        margin: auto;
                        padding: 20mm;
                        padding-top: 10mm;
                        background: white;
                        box-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
                        box-sizing: border-box;
                    }

                    .print-buttons {
                        margin-bottom: 20px;
                        display: flex;
                        flex-direction: row;
                        width: 210mm;
                        margin: auto;
                        justify-content: flex-end;
                        margin-top: 5px;
                    }

                    .print-buttons button {
                        margin-right: 10px;
                        padding: 10px 20px;
                        font-size: 16px;
                        cursor: pointer;
                    }

                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 10px;
                    }

                    th, td {
                        border: 1px solid #000;
                        padding: 8px;
                        text-align: left;
                        font-size: 12pt;
                    }

                    th {
                        background-color: #f0f0f0;
                    }
                </style>
            </head>
            <body>
                <div id="a4" class="a4">
                    <div class="logo">
                      <img class="d-flex" src="../assets/img/logo.png" style="height: 100px;margin-right: 10px;margin-left: 10px;">
                      <span style="color: rgb(78,155,229);font-size: 22px;font-weight: bold;margin-right: 10px;">Завод Контакт</span>
                    </div>
                    ${elem.innerHTML}
                </div>
                <div class="print-buttons">
                    <button class="btn_vending" onclick="window.close()">Отмена</button>
                    <button class="btn_vending" onclick="printJS('a4', 'html')" style="margin-right: 0px;">Печать</button>
                </div>
            </body>
        </html>
    `);

    printWindow.document.close(); // Завершаем запись
    printWindow.focus(); // Фокусируем новое окно
}




export function generateTableHistoryLoad(jsonHistoryLoad, containerId) {
    const container = document.getElementById(containerId);

    const table = document.createElement("table");
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";

    // Заголовки
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const headers = ["Дата", "Идентификатор операции", "Пользователь", "Статус"];

    headers.forEach(headerText => {
        const th = document.createElement("th");
        th.textContent = headerText;
        th.style.border = '1px solid';
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Преобразуем объект в массив
    const operationsArray = Object.values(jsonHistoryLoad.operation);

    function parseDate(dateStr) {
        const [day, month, year] = dateStr.split(".");
        return new Date(year, month - 1, day);
    }

    // Найдём самую свежую дату
    const latestDate = operationsArray
        .map(op => parseDate(op.date.trim()))
        .reduce((max, curr) => (curr > max ? curr : max), new Date(0));

    function isSameDate(date1, date2) {
        return (
            date1.getFullYear() === date2.getFullYear() &&
            date1.getMonth() === date2.getMonth() &&
            date1.getDate() === date2.getDate()
        );
    }

    const tbody = document.createElement("tbody");

    operationsArray.forEach(item => {
        const row = document.createElement("tr");

        const itemDate = parseDate(item.date.trim());
        const isLatest = isSameDate(itemDate, latestDate);
        const status = item.status.trim().toLowerCase();
        const idLoad = item.ID_load.trim();

        row.style.cursor = "pointer";

        let destinationUrl = `/screen_14_2_random_load.html?ID_load=${encodeURIComponent(idLoad)}`;

        const printerCell = document.createElement("td");

        if (isLatest && status === "на загрузке" || isLatest && status === "mass_load_init") {
            // Кнопка с иконкой принтера
            const printButton = document.createElement("button");
            printButton.style.width = "35px";
            printButton.style.height = "35px";
            printButton.style.backgroundImage = "url('../assets/img/printer.png')"; // Путь к иконке
            printButton.style.backgroundSize = "contain";
            printButton.style.backgroundRepeat = "no-repeat";
            printButton.style.backgroundColor = "transparent";
            printButton.style.border = "none";
            printButton.title = "Печать";

            printButton.addEventListener("click", (e) => {
                e.stopPropagation();

                // Генерируем таблицу
                generatePrintTable(jsonHistoryLoad);

                // Печатаем только содержимое printArea
                let print_area = document.getElementById('printArea')
                console.log(print_area);
                printElement(print_area);
            });


            printerCell.appendChild(printButton);
            //destinationUrl = `/screen_14_1_last_load.html?ID_load=${encodeURIComponent(idLoad)}`;
        }

        row.innerHTML = `
            <td>${item.date.trim()}</td>
            <td>${item.ID_load.trim()}</td>
            <td>${item.user.trim()}</td>
            <td>${item.status.trim()}</td>
        `;

        for (let td of row.querySelectorAll('td')) {
            td.style.border = '1px solid';
        }

        printerCell.style.border = '1px solid';
        row.appendChild(printerCell);

        row.addEventListener("click", () => {
            let token = localStorage.getItem('token');
            let full_url = destinationUrl + "&token=" + token;
            window.location.href = full_url;
        });

        tbody.appendChild(row);
    });

    if (operationsArray.length === 0) {
        const emptyRow = document.createElement("tr");
        const emptyTd = document.createElement("td");
        emptyTd.colSpan = 5;  // Для столбцов: Дата, Идентификатор операции, Пользователь, Статус, ""
        emptyTd.textContent = "История загрузок пуста";
        emptyTd.style.textAlign = "center";
        emptyTd.style.fontStyle = "italic";
        emptyTd.style.border = '1px solid';
        emptyRow.appendChild(emptyTd);
        tbody.appendChild(emptyRow);
    }

    table.appendChild(tbody);

    container.innerHTML = "";
    container.appendChild(table);
}
