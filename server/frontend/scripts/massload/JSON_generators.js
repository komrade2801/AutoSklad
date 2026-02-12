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

    console.log(jsonObject);

    return jsonObject;
}


