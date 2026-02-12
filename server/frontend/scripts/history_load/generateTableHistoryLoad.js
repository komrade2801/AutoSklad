import { openModal } from './modal_window_14.js'

export function generateTableHistoryLoad() {

    console.log("generateTableHistoryLoad")
    console.log(window.appData.history_loads.operation)

    if (window.appData.history_loads.operation != undefined) {
//        $('#droppable_tools_table').bootstrapTable('refreshOptions', {'height': $("#droppable_tools_div").height()});
        $('#history_load_table').bootstrapTable('load', window.appData.history_loads.operation);
        $('#history_load_table').bootstrapTable('hideLoading');
    }
    return;
}