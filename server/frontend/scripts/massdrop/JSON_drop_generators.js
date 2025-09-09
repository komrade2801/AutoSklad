// Функция для генерации JSON-файла с заполненными ячейками
export function generateJsonCellsDrop(rowsCount, cellsCount, jsonObjectTools) {

    // Генерация jsonCells с ячейками
    const jsonCellsDrop = { rows: {} };

    // Создаём массив доступных инструментов, где каждый инструмент представлен одной штукой
    const availableTools = [];
    Object.values(jsonObjectTools.plans).forEach(plan => {
        Object.values(plan.groups).forEach(group => {
            Object.values(group.value).forEach(tool => {
                for (let i = 0; i < tool.sum; i++) {
                    availableTools.push({
                        plan: plan.name,
                        tool: tool.tools
                    });
                }
            });
        });
    });

    for (let rowIndex = 1; rowIndex <= rowsCount; rowIndex++) {
        const row = {};

        for (let cellIndex = 1; cellIndex <= cellsCount; cellIndex++) {
            const cellId = `${(rowIndex - 1) * cellsCount + cellIndex}`;

            // Определяем tool и plan из доступных инструментов или задаём None
            let tool = "None";
            let plan = "None";

            if (availableTools.length > 0) {
                const selectedTool = availableTools.splice(Math.floor(Math.random() * availableTools.length), 1)[0];
                tool = selectedTool.tool;
                plan = selectedTool.plan;
            }

            // Устанавливаем цвет ячейки и блокировку
            let backgroundColor;
            let block;

            if (plan === "None" && tool !== "None") {
                backgroundColor = "#2C8822";
                block = true;
            } else if (plan === "None" && tool === "None") {
                backgroundColor = "#69696910";
                block = false;
            } else {
                backgroundColor = "#ff4f00";
                block = true;
            }

            row[cellIndex.toString()] = {
                id: cellId,
                type: "big",
                backgroundColor: backgroundColor,
                content: {
                    tool: tool,
                    plan: plan
                },
                block: block
            };
        }

        jsonCellsDrop.rows[rowIndex.toString()] = { cells: row };
    }

    return jsonCellsDrop;
}



//цвета для ячеек:
//backgroundColor: '#69696910', для пустых
//'#535353' для занятых
//'#ff4f00' по чертежу
//'#2C8822' свободный инструмент




export function generateJsonToolsDrop(jsonCellsDrop) {
    const allTools = [];

    const sortedRowKeys = Object.keys(jsonCellsDrop.rows).map(Number).sort((a, b) => a - b);

    for (const rowKey of sortedRowKeys) {
        const row = jsonCellsDrop.rows[rowKey];

        const sortedCellKeys = Object.keys(row.cells).map(Number).sort((a, b) => a - b);

        for (const cellKey of sortedCellKeys) {
            const cell = row.cells[cellKey];
            const { plan, groupName, tool } = cell.content;

            if (tool === "None") continue;

            allTools.push({
                plan,
                groupName,
                tool,
                cellId: Number(cell.id) // Сохраняем номер ячейки как число
            });
        }
    }

    // Теперь весь массив отсортируем по номеру ячейки
    allTools.sort((a, b) => a.cellId - b.cellId);

    // После сортировки можем собрать обратно структуру plans/groups
    const jsonToolsDrop = { plans: {} };

    for (const toolData of allTools) {
        const { plan, groupName, tool, cellId } = toolData;

        if (!jsonToolsDrop.plans[plan]) {
            jsonToolsDrop.plans[plan] = { name: plan, groups: {} };
        }

        const planEntry = jsonToolsDrop.plans[plan];

        if (!planEntry.groups[groupName]) {
            planEntry.groups[groupName] = { name: groupName, value: [] };
        }

        const groupEntry = planEntry.groups[groupName];

        groupEntry.value.push({
            tools: tool,
            cell: cellId
        });
    }

    return jsonToolsDrop;
}




// Преобразуем входные данные и выводим результат
//console.log(transformJsonCellsToJsonToolsDrop(jsonCells));
