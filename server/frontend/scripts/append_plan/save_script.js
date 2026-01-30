
  window.jsonPlan = {};

  function save_all_plans(device_number, plan_request, saveButton){
    const url = `../backend/create_plan/${device_number}`+"?token="+localStorage.getItem("token");
    // Редирект только после полного ответа сервера (в .then ниже) — fetch отправляет тело запроса до получения response
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
      let token = localStorage.getItem('token');
      let full_url = targetUrl + "?token=" + token;
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

  document.getElementById('saveButton').addEventListener('click', function () {
    const saveButton = document.getElementById('saveButton');
    if (saveButton.disabled) return;
    const enterpriseValue = document.getElementById('enterpriseInput').value;
    //const barcodeValue = document.getElementById('barcodeInput').value;
    const nameValue = document.getElementById('nameInput').value;
    const descriptionValue = document.getElementById('descriptionInput').value;
    const designationValue = document.getElementById('designationInput').value;
    const createMassLoad = document.getElementById("createMassLoad").checked;

    console.log("клик был");

    if (nameValue === '') {
        alert('Название чертежа не может быть пустым');
        document.getElementById('nameInput').focus();
        return;
    }

    if (designationValue === '') {
        alert('Номер чертежа не может быть пустым');
        document.getElementById('designationInput').focus();
        return;
    }

        // Подготовим объект tools с актуальными значениями из input'ов
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
          // tools[toolName] = toolCount.toString();
          tools.push({
            id: toolId,
            name: toolName,
            quantity: toolCount
          });
        }
    });

    // Валидация обязательных полей
    if (tools.length === 0) {
        alert('Необходимо выбрать инструменты');
        return;
    }

    window.jsonPlan = {
        id: 0,
        enterprise: enterpriseValue || "string",
        barcode: "",
        name: nameValue || "string",
        description: descriptionValue || "string",
        designation: designationValue || "string",
        index_list: 0,
        list_count: 0,
        parent_plan_id: null,
        parent_plan: null,
        tools: tools
    };

    console.log(window.jsonPlan);
    let device_number = 1;
    let plan_request = {'plan': window.jsonPlan, 'create_mass_load': createMassLoad};
    saveButton.disabled = true;
    saveButton.textContent = 'Сохранение...';
    save_all_plans(device_number, plan_request, saveButton);
  });


window.save_all_plans = save_all_plans;