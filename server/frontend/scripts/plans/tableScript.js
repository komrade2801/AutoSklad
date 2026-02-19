// Универсальная функция для модального подтверждения удаления
function showDeleteConfirm(message) {
    return new Promise((resolve) => {
        // Устанавливаем текст сообщения
        document.getElementById('deleteConfirmMessage').textContent = message;

        // Показываем модальное окно
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();

        // Обработчики кнопок
        const confirmBtn = document.getElementById('confirmDeleteBtn');
        const cancelBtn = document.getElementById('cancelDeleteBtn');

        const handleConfirm = () => {
            modal.hide();
            cleanup();
            resolve(true);
        };

        const handleCancel = () => {
            modal.hide();
            cleanup();
            resolve(false);
        };

        const cleanup = () => {
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
        };

        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);

        // Обработчик закрытия модального окна по крестику или клику вне
        document.getElementById('deleteConfirmModal').addEventListener('hidden.bs.modal', () => {
            cleanup();
            resolve(false);
        }, { once: true });
    });
}

// Функция для открытия модального окна списка инструментов
function openPlanToolListModal(plan_designation, plan_tools) {
    document.getElementById('modal_plan_tools_id').textContent = plan_designation;

    if (plan_tools != undefined) {

//        show_random_plan('flex');  // Открываем модальное окно

        showToolModal(true);
//        $('#random_plan_table').bootstrapTable('refreshOptions', {'height': $("#random_plan_div").height()});
        $('#random_plan_table').bootstrapTable('showLoading');
        $('#random_plan_table').bootstrapTable('load',plan_tools);
        $('#random_plan_table').bootstrapTable('hideLoading');
    }
}


function actionToolsFormatter(value, row, index, field) {

     let actionsDiv = document.createElement("div");
     actionsDiv.className = "table-actions";

     // Tool list button
     let toolListButton = document.createElement("i");
     toolListButton.className = "bi bi-list-ol action-button";
     toolListButton.title = "Показать список инструментов";

     toolListButton.addEventListener('click', async function () {
        openPlanToolListModal(row.designation, row.tools);
     });

     actionsDiv.appendChild(toolListButton);

     // Barcode button
     let barcodeButton = document.createElement("i");
     barcodeButton.className = "bi bi-qr-code action-button";
     barcodeButton.title = "Показать штрихкод";

     barcodeButton.addEventListener('click', async function () {
        openModalBarcode(row.id, row.designation);
     });

     actionsDiv.appendChild(barcodeButton);

     // Edit button
     let editButton = document.createElement("i");
     editButton.className = "bi bi-pencil-fill action-button";
     editButton.title = "Редактировать чертеж";

     editButton.addEventListener('click', async function () {
         const toolTypeId = row.id;
         if (!toolTypeId) {
             console.error("ID чертежа не найден");
             return;
         }

         // Проверяем, занят ли инструмент
         try {
             const checkResponse = await fetch(`/backend/check_tool_busy/${toolTypeId}`);
             if (!checkResponse.ok) {
                 throw new Error("Ошибка проверки чертежа");
             }
             const checkData = await checkResponse.json();

             if (checkData.is_busy) {
                 showToast("Данный инструмент используется в вендинге. Редактировать можно только свободный инструмент. " + checkData.message, 'warning');
                 return;
             }

             // Переходим на страницу редактирования с параметром tool_type_id
             let url = '../screen_16_add_tool.html';
             let targetUrl = new URL(url, window.location.origin).href;
             let token = localStorage.getItem('token');
             let full_url = targetUrl + "?token=" + token + "&tool_type_id=" + toolTypeId;
             window.location.href = full_url;
         } catch (error) {
             console.error('Ошибка при проверке инструмента:', error);
             showToast('Ошибка при проверке инструмента', 'danger');
         }
     });

     actionsDiv.appendChild(editButton);

     // Delete button
     let deleteButton = document.createElement("i");
     deleteButton.className = "bi bi-x-circle action-button";
     deleteButton.title = "Удалить чертеж";

     deleteButton.addEventListener('click', async function () {
         const toolTypeId = row.id;
         if (!toolTypeId) {
             console.error("ID инструмента не найден");
             return;
         }

         // Подтверждение удаления
         const confirmed = await showDeleteConfirm("Вы уверены, что хотите удалить этот чертёж?");
         if (!confirmed) {
             return;
         }

         // Удаляем инструмент (endpoint сам проверит занятость)
         try {
             const deleteResponse = await fetch(`/backend/delete_tool_type/${toolTypeId}`, {
                 method: 'DELETE'
             });

             if (!deleteResponse.ok) {
                 const errorData = await deleteResponse.json();
                 showToast(errorData.detail || "Ошибка при удалении чертежа", 'danger');
                 return;
             }

             const result = await deleteResponse.json();
             showToast(result.message || "Чертёж успешно удален", 'success');

             // Перезагружаем страницу для обновления таблицы
             let url = './screen_7_plans.html';
             let targetUrl = new URL(url, window.location.origin).href;
             let token = localStorage.getItem('token');
             let full_url = targetUrl + "?token=" + token;
             window.location.href = full_url;
         } catch (error) {
             console.error('Ошибка при удалении чертежа:', error);
             showToast('Ошибка при удалении чертежа', 'danger');
         }
     });

     actionsDiv.appendChild(deleteButton);

     return actionsDiv;
}

/**
 * Устанавливает в модалку URL изображения и открывает её (Bootstrap 5).
 * @param {number} planId
 * @param {string} planDesignation
 */
function openModalBarcode(planId, planDesignation) {
    document.getElementById('modal_plan_id').textContent = planDesignation || '';

    const img = document.getElementById('modal_barcode_img');
    img.src = `/backend/plan_barcode?plan_index=${encodeURIComponent(planId)}`;
    img.alt = 'Штрихкод чертежа';
    img.onerror = () => {
        console.error('Не удалось загрузить штрих‑код');
        img.alt = 'Ошибка загрузки';
    };

    showBarcodeModal(true);
}

// Функция для отображения модального окна штрихкода (Bootstrap 5)
function showBarcodeModal(show) {
    const modalEl = document.getElementById('modal_window_barcode');
    if (!modalEl) return;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    if (show) {
        modal.show();
    } else {
        modal.hide();
    }
}

window.showBarcodeModal = showBarcodeModal;