// Функция для получения JSON-данных через эндпоинт
export async function fetchGroupsData(device_number) {
    // 1
    const url = "../backend/get_all_groups_from_db/?device_number=" + device_number;
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

/** Очищает выпадающие списки групп, оставляя только опцию "Нет" (value=0). */
function clearGroupsSelects() {
    const defaultOptionHtml = '<option value="0" selected>Нет</option>';
    const element_tool_groups = document.getElementById('select_group');
    const element_group_groups = document.getElementById("select_parent_group");
    if (element_tool_groups) {
        element_tool_groups.innerHTML = defaultOptionHtml;
    }
    if (element_group_groups) {
        element_group_groups.innerHTML = defaultOptionHtml;
    }
}

// Функция для загрузки данных и заполнения выпадающих списков групп (можно вызывать повторно при открытии модалок)
export async function loadGroupsData(device_number) {
    const element_tool_groups = document.getElementById('select_group');
    const element_group_groups = document.getElementById("select_parent_group");

    if (!element_tool_groups || !element_group_groups) {
        return;
    }

    clearGroupsSelects();

    const jsonGroups = await fetchGroupsData(device_number);
    if (jsonGroups && jsonGroups.groups) {
        Object.values(jsonGroups.groups).forEach(group => {
            const group_opt = document.createElement('option');
            group_opt.value = group.id;
            group_opt.innerHTML = group.name;

            element_group_groups.appendChild(group_opt);
            element_tool_groups.appendChild(group_opt.cloneNode(true));
        });
    } else {
        console.error("Не удалось загрузить данные групп.");
    }
}