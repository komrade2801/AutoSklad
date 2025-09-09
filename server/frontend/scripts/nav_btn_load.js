export function nav_btn_add(element_name) {
  fetch('/assets/html/nav_btn.html?token='+localStorage.getItem('token'))
    .then(response => response.text())
    .then(html => {
      document.getElementById('v-pills-tab').innerHTML = html;
      const element = document.getElementById(element_name);
      if (element) {
        element.classList.remove('btn_vending');
        element.classList.add('btn_vending_active'); // Добавит класс "btn_vending_active"
        }
      }
    );
}
