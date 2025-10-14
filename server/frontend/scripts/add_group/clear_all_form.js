// Функция для очистки полей ввода и сброса значений select
function clearAllForm() {
    document.querySelectorAll(".form-control").forEach(input => {
        input.value = "";
    });

    document.querySelectorAll("select").forEach(select => {
        select.value = "0";
    });
}