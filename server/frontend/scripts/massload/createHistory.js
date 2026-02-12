// Функция для создания строк истории на основе JSON-данных
export function createHistory() {

    console.log(window.appData.history);

    if (window.appData.history != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#loadable_story_table').bootstrapTable('load', window.appData.history);
        $('#loadable_story_table').bootstrapTable('hideLoading');
    }

    return;
}
