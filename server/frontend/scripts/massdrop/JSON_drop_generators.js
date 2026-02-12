export function generateJsonToolsDrop(jsonCellsDrop) {
    const allTools = [];

    const sortedRowKeys = Object.keys(jsonCellsDrop.rows).map(Number).sort((a, b) => a - b);

    for (const rowKey of sortedRowKeys) {
        const row = jsonCellsDrop.rows[rowKey];

        const sortedCellKeys = Object.keys(row.cells).map(Number).sort((a, b) => a - b);

        for (const cellKey of sortedCellKeys) {
            const cell = row.cells[cellKey];

            // исключаются инструменты без названия и добавленные в чертеж
            if (cell.content.tool === "None" || cell.content.plan !== '') {
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
    return allTools;
}