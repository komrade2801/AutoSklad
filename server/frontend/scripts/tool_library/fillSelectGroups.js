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

// Функция для загрузки данных и создания таблицы
export async function loadGroupsData(device_number) {

    const element_tool_groups = document.getElementById('select_group');
    const element_group_groups = document.getElementById("select_parent_group");

    console.log(element_tool_groups);
    console.log(element_group_groups);

    const jsonGroups = await fetchGroupsData(device_number);
    if (jsonGroups) {
        console.log(jsonGroups);

        Object.values(jsonGroups.groups).forEach(group => {
            console.log(group);

            const group_opt = document.createElement('option');
            group_opt.value = group.id;
            group_opt.innerHTML = group.name;

            element_group_groups.appendChild(group_opt);

            let group_opt_copy = group_opt.cloneNode(true);

            element_tool_groups.appendChild(group_opt_copy);
        });
    } else {
        console.error("Не удалось загрузить данные для таблицы.");
    }
}