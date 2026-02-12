import { generateTools } from './generateTools.js'


// Функция для генерации JSON-History с историей текущей загрузки
export function updateJsonHistoryLoad() {


    console.log(window.appData.history.operation);

    window.appData.history.list = [];
    window.appData.history.table = [];

    for (const [key, operation] of Object.entries(window.appData.history.operation)) {
        console.log(key);
        console.log(operation);

        window.appData.history.table.push({
            id: operation.id,
            name: operation.name,
            quantity: operation.quantity
        });

        window.appData.history.list.push({
            id: String(operation.id)
        });
    }

    createHistory();
}

// Функция для создания строк истории на основе JSON-данных
export function createHistory() {
    console.log("history:")
    console.log(window.appData.history.table);

    if (window.appData.history.table != undefined) {
//        $('#droppable_story_table').bootstrapTable('refreshOptions', {'height': $("#droppable_story_div").height()});
        $('#selected_tools_table').bootstrapTable('load', window.appData.history.table);
        $('#selected_tools_table').bootstrapTable('hideLoading');
    }
}