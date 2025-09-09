export function generatePrintTable(jsonObjectHistory) {
    const operations = jsonObjectHistory.operation;
    if (!operations) return;

    // Преобразуем операции в массив с удобными полями
    const operationList = Object.values(operations).map(op => ({
        cell: op.cell,
        tool: op.tool,
        plan: op.plan
    }));

    // Сортируем по cellId по возрастанию (преобразуем cell к числу для сортировки)
    operationList.sort((a, b) => Number(a.cell) - Number(b.cell));

    // Генерируем HTML-таблицу
    let tableHTML = '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse; width: 100%;">';
    tableHTML += `
        <thead>
            <tr>
                <th>Cell ID</th>
                <th>Tool</th>
                <th>Plan</th>
            </tr>
        </thead>
        <tbody>
    `;

    for (const op of operationList) {
        tableHTML += `
            <tr>
                <td>${op.cell}</td>
                <td>${op.tool}</td>
                <td>${op.plan}</td>
            </tr>
        `;
    }

    tableHTML += '</tbody></table>';

    // Вставляем таблицу в контейнер
    const printArea = document.getElementById('printArea');
    printArea.innerHTML = tableHTML;
}
