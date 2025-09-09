import { jsonHistoryOperation } from '../../JSONs/history_operation.js'
import { createTableHistoryOperation } from './createTableHistoryOperation.js'

const currentFilters = {
    user: null,
    plan: null,
    operationType: null
};


  document.addEventListener("DOMContentLoaded", () => {
      // Получаем ссылки на элементы
      const dropdownItems = document.querySelectorAll("#type-menu .dropdown-item");
      const currentMenuDiv = document.querySelector("#type-menu .btn_vending");
      const userDiv = document.getElementById("user");
      const numberPlanDiv = document.getElementById("number-plan");
      const typeOperationDiv = document.getElementById("type-operation");

      // Устанавливаем начальное состояние
      currentMenuDiv.textContent = "-";
      userDiv.style.display = "none";
      numberPlanDiv.style.display = "none";
      typeOperationDiv.style.display = "none";

      // Добавляем обработчики событий для dropdown items
      dropdownItems.forEach(item => {
        item.addEventListener("click", (event) => {
          const selectedText = event.target.textContent;

          // Сброс фильтров
          currentFilters.user = null;
          currentFilters.plan = null;
          currentFilters.operationType = null;

          // Сброс текста кнопок
          document.querySelector('#user .btn_vending').textContent = 'Пользователь';
          document.querySelector('#number-plan .btn_vending').textContent = 'Номер чертежа';
          document.querySelector('#type-operation .btn_vending').textContent = 'Тип операции';


          // Перерисовать таблицу
          applyFilters(jsonHistoryOperation, 'column-1');

          // Управляем отображением div'ов
          if (selectedText === "Тип операции") {
            typeOperationDiv.style.display = "flex";
            userDiv.style.display = "none";
            numberPlanDiv.style.display = "none";
          } else if (selectedText === "Пользователи") {
            typeOperationDiv.style.display = "none";
            userDiv.style.display = "flex";
            numberPlanDiv.style.display = "none";
          } else if (selectedText === "Чертежи") {
            typeOperationDiv.style.display = "none";
            userDiv.style.display = "none";
            numberPlanDiv.style.display = "flex";
          }

          // Меняем текст текущего выбора
          currentMenuDiv.textContent = selectedText;
        });
      });
    });


//генерация выпадающего списка пользователей
export function populateUserDropdown(jsonHistoryOperation) {
    const userDropdown = document.querySelector('#user .dropdown-menu');
    const users = [...new Set(Object.values(jsonHistoryOperation.operation).map(op => op.user))];

    userDropdown.innerHTML = '';

    users.forEach(user => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.textContent = user;
        item.addEventListener('click', () => {
            document.querySelector('#user .btn_vending').textContent = user;
            currentFilters.user = user;
            applyFilters(jsonHistoryOperation, "column-1");
        });
        userDropdown.appendChild(item);
    });
}



//генерация выпадающего списка чертежей
export function populatePlanDropdown(jsonHistoryOperation) {
    const planDropdown = document.querySelector('#number-plan .dropdown-menu');
    const plans = [...new Set(Object.values(jsonHistoryOperation.operation).map(op => op.plan))];

    planDropdown.innerHTML = '';

    plans.forEach(plan => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.textContent = plan;
        item.addEventListener('click', () => {
            document.querySelector('#number-plan .btn_vending').textContent = plan;
            currentFilters.plan = plan;
            applyFilters(jsonHistoryOperation, "column-1");
        });
        planDropdown.appendChild(item);
    });
}



//генерация выпадающего списка операций
export function populateOperationTypeDropdown(jsonHistoryOperation) {
    const typeDropdown = document.querySelector('#type-operation .dropdown-menu');
    const types = [...new Set(Object.values(jsonHistoryOperation.operation).map(op => op.name_operation))];

    typeDropdown.innerHTML = '';

    types.forEach(type => {
        const item = document.createElement('a');
        item.className = 'dropdown-item';
        item.textContent = type;
        item.addEventListener('click', () => {
            document.querySelector('#type-operation .btn_vending').textContent = type;
            currentFilters.operationType = type;
            applyFilters(jsonHistoryOperation, "column-1");
        });
        typeDropdown.appendChild(item);
    });
}


//перерисовка таблицы в соответствии с фильтрами
function applyFilters(jsonHistoryOperation, containerId) {
    const allOperations = Object.values(jsonHistoryOperation.operation);

    const filtered = allOperations.filter(op => {
        return (!currentFilters.user || op.user === currentFilters.user) &&
               (!currentFilters.plan || op.plan === currentFilters.plan) &&
               (!currentFilters.operationType || op.name_operation === currentFilters.operationType);
    });

    // Заменяем содержимое контейнера
    const container = document.getElementById(containerId);
    container.innerHTML = ""; // очистка

    // Рисуем таблицу по отфильтрованным данным
    createTableHistoryOperation(containerId, { operation: Object.fromEntries(filtered.map((op, idx) => [idx, op])) });
}
