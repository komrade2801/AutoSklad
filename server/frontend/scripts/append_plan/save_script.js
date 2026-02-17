  window.jsonPlan = {};

  function save_all_plans(device_number, plan_request, saveButton) {
    const url = `../backend/create_plan/${device_number}` + "?token=" + localStorage.getItem("token");
    // Редирект только после успешного ответа сервера (в .then ниже), не до завершения запроса
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(plan_request)
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
      console.log('Данные истории сохранены на сервере', data);
      const targetUrl = "./screen_7_plans.html";
      const token = localStorage.getItem('token');
      const full_url = targetUrl + "?token=" + token;
      window.location.href = full_url;
    })
    .catch(err => {
      console.error('Ошибка при сохранении чертежа/массовой загрузки:', err);
      showToast('Ошибка при сохранении: ' + (err.message || err), 'danger');
      if (saveButton) {
        saveButton.disabled = false;
        saveButton.textContent = 'Сохранить';
      }
    });
  }

  // Один обработчик на кнопку «Сохранить» — только через addEventListener, без дублирования
  const saveButtonEl = document.getElementById('saveButton');
  if (!saveButtonEl) {
    console.error('save_script: кнопка #saveButton не найдена');
  } else {
    saveButtonEl.addEventListener('click', function (event) {
      event.preventDefault();
      const saveButton = document.getElementById('saveButton');
      if (saveButton.disabled) return;

      // Блокируем повторное нажатие до завершения запроса или ошибки валидации
      saveButton.disabled = true;
      saveButton.textContent = 'Сохранение...';

      const enterpriseValue = document.getElementById('enterpriseInput').value;
      const nameValue = document.getElementById('nameInput').value;
      const descriptionValue = document.getElementById('descriptionInput').value;
      const designationValue = document.getElementById('designationInput').value;
      // Флаг «Сгенерировать массовую загрузку» — передаётся на бэкенд как create_mass_load (обязательно boolean)
      const createMassLoadCheckbox = document.getElementById("createMassLoad");
      const createMassLoad = createMassLoadCheckbox ? Boolean(createMassLoadCheckbox.checked) : true;

      if (nameValue === '') {
        showToast('Название чертежа не может быть пустым', 'warning');
        document.getElementById('nameInput').focus();
        saveButton.disabled = false;
        saveButton.textContent = 'Сохранить';
        return;
      }

      if (designationValue === '') {
        showToast('Номер чертежа не может быть пустым', 'warning');
        document.getElementById('designationInput').focus();
        saveButton.disabled = false;
        saveButton.textContent = 'Сохранить';
        return;
      }

      const plan_tools = window.appData.history.table;
      console.log(plan_tools);

      if (plan_tools.length === 0) {
        showToast('Необходимо выбрать инструменты', 'warning');
        saveButton.disabled = false;
        saveButton.textContent = 'Сохранить';
        return;
      }

      window.jsonPlan = {
        id: 0,
        enterprise: enterpriseValue || "Без предприятия",
        barcode: "",
        name: nameValue || "Без названия",
        description: descriptionValue || "Без описания",
        designation: designationValue || "Без обозначения",
        index_list: 0,
        list_count: 0,
        parent_plan_id: null,
        parent_plan: null,
        tools: plan_tools
      };

      const device_number = 1;
      const plan_request = {
        plan: window.jsonPlan,
        create_mass_load: createMassLoad
      };
      save_all_plans(device_number, plan_request, saveButton);
    });
  }


window.save_all_plans = save_all_plans;