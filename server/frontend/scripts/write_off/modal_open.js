    // Функция для открытия модального окна
function openModalConfirmation() {
    console.log("функция OMC вызвана")
    // Заполняем данные в модальном окне (это может быть динамическое содержимое)
    //document.querySelector('.cell_number').textContent = 'Ячейка № ' + cellNumber;
    //document.querySelector('img').src = 'image_' + cellNumber + '.jpg'; // Изменить путь к изображению
    //document.querySelector('.tool_group').textContent = 'Группа: Группа ' + cellNumber;
    //document.querySelector('.tool_name').textContent = 'Инструмент: ' + toolName;
    //document.querySelector('.plan_name').textContent = 'Чертёж: ' + planName;

    show('flex');  // Открываем модальное окно
}

window.openModalConfirmation = openModalConfirmation;