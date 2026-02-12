import { openModal } from './modal_window_13.js'

export function generateTableHistoryDrop() {

    console.log("generateTableHistoryDrop")
    console.log(window.appData.history_drops.operation)

    if (window.appData.history_drops.operation != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#history_drop_table').bootstrapTable('load', window.appData.history_drops.operation);
        $('#history_drop_table').bootstrapTable('hideLoading');
    }
    return;
}