/**
 * Отправляет историю массовой загрузки на бэкенд.
 * @param {number} deviceNumber — номер устройства (подставьте ваш актуальный ID)
 */
export function saveHistoryAsMassLoad(deviceNumber) {
  const url = `../backend/mass_load_tools/${deviceNumber}`+"?token="+localStorage.getItem("token");
  const history = window.appData.history || {};
  console.log(url);
  console.log('Sending history:', history);
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(history)
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
    const targetUrl = "./screen_14_history_load.html";
    let token = localStorage.getItem('token');
    let full_url = targetUrl + "?token=" + token;
    window.location.href = full_url;
  })
  .catch(err => {
    console.error('Ошибка при сохранении истории:', err);
    showToast('Не удалось сохранить историю: ' + err.message, 'danger');
  });
}

// Делаем функцию доступной глобально (если нужно вызывать из HTML)
window.saveHistoryAsMassLoad = saveHistoryAsMassLoad;
