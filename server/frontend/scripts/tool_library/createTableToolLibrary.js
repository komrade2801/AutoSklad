var show_conf = function (state) {
    document.getElementById('modal_window_confirmation').style.display = state
    document.getElementById('membrane').style.display = state
}

function openModalConf() {
    show_conf('flex');  // Открываем модальное окно
}

window.openModalConf = openModalConf;
window.show_conf = show_conf;

export function createTableToolLibrary(jsonToolLibrary) {

    console.log('createTableToolLibrary');
    const data = jsonToolLibrary["tools"];
    console.log(data);

    if (data != undefined) {
        $('#tool_library_table').bootstrapTable('load', data);
        $('#tool_library_table').bootstrapTable('hideLoading');
    }

    const group_data = jsonToolLibrary["groups"];
    console.log(group_data);

    if (group_data != undefined) {
        $('#group_library_table').bootstrapTable('load', group_data);
        $('#group_library_table').bootstrapTable('hideLoading');
    }
}


// Функция для получения JSON-данных через эндпоинт
export async function fetchToolLibraryData(device_number) {
    // 1
    const url = "../backend/get_groups_from_db/?device_number=" + device_number;
    console.log(url);
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: " + response.status);
        }
        const jsonData = await response.json();
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}