export function generateJsonAllTool(groupsCount) {
    const jsonObjectAllTools = { groups: {} };

    for (let groupIndex = 0; groupIndex < groupsCount; groupIndex++) {
        jsonObjectAllTools.groups[groupIndex] = {
            name: `Группа ${groupIndex + 1}`,
            value: {}
        };

        const valuesPerGroupCount = Math.floor(Math.random() * 20) + 1; // От 1 до 20 инструментов в группе
        for (let valueIndex = 0; valueIndex < valuesPerGroupCount; valueIndex++) {
            jsonObjectAllTools.groups[groupIndex].value[valueIndex] = {
                tools: `Инструмент ${valueIndex + 1}`,
                stock: Math.floor(Math.random() * 21),  // Количество на складе
                machine: Math.floor(Math.random() * 21), // Количество в аппарате
                in_use: Math.floor(Math.random() * 21) // Количество на руках
            };
        }
    }
console.log(jsonObjectAllTools);
    return jsonObjectAllTools;
}

