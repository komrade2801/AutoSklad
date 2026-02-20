// Функция для отображения модального окна с инструментами (Bootstrap 5)
function showToolModal(show) {
    const modalEl = document.getElementById('modal_window_tool');
    if (!modalEl) return;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    if (show) {
        modal.show();
    } else {
        modal.hide();
    }
}

window.showToolModal = showToolModal;



/**
 * Печать содержимого модалки (только картинки).
 */
export function printBarcode() {
    const img = document.getElementById('modal_barcode_img');
    const title = document.getElementById('modal_barcode_plan_title');

    const width = img.width;
    const height = img.height;

    const left = (window.screen.width / 2) - (width / 2);
    const top = (window.screen.height / 2) - (height / 2);

    const printWindow = window.open('', '_blank', 'width=${width},height=${height},top=${top},left=${left}');

    printWindow.document.write(`<img src="${img.src}" onload="window.print()">`);
    printWindow.document.write(`<p style="font-family: 'Roboto', sans-serif; font-size: 2rem; font-weight: 600; margin-top: -1rem; color: #000000; width: 285px; text-align: center;">${title.innerHTML}</p>`);

    printWindow.document.close(); // Завершаем запись
    printWindow.focus(); // Фокусируем новое окно
}

window.printBarcode = printBarcode;

export function createTableAllPlans(containerId, jsonAllPlans) {

    console.log('createTableAllPlans');
    console.log(jsonAllPlans);

    const data = Array.isArray(jsonAllPlans) ? jsonAllPlans : (jsonAllPlans ? jsonAllPlans["plans"] : []);
    console.log(data);

    $('#plans_table').bootstrapTable('load', data);
    $('#plans_table').bootstrapTable('hideLoading');

    // Выравниваем тулбар после загрузки данных
    if (window.alignToolbar) {
        window.alignToolbar('#plans_table');
    }
}
