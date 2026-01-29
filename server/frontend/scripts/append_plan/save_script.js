
  window.jsonPlan = {};

  function save_all_plans(device_number, plan_request){
    const url = `../backend/create_plan/${device_number}`+"?token="+localStorage.getItem("token");
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
      console.error('Ошибка при сохранении истории:', err);
    });
  }

  document.getElementById('saveButton').addEventListener('click', function () {
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

        // Подготовим объект tools с актуальными значениями из input'ов (только строки выбора — .tool-row-block)
    const toolsContainer = document.getElementById("selection_tools");
    const toolRows = toolsContainer.querySelectorAll(".tool-row-block");
    const tools = [];

    toolRows.forEach(div => {
        const nameDiv = div.querySelector(".tool-name-block");
        const input = div.querySelector(".input_amount");

        if (nameDiv && input) {
            const toolIdRaw = nameDiv.getAttribute('data-tool-id');
            const toolId = toolIdRaw != null ? parseInt(toolIdRaw, 10) : NaN;
            if (Number.isNaN(toolId)) return;
            const toolName = nameDiv.textContent.trim();
            const toolCount = parseInt(input.value, 10) || 1;
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
    const device_number = 1;
    const plan_request = { plan: window.jsonPlan, create_mass_load: createMassLoad };
    save_all_plans(device_number, plan_request);
    // Перенаправление выполняется в save_all_plans после успешного ответа
  });


window.save_all_plans = save_all_plans;