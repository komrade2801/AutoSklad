import { createToolForDrop } from './createToolForDrop.js'


// Функция для генерации JSON-History с историей текущей загрузки
export function updateJsonHistoryDrop() {


    console.log(window.appData.story.operation);

    window.appData.story.list = [];
    window.appData.story.table = [];

    for (const [key, operation] of Object.entries(window.appData.story.operation)) {
        console.log(key);
        console.log(operation);

        window.appData.story.table.push({
            operation: key,
            cell: operation.cell,
            number: operation.number,
            tool: operation.tool,
            plan: operation.plan,
            group: operation.group
        });

        window.appData.story.list.push({
            cell: String(operation.cell)
        });
    }

    createHistory();
}


function handleUnloadClick(toolName, groupName, cellNumber, cellId, planDesignation) {

    console.log(toolName, groupName, cellNumber, cellId, planDesignation);

    // Ничего не делаем, если содержимое пустое
    if (toolName === 'None') return;

    // Убедимся, что window.appData.story.operation существует
    if (!window.appData.story.operation) {
        window.appData.story.operation = {}; // Инициализируем, если это null или undefined
    }

    // create new operation in history

    const newKey = Object.keys(window.appData.story.operation).length + 1;

    window.appData.story.operation[newKey] = {
        cell: cellId,
        number: cellNumber,
        tool: toolName,
        plan: planDesignation,
        group: groupName
    }

    updateJsonHistoryDrop(toolName, groupName, cellNumber, cellId, planDesignation);

    // delete from tool list

    const index = window.appData.tools.findIndex(item => item.cell === cellId);

    if (index != -1) {
        // Если вдруг инструмент найден, удаляем из списка

        window.appData.tools.splice(index, 1); // Removes 1 element at the found index
        createToolForDrop();
    }

    show('none');
}

window.handleUnloadClick = handleUnloadClick;

function handleUnloadModalClick(elementButton) {
    console.log(elementButton);

    const obj = Object.fromEntries(Object.entries(elementButton.dataset));

    if (obj != undefined) {
        handleUnloadClick(obj.toolName, obj.groupName, obj.cellNumber, obj.cellId, obj.planDesignation)
    } else {
        show('none');
    }
}

window.handleUnloadModalClick = handleUnloadModalClick;



// Функция для создания строк истории на основе JSON-данных
export function createHistory() {
    console.log("history:")
    console.log(window.appData.story.table);

    if (window.appData.story.table != undefined) {
//        $('#droppable_story_table').bootstrapTable('refreshOptions', {'height': $("#droppable_story_div").height()});
        $('#droppable_story_table').bootstrapTable('load', window.appData.story.table);
        $('#droppable_story_table').bootstrapTable('hideLoading');
    }
}

function deleteDrop(operationKeyToDelete) {

    if (!window.appData.story.operation || !window.appData.story.operation[operationKeyToDelete]) {
        return; // Если вдруг операция не найдена, ничего не делаем
    }

    const operation = window.appData.story.operation[operationKeyToDelete];

    // delete operation from history

    delete window.appData.story.operation[operationKeyToDelete];

    updateJsonHistoryDrop();

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