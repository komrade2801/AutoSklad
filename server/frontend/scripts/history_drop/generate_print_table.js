export function generatePrintTable(jsonObjectHistory) {
    console.log("generatePrintTable")
    console.log(jsonObjectHistory)
    const operations = jsonObjectHistory.operation;
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
