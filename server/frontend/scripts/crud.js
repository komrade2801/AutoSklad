
// Функция для получения JSON-данных через эндпоинт
export async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Ошибка сети, статус: ${response.status}");
        }
        const jsonData = await response.json();
        return jsonData;
    } catch (error) {
        console.error("Ошибка получения данных:", error);
        return null;
    }
}

/*
 * Функция загрузки и сохранения JSON.
 * Возвращает Promise, чтобы можно было ждать результата.
 */
export function initData(url) {
    return fetchData(url)
      .then(data => {
        return data;
      })
      .catch(err => {
        console.error('Не удалось загрузить инструменты', err);
        return null;
      });
}

// crud.js
export async function saveUserData(userObj) {
    const token = localStorage.getItem('token');
    const response = await fetch('../backend/create_user?token='+token, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userObj),
    });
    if (!response.ok) {
      const err = await response.text();
      throw new Error(`Ошибка сохранения: ${err}`);
    }
    return response.json();
  }