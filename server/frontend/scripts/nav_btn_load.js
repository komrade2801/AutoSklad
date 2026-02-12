// ── Динамические стили для sidebar ──
if (!document.getElementById('sidebar-toggle-styles')) {
  const style = document.createElement('style');
  style.id = 'sidebar-toggle-styles';
  style.textContent = `
    #v-pills-tab {
      position: relative;
      flex-shrink: 0;
      transition: width 0.25s ease, padding 0.25s ease;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      background: rgba(255, 255, 255, 0.07);
      border-right: 1.5px solid rgba(78, 155, 229, 0.45);
      width: 250px !important;
      margin-top: 0 !important;
      padding-top: 10px;
      padding-left: 10px !important;
      padding-right: 10px;
    }

    #v-pills-tab.sidebar-collapsed {
      width: 30px !important;
      padding-left: 3px !important;
      padding-right: 3px !important;
      align-items: center;
    }

    /* ── Строка с кнопкой toggle ── */
    .sidebar-toggle-row {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      padding: 0 0 5px 0;
      margin-bottom: 4px;
      border-bottom: 1.5px solid rgba(78, 155, 229, 0.45);
      flex-shrink: 0;
      transition: justify-content 0.25s ease;
    }

    #v-pills-tab.sidebar-collapsed .sidebar-toggle-row {
      justify-content: center;
    }

    /* ── Кнопка toggle ── */
    .sidebar-toggle-btn {
      height: 24px;
      min-height: 24px;
      padding: 0;
      border: 1px solid rgba(78, 155, 229, 0.5);
      border-radius: 4px;
      background: rgba(0, 49, 114, 0.6);
      color: rgb(131, 173, 239);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      z-index: 10;
      transition: width 0.25s ease;
      /* раскрыт — на всю ширину как кнопки навигации */
      width: 100%;
    }

    /* свёрнут — компактный квадрат */
    #v-pills-tab.sidebar-collapsed .sidebar-toggle-btn {
      width: 24px;
    }

    .sidebar-toggle-btn:hover {
      background: rgba(0, 49, 114, 0.9);
      color: rgb(200, 225, 255);
    }


    /* ── Иконки burger / close ── */
    .sidebar-toggle-btn .icon-burger,
    .sidebar-toggle-btn .icon-close {
      transition: opacity 0.2s ease, transform 0.2s ease;
    }

    .sidebar-toggle-btn .icon-close {
      position: absolute;
      opacity: 0;
      transform: rotate(-90deg);
    }

    /* Когда sidebar раскрыт — показываем крестик, прячем бургер */
    #v-pills-tab:not(.sidebar-collapsed) .sidebar-toggle-btn .icon-burger {
      opacity: 0;
      transform: rotate(90deg);
    }
    #v-pills-tab:not(.sidebar-collapsed) .sidebar-toggle-btn .icon-close {
      opacity: 1;
      transform: rotate(0deg);
    }

    /* ── Обёртка кнопок ── */
    .sidebar-buttons-wrap {
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: opacity 0.2s ease;
    }

    #v-pills-tab.sidebar-collapsed .sidebar-buttons-wrap {
      opacity: 0;
      pointer-events: none;
      height: 0;
      overflow: hidden;
    }
  `;
  document.head.appendChild(style);
}


export function nav_btn_add(element_name) {
  fetch('/assets/html/nav_btn.html?token=' + localStorage.getItem('token'))
    .then(response => response.text())
    .then(html => {
      const sidebar = document.getElementById('v-pills-tab');
      if (!sidebar) return;

      // Запоминаем соседний контент-блок
      const contentPanel = sidebar.nextElementSibling;

      // Формируем строку с toggle-кнопкой + обёртку кнопок
      sidebar.innerHTML =
        '<div class="sidebar-toggle-row">' +
          '<button id="sidebar-toggle" class="sidebar-toggle-btn" type="button" title="Меню навигации">' +
            '<svg class="icon-burger" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">' +
              '<path d="M2 3.5h12v1.5H2zm0 4h12v1.5H2zm0 4h12v1.5H2z"/>' +
            '</svg>' +
            '<svg class="icon-close" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">' +
              '<path d="M3.17 3.17a.75.75 0 0 1 1.06 0L8 6.94l3.77-3.77a.75.75 0 1 1 1.06 1.06L9.06 8l3.77 3.77a.75.75 0 1 1-1.06 1.06L8 9.06l-3.77 3.77a.75.75 0 0 1-1.06-1.06L6.94 8 3.17 4.23a.75.75 0 0 1 0-1.06z"/>' +
            '</svg>' +
          '</button>' +
        '</div>' +
        '<div class="sidebar-buttons-wrap">' + html + '</div>';

      // Подсвечиваем активную кнопку
      const active = document.getElementById(element_name);
      if (active) {
        active.classList.remove('btn_vending');
        active.classList.add('btn_vending_active');
      }

      // ── Toggle-логика ──
      const STORAGE_KEY = 'sidebar_collapsed';
      const collapsed = localStorage.getItem(STORAGE_KEY) === 'true';

      function applySidebarState(isCollapsed) {
        if (isCollapsed) {
          sidebar.classList.add('sidebar-collapsed');
        } else {
          sidebar.classList.remove('sidebar-collapsed');
        }
        // Корректируем ширину контент-панели
        if (contentPanel) {
          contentPanel.style.width = isCollapsed
            ? 'calc(100% - 30px)'
            : 'calc(100% - 250px)';
        }
      }

      // Применяем сохранённое состояние
      applySidebarState(collapsed);

      // Обработчик клика
      document.getElementById('sidebar-toggle').addEventListener('click', () => {
        const nowCollapsed = !sidebar.classList.contains('sidebar-collapsed');
        localStorage.setItem(STORAGE_KEY, nowCollapsed);
        applySidebarState(nowCollapsed);
      });
    });
}
