import { createTableToolLibrary } from './createTableToolLibrary.js?v=3';
import { loadToolLibraryTable } from './createTableToolLibrary.js?v=3';
import { fetchToolLibraryData } from './createTableToolLibrary.js?v=3';

//import { jsonToolLibrary } from '../../JSONs/tool_library.js';
import { nav_btn_add } from '../nav_btn_load.js';

import { navbar_add } from '../navbar.js';

//export const jsonObjectCells = generateJsonCells(32, 32);
//export const jsonObjectHistory = {};


async function confirmDeleteToolType() {
    if (!window.toolTypeToDelete) {
        alert("Ошибка: не выбран тип инструмента для удаления");
        show_conf('none');
        return;
    }

    const toolTypeId = window.toolTypeToDelete;
    const url = `../backend/tool_types/${toolTypeId}`;

    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const successData = await response.json();
            alert(successData.message || "Тип инструмента успешно удален");
            // Refresh the table
            const container = document.getElementById("column-1");
            container.innerHTML = ""; // Clear existing table
            let device_number = 1;
            loadToolLibraryTable("column-1", device_number);
        } else {
            const errorData = await response.json();
            let errorMessage = "Неизвестная ошибка при удалении";

            if (response.status === 404) {
                errorMessage = "Тип инструмента не найден";
            } else if (response.status === 500) {
                const detail = errorData.detail || "";
                if (detail.includes("Не удалось удалить инструмент")) {
                    errorMessage = "Не удалось удалить связанные инструменты";
                } else if (detail.includes("Не удалось удалить тип инструмента")) {
                    errorMessage = "Не удалось удалить тип инструмента";
                } else if (detail.includes("Ошибка при удалении типа инструмента")) {
                    errorMessage = "Внутренняя ошибка сервера при удалении";
                } else {
                    errorMessage = "Ошибка сервера при удалении";
                }
            }

            alert(`Ошибка при удалении: ${errorMessage}`);
        }
    } catch (error) {
        console.error("Ошибка сети:", error);
        alert("Ошибка сети при удалении типа инструмента");
    }

    // Close modal
    show_conf('none');
    // Clear the stored id
    window.toolTypeToDelete = null;
}

function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
    }
    let device_number = 1;
    nav_btn_add(element_name);
    navbar_add(element_name);
    loadToolLibraryTable("column-1", device_number);
}

// Make function global
window.confirmDeleteToolType = confirmDeleteToolType;

// Делаем функцию доступной глобально
window.initialization = initialization;
