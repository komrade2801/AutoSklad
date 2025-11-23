// export function generatePrintTable(jsonObjectHistory) {
//     const operations = jsonObjectHistory.operation;
//     if (!operations) return;

//     // Преобразуем операции в массив с удобными полями
//     const operationList = Object.values(operations).map(op => ({
//         cell: op.cells,
//         tool: op.tools,
//         plan: op.plans
//     }));

//     // Сортируем по cellId по возрастанию (преобразуем cell к числу для сортировки)
//     operationList.sort((a, b) => Number(a.cell) - Number(b.cell));

//     // Генерируем HTML-таблицу
//     let tableHTML = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse; width: 100%;">';
//     tableHTML += `
//         <thead>
//             <tr>
//                 <th>Cell ID</th>
//                 <th>Tool</th>
//                 <th>Plan</th>
//             </tr>
//         </thead>
//         <tbody>
//     `;

//     for (const op of operationList) {
//         tableHTML += `
//             <tr>
//                 <td>${op.cell}</td>
//                 <td>${op.tool}</td>
//                 <td>${op.plan}</td>
//             </tr>
//         `;
//     }

//     tableHTML += '</tbody></table>';

//     // Вставляем таблицу в контейнер
//     const printArea = document.getElementById('printArea');
//     printArea.innerHTML = tableHTML;
// }
export function generatePrintTable(jsonObjectHistory) {
    console.log("generatePrintTable")
    console.log(jsonObjectHistory)
    const operations = jsonObjectHistory.operation;
    if (!operations) return;
  
    // 1. «Раскручиваем» операции в плоский массив строк
    const rows = [];
  
    //Object.values( ).forEach();
    for (const operationKey in operations) {
        const op = operations[operationKey];
        console.log(op)
        const status = op.status.trim().toLowerCase();
        if (status === "на загрузке" || status === "mass_load_init" || status === "объявлена массовая загрузка") {
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
  