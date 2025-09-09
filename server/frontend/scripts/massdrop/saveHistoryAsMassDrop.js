// historySender.js

// import { jsonObjectHistory } from './init.js';

/**
 * Отправляет историю массовой загрузки на бэкенд.
 * @param {number} deviceNumber — номер устройства (подставьте ваш актуальный ID)
 */
export function saveHistoryAsMassDrop(deviceNumber) {
  const url = `../backend/mass_drop_tools/${deviceNumber}`+"?token="+localStorage.getItem("token");
  console.log(url);
  let jsonObjectHistory = window.appData.story;
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(jsonObjectHistory)
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
    console.log('История успешно отправлена:', data);
    // alert('Данные истории сохранены на сервере');
    const targetUrl = "./screen_13_history_drop.html";
    let token = localStorage.getItem('token');
    let full_url = targetUrl + "?token=" + token;
    window.location.href = full_url;
  })
  .catch(err => {
    console.error('Ошибка при сохранении истории:', err);
    alert('Не удалось сохранить историю:\n' + err.message);
  });
}

// Делаем функцию доступной глобально (если нужно вызывать из HTML)
window.saveHistoryAsMassDrop = saveHistoryAsMassDrop;
