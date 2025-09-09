// Функция для генерации JSON-файла с инструментами
export function generateJsonTool(plansCount, groupsPerPlanCount, valuesPerGroupCount) {
//plansCount (количество чертежей), groupsPerPlanCount (количество групп в одном чертеже), valuesPerGroupCount (количество инструментов в 1 группе)
    const jsonObject = { plans: {} };

    for (let planIndex = 0; planIndex < plansCount; planIndex++) {
        jsonObject.plans[planIndex] = {
            name: planIndex === 0 ? "None" : `хххх.DDDDDD.DD СБ${planIndex + 1}`,
            groups: {}
        };

        for (let groupIndex = 0; groupIndex < groupsPerPlanCount; groupIndex++) {
            jsonObject.plans[planIndex].groups[groupIndex] = {
                name: `Группа ${groupIndex + 1}`,
                value: {}
            };

            for (let valueIndex = 0; valueIndex < valuesPerGroupCount; valueIndex++) {
                jsonObject.plans[planIndex].groups[groupIndex].value[valueIndex] = {
                    tools: `Инструмент ${valueIndex + 1}`,
                    sum: Math.floor(Math.random() * 20) + 1
                };
            }
        }
    }

    return jsonObject;
}

// Пример вызова функции
//const jsonResult = generateJsonTool(2, 2, 3);
//console.log(JSON.stringify(jsonResult, null, 2));




// Функция для генерации JSON-файла с ячейками аппарата
export function generateJsonCells(rowsCount, cellsCount) {
    const jsonObject = { rows: {} };

    for (let row = 1; row <= rowsCount; row++) {
        jsonObject.rows[row] = { cells: {} };

        for (let cell = 1; cell <= cellsCount; cell++) {
            jsonObject.rows[row].cells[cell] = {
                id: (row - 1) * cellsCount + cell, // Уникальный номер в зависимости от строки и ячейки
                type: "big", // Или "small", в зависимости от требований
                backgroundColor: '#69696910', // Общий цвет
                content: {
                    tool: "None",
                    plan: "None"
                },
                block: false
            };
        }
    }

    console.log(jsonObject)
    return jsonObject; //JSON.stringify(, null, 2) Форматированное представление
}


//цвета для ячеек:
//backgroundColor: '#69696910', для пустых
//'#535353' для занятых
//'#ff4f00' по чертежу
//'#2C8822' free_tools





