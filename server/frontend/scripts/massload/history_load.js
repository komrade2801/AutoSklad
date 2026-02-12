import { createTools } from './createTools.js'


// Функция для генерации JSON-History с историей текущей загрузки
export function updateJsonHistoryLoad() {


    console.log(window.appData.history.operation);

    window.appData.history.list = [];
    window.appData.history.table = [];

    for (const [key, operation] of Object.entries(window.appData.history.operation)) {
        console.log(key);
        console.log(operation);

        window.appData.history.table.push({
            tool: operation.tool,
            name: operation.name,
            sum: operation.sum
        });

        window.appData.history.list.push({
            tool: String(operation.tool)
        });
    }

    createHistory();
}


function handleLoadClick(toolName, toolSum) {

    // Ничего не делаем, если содержимое пустое
    if (toolName === 'None') return;

    // Убедимся, что window.appData.history.operation существует
    if (!window.appData.history.operation) {
        window.appData.history.operation = {}; // Инициализируем, если это null или undefined
    }

    // create new operation in history

    const newKey = Object.keys(window.appData.history.operation).length + 1;

    window.appData.history.operation[newKey] = {
        tool: toolName,
        sum: toolSum
    }

    updateJsonHistoryLoad();

    // delete from tool list

    const index = window.appData.tools.findIndex(item => item.cell === cellId);

    if (index != -1) {
        // Если вдруг инструмент найден, удаляем из списка

        window.appData.tools.splice(index, 1); // Removes 1 element at the found index
        createTools();
    }

    show('none');
}

window.handleLoadClick = handleLoadClick;



// Функция для создания строк истории на основе JSON-данных
export function createHistory() {
    console.log("history:")
    console.log(window.appData.history.table);

    if (window.appData.history.table != undefined) {
//        $('#droppable_story_table').bootstrapTable('refreshOptions', {'height': $("#droppable_story_div").height()});
        $('#loadable_story_table').bootstrapTable('load', window.appData.history.table);
        $('#loadable_story_table').bootstrapTable('hideLoading');
    }
}

function deleteDrop(operationKeyToDelete) {

    if (!window.appData.history.operation || !window.appData.history.operation[operationKeyToDelete]) {
        return; // Если вдруг операция не найдена, ничего не делаем
    }

    const operation = window.appData.history.operation[operationKeyToDelete];

    // delete operation from history

    delete window.appData.history.operation[operationKeyToDelete];

    updateJsonHistoryLoad();

    // create new tool in list

    window.appData.tools.push({
        cell: operation.cell,
        number: operation.number,
        tool: operation.tool,
        plan: operation.plan,
        group: operation.group
    });

    createToolForDrop();
}

window.deleteDrop = deleteDrop;