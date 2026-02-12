export function generatePrintTable() {
    console.log("generatePrintTable")
    console.log(window.appData.history_drops)
    const operations = window.appData.history_drops.operation;
    if (!operations) return;

    const rows = [];

    for (const operationKey in operations) {
        const op = operations[operationKey];
        console.log(op)
        const status = op.status.trim().toLowerCase();
        if (status === "на выгрузке" || status === "mass_drop_init" || status === "объявлена массовая выгрузка") {
            const { cells = [], tools = [], plans = [] } = op;
            const count = cells.length;

            for (let i = 0; i < count; i++) {
              rows.push({
                cell: cells[i],
                tool: tools[i] ?? '—',
                plan: plans[i] ?? '—',
              });
            }
        }
    }

    // 2. Сортируем по cell (числово)
    rows.sort((a, b) => Number(a.cell) - Number(b.cell));

    // 3. Собираем HTML
    let tableHTML = `
      <table border="1" cellpadding="5" cellspacing="0"
             style="border-collapse:collapse; width:100%;">
        <thead>
          <tr>
            <th>Номер ячейки</th>
            <th>Инструмент</th>
            <th>Чертёж</th>
          </tr>
        </thead>
        <tbody>
    `;

    rows.forEach(({ cell, tool, plan }) => {
      tableHTML += `
        <tr>
          <td>${cell}</td>
          <td>${tool}</td>
          <td>${plan}</td>
        </tr>
      `;
    });

    tableHTML += `
        </tbody>
      </table>
    `;

    // 4. Вставляем в printArea
    const printArea = document.getElementById('printArea');
    if (printArea) {
      printArea.innerHTML = tableHTML;
    }
}

export function printElement(elem) {
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
