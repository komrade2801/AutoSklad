/**
 * Возвращает имя текущего HTML-файла, например "screen_2_mass_load.html".
 */
function getCurrentPageName() {
  // Получаем полный путь текущего URL (например "/folder/screen_2_mass_load.html")
  const path = window.location.pathname;
  // Разбиваем по "/" и берём последний элемент
  const segments = path.split('/');
  return segments.pop() || '';
}

// Пример использования:
const pageName = getCurrentPageName();
console.log('Текущая страница:', pageName);


/**
 * Загружает содержимое шапки из /assets/html/navbar.html
 * и вставляет внутрь <nav id="navbar">, затем выполняет нужную
 * инициализацию (активный экран, данные пользователя и т.п.).
 *
 */
// export function navbar_add(element_name) {
//   // Собираем URL с токеном
//   const token = localStorage.getItem('token');
//   const url = `/assets/html/navbar.html?token=${encodeURIComponent(token)}&screen_key=${encodeURIComponent(element_name)}`;

//   fetch(url)
//     .then(response => {
//       if (!response.ok) {
//         throw new Error(`Не удалось загрузить navbar: ${response.status}`);
//       }
//       return response.text();
//     })
//     .then(html => {
//       // Вставляем HTML внутрь <nav id="navbar">
//       const nav = document.getElementById('navbar');
//       nav.innerHTML = html;
//     })
//     .catch(err => {
//       console.error('Ошибка при загрузке navbar:', err);
//     });
// }

export function navbar_add(element_name) {
  const token = localStorage.getItem('token');
  const url = `/assets/html/navbar.html?token=${encodeURIComponent(token)}&screen_key=${encodeURIComponent(element_name)}`;

  return fetch(url)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Не удалось загрузить navbar: ${response.status}`);
      }
      return response.text();
    })
    .then(html => {
      document.getElementById('navbar').innerHTML = html;
    });
}

