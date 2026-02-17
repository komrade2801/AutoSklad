function navigateWithToken(url) {

  // Определяем абсолютный URL для сравнения: учитываем window.location.origin
  const targetUrl = new URL(url, window.location.origin).href;
    if (!url.includes(".html")) {
      // URL не содержит ".html"
      // Действия, если условие истинно
      console.log('Переход не требуется: URL не содержит .html');
      // window.location.reload();
      return;
    }
  // Если текущий URL совпадает с целевым, выходим из функции
  let savedUrl = localStorage.getItem('url');
  savedUrl = new URL(savedUrl, window.location.origin).href;
  if (savedUrl === targetUrl) {
    console.log('Переход не требуется: текущий URL совпадает с целевым.');
    return;
  }
  let token = localStorage.getItem('token');
  let full_url = targetUrl + "?token=" + token;
  window.location.href = full_url;
  return;
}

function extractPageName(url) {
  const match = url.match(/(\w+)\.html/);
  return match ? match[1] : 'default_name';
}


// Функция авторизации
function loginUser() {
  const login = document.getElementById('loginInput').value;
  const password = document.getElementById('passwordInput').value;
  // Формируем URL для запроса авторизации (здесь GET используется для простоты)
  const authUrl = `/backend/authorization?login=${encodeURIComponent(login)}&password=${encodeURIComponent(password)}`;
  fetch(authUrl, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Неверный логин или пароль');
    }
    return response.json();
  })
  .then(data => {
    // Ожидается, что сервер вернул поля token и redirect_url
    const token = data.token;
    if (!token) {
      throw new Error('Токен не получен');
    }

    localStorage.setItem('token', token);
    // Сохраняем данные пользователя, если они есть
    localStorage.setItem('user', JSON.stringify(data.user));    
    // Сохраняем токен в localStorage
    // Переходим на страницу, выбранную на сервере
    navigateWithToken(data.redirect_url);
    // Сохраняем токен в localStorage

    
    // Вместо использования fetch + document.write, делаем полноценный редирект:
    // window.location.href = data.redirect_url;
    //return;
  })
  .catch(error => {
    console.error('Ошибка авторизации:', error);
    showToast(error.message, 'danger');
  });
}


// // Делаем функцию доступной глобально
// window.navigateWithToken = navigateWithToken;
// // Делаем функцию доступной глобально
// window.loginUser = loginUser;

// обработчик кнопки вход на экране авторизации.
document.addEventListener('DOMContentLoaded', () => {
  // Общая инициализация для основной страницы
  try {
    document.getElementById('login').addEventListener('click', loginUser);
  } catch (error) {

  }
});

// Функция для показа toast уведомлений
function showToast(message, type = 'info', title = '') {
    // Создаем контейнер для toast, если его нет
    let toastContainer = document.querySelector('.toast-container.position-fixed.top-0.end-0');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Создаем toast элемент
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    // Определяем заголовок в зависимости от типа
    const defaultTitles = {
        'success': 'Успех',
        'danger': 'Ошибка',
        'warning': 'Предупреждение',
        'info': 'Информация'
    };

    const toastTitle = title || defaultTitles[type] || 'Уведомление';

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${toastTitle}:</strong> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Закрыть"></button>
        </div>
    `;

    // Добавляем toast в контейнер
    toastContainer.appendChild(toastEl);

    // Показываем toast
    const toast = new bootstrap.Toast(toastEl, {
        delay: 5000 // Автоматическое скрытие через 5 секунд
    });
    toast.show();

    // Удаляем toast из DOM после скрытия
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

// Делаем функцию глобальной
window.showToast = showToast;
