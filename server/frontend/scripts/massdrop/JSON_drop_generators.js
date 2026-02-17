export function generateJsonToolsDrop(jsonCellsDrop) {
    console.log('[massdrop] Входной массив ячеек:', JSON.stringify(jsonCellsDrop, null, 2));

    const allTools = [];

    const sortedRowKeys = Object.keys(jsonCellsDrop.rows).map(Number).sort((a, b) => a - b);

    for (const rowKey of sortedRowKeys) {
        const row = jsonCellsDrop.rows[rowKey];

        const sortedCellKeys = Object.keys(row.cells).map(Number).sort((a, b) => a - b);

        for (const cellKey of sortedCellKeys) {
            const cell = row.cells[cellKey];

            // исключаются инструменты без названия, добавленные в чертеж,
            // и ячейки без статуса mass_load_ready (3) или load_ready (7)
            const allowedStatuses = [3, 7];
            if (cell.content.tool === "None" || cell.content.plan !== '' || !allowedStatuses.includes(cell.content.status_id)) {
                continue;
            }

            allTools.push({
                tool: cell.content.tool,
                group: cell.content.group,
                plan: cell.content.plan,
                cell: Number(cell.id),
                number: Number(cell.number)
            });
        }
    }

    console.log('[massdrop] Отфильтрованный список инструментов:', JSON.stringify(allTools, null, 2));
    return allTools;
}