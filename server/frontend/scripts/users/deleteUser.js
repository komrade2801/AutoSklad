import { generateTableUsers } from './createTableAllUsers.js'


function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Ошибка при разборе токена:", e);
    return null;
  }
}



function deleteUser() {
console.log("функция удаления вызвана")
  const userIndex = window.userIndexToDelete;

  if (userIndex == null) {
    console.error("Индекс пользователя не задан");
    return;
  }

    // запрет на удаление текущего пользователя
//  const token = localStorage.getItem('token');
//  const currentUser = parseJwt(token);
//
//  if (!currentUser || currentUser.index == null) {
//    console.error("Не удалось определить текущего пользователя");
//    return;
//  }
//
//  if (currentUser.index === userIndex) {
//    alert("Нельзя удалить текущего пользователя.");
//    return;
//  }

  const userPos = window.jsonUsers.findIndex(user => user.index === userIndex);

  if (userPos === -1) {
    console.error("Пользователь не найден");
    return;
  }

  // Отправляем запрос на удаление
  fetch(`/backend/delete_user/${userIndex}`, {
    method: 'DELETE',
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`Ошибка удаления пользователя: ${response.statusText}`);
    }

    // Удаляем из локального массива и обновляем таблицу
    window.jsonUsers.splice(userPos, 1);
    generateTableUsers('column-1', window.jsonUsers);
    show_conf('none');
    window.userIndexToDelete = null;
  })
  .catch(error => {
    console.error("Ошибка при удалении пользователя:", error);
  });
}

window.deleteUser = deleteUser;
