var qr_rows = []
function fillManualFields(elem) {
//    console.log(event.key)
    if (event.key === 'Tab') {
        event.preventDefault();
        console.log(elem.value);

        qr_rows.push(elem.value);
        elem.value = '';
    }
    if(event.key === 'Enter') {
        event.preventDefault();

        // Если в textarea остался текст, который не был добавлен в массив - добавляем его
        if (elem.value && elem.value.trim()) {
            qr_rows.push(elem.value);
            elem.value = '';
        }

        fetch("/backend/qr/", {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({'content': qr_rows})
          })
          .then(response => {
            if (!response.ok) {
              return response.text().then(text => {
                throw new Error(`Ошибка ${response.status}: ${text}`);
              });
            }
            return response.json();
          })
          .then(data => {
            console.log('Результат декодировки:', data);

            const enterpriseInput = document.getElementById('enterpriseInput');
            const designationInput = document.getElementById('designationInput');
            const nameInput = document.getElementById('nameInput');
            const descriptionInput = document.getElementById('descriptionInput');

            // Заполняем поля из новой структуры ответа
            enterpriseInput.value = data.enterprise || "";
            designationInput.value = data.designation || "";
            nameInput.value = data.name || "";
            descriptionInput.value = data.description || "";

            // Автоматически переключаем на вкладку "Ввести вручную" для возможности редактирования
            const autoTab = document.getElementById('tab2');
            if (autoTab) {
                autoTab.checked = true;
                // Триггерим событие change для обновления состояния полей
                autoTab.dispatchEvent(new Event('change'));
            }

            // Убеждаемся, что поля редактируемы
            enterpriseInput.disabled = false;
            designationInput.disabled = false;
            nameInput.disabled = false;
            descriptionInput.disabled = false;

            const qrCodeInput = document.getElementById('qrCodeInput');
            qrCodeInput.placeholder = 'QR-код отсканирован успешно'
            qrCodeInput.blur();
            qrCodeInput.value = '';

            qr_rows = []
          })
          .catch(err => {
            console.error('Ошибка при декодировании:', err);
            alert('Ошибка при декодировании QR-кода: ' + err.message);
          });
    }
}