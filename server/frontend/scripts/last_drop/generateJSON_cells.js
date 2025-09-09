export function generateJson() {
    const rows = {};
    const tools = [
        { tool: "молоток большой 30см", group: "молоток", plan: "хххх.DDDDDD.DD СБ" },
        { tool: "молоток средний 20см", group: "молоток", plan: "хххх.DDDDDD.DD СБ" },
        { tool: "молоток маленький 10см", group: "молоток", plan: "хххх.DDDDDD.DD СБ" },
        { tool: "сверло 0,2мм", group: "свёрла", plan: "хххх.DDDDDD.DD СБ2" },
        { tool: "сверло 0,5мм", group: "свёрла", plan: "хххх.DDDDDD.DD СБ2" },
        { tool: "сверло 0,7мм", group: "свёрла", plan: "хххх.DDDDDD.DD СБ2" }
    ];

    let filledCells = new Set();
    while (filledCells.size < 25) {
        filledCells.add(Math.floor(Math.random() * 1024) + 1);
    }

    let id = 1;
    for (let row = 1; row <= 32; row++) {
        rows[row] = { cells: {} };
        for (let col = 1; col <= 32; col++) {
            let cell = {
                id: id.toString(),
                type: "small",
                block: "false",
                backgroundColor: "#2C8822",
                content: { tool: "None", groupName: "None", plan: "None" }
            };
            let shouldFill = Math.random() < 0.6;

            if (shouldFill) {
                let toolData = tools[Math.floor(Math.random() * tools.length)];
                cell.content = { tool: toolData.tool, groupName: toolData.group, plan: toolData.plan };
                cell.backgroundColor = filledCells.has(id) ? "#ff4f00" : "#535353";
                cell.block = "true";
            }

            rows[row].cells[col] = cell;
            id++;
        }
    }

    return JSON.stringify({ rows }, null, 2);
}

//console.log(generateJson());
