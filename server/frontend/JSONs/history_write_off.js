//для генерации таблицы "История списаний".
//где toolPosition, там только один из вариантов, он или с рук, или со склада.

export const jsonHistoryWriteOff = {
    "operation":
    {
        "0": {
            "ID_tool": "892 027 999",
            "group": "Молотки",
            "toolName": "молоток зелёный 35см",
            "toolPosition": "stock", // или "in_use"
            "username": "-", // или username пользователя
            "sum": "None",
            "reason": "None",
            "time": "None"
        },
        "1": {
            "ID_tool": "892 027 999",
            "group": "Молотки",
            "toolName": "молоток зелёный 35см",
            "toolPosition": "stock", // или "in_use"
            "username": "-", // или username пользователя
            "sum": "None",
            "reason": "None",
            "time": "None"
        },
        "2": {
            "ID_tool": "892 027 999",
            "group": "Молотки",
            "toolName": "молоток зелёный 35см",
            "toolPosition": "in_use",
            "username": "Baba_Manya",
            "sum": "None",
            "reason": "None",
            "time": "None"
        }
    }
};