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
    }

    #v-pills-tab.sidebar-collapsed {
      width: 0 !important;
      padding: 0 !important;
      border: none !important;
    }

    .sidebar-buttons-wrap {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    #v-pills-tab.sidebar-collapsed .sidebar-buttons-wrap {
      opacity: 0;
      pointer-events: none;
      height: 0;
      overflow: hidden;
    }

    #sidebar-toggle:hover {
      background: rgba(0, 49, 114, 0.9) !important;
      color: rgb(200, 225, 255) !important;
    }
  `;
  document.head.appendChild(style);
}

// ── Глобальная функция toggle (вызывается кнопкой из navbar) ──
const SIDEBAR_STORAGE_KEY = 'sidebar_collapsed';

window.toggleSidebar = function () {
  const sidebar = document.getElementById('v-pills-tab');
  if (!sidebar) return;

  const nowCollapsed = !sidebar.classList.contains('sidebar-collapsed');
  localStorage.setItem(SIDEBAR_STORAGE_KEY, nowCollapsed);
  _applySidebarState(sidebar, nowCollapsed);
};

function _applySidebarState(sidebar, isCollapsed) {
  if (isCollapsed) {
    sidebar.classList.add('sidebar-collapsed');
  } else {
    sidebar.classList.remove('sidebar-collapsed');
  }
  // Корректируем ширину соседней контент-панели
  const contentPanel = sidebar.nextElementSibling;
  if (contentPanel) {
    contentPanel.style.width = isCollapsed
      ? '100%'
      : 'calc(100% - 235px)';
  }
}


export function nav_btn_add(element_name) {
  fetch('/assets/html/nav_btn.html?token=' + localStorage.getItem('token'))
    .then(response => response.text())
    .then(html => {
      const sidebar = document.getElementById('v-pills-tab');
      if (!sidebar) return;

      // Оборачиваем кнопки навигации
      sidebar.innerHTML = '<div class="sidebar-buttons-wrap">' + html + '</div>';

      // Подсвечиваем активную кнопку
      const active = document.getElementById(element_name);
      if (active) {
        active.classList.remove('btn_vending');
        active.classList.add('btn_vending_active');
      }

      // Применяем сохранённое состояние
      const collapsed = localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
      _applySidebarState(sidebar, collapsed);
    });
}
