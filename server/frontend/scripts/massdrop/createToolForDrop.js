// Функция для создания строк инструмента на основе JSON-данных
export function createToolForDrop() {
    console.log(window.appData.tools);

    if (window.appData.tools != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#droppable_tools_table').bootstrapTable('load', window.appData.tools);
        $('#droppable_tools_table').bootstrapTable('hideLoading');
    }
}