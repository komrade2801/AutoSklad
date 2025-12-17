import { createTableRandomDrop } from './createTableRandomDrop.js';
import { nav_btn_add } from '../nav_btn_load.js';
import { navbar_add } from '../navbar.js';
import { initData } from '../crud.js';

window.jsonHistoryRandomDrop = window.jsonHistoryRandomDrop || {};

function Id_title() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get("ID_drop");
  let num = NaN;
  if (raw) {
    const m = raw.match(/№\s*(\d+)/);
    num = m ? Number(m[1]) : NaN;
    const el = document.getElementById("title");
    if (el) el.textContent = `Выгрузка № ${num}`;
  }
  return num;
}

function initialization(element_name) {
    if (localStorage.getItem('token') === null){
        console.log('token не обнаружен в хранилище!');
        window.location.href='/';
        return;
    }

    nav_btn_add(element_name);

  // Сначала грузим navbar, а потом всё остальное
  navbar_add(element_name).then(() => {
    const idNumber = Id_title();
    if (isNaN(idNumber)) {
      console.error("Не удалось извлечь номер выгрузки");
      return;
    }

    initData(`../backend/random_drop?ID_drop=${idNumber}`)
      .then(data => {
        if (data) {
          window.jsonHistoryRandomDrop = data;
          createTableRandomDrop(data, 'column-1');
        }
      })
      .catch(err => console.error("Ошибка загрузки данных:", err));
  }).catch(err => {
    console.error("Не удалось загрузить navbar:", err);
  });
}

window.initialization = initialization;