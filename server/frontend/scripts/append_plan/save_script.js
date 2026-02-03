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
      alert('Ошибка при сохранении: ' + (err.message || err));
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
        alert('Название чертежа не может быть пустым');
        document.getElementById('nameInput').focus();
        saveButton.disabled = false;
        saveButton.textContent = 'Сохранить';
        return;
      }

      if (designationValue === '') {
        alert('Номер чертежа не может быть пустым');
        document.getElementById('designationInput').focus();
        saveButton.disabled = false;
        saveButton.textContent = 'Сохранить';
        return;
      }

      const toolsContainer = document.getElementById("selection_tools");
      const toolDivs = toolsContainer.querySelectorAll("div");
      const tools = [];

      toolDivs.forEach(div => {
        const nameDiv = div.querySelector(".toolName") || div.firstChild;
        const input = div.querySelector(".input_amount");

        if (nameDiv && input) {
          const toolId = nameDiv.getAttribute('data-tool-id');
          const toolName = nameDiv.textContent.trim();
          const toolCount = parseInt(input.value, 10) || 1;
          tools.push({
            id: toolId,
            name: toolName,
            quantity: toolCount
          });
        }
      });

      if (tools.length === 0) {
        alert('Необходимо выбрать инструменты');
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
        tools: tools
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