
  window.jsonPlan = {};

  export function save_all_plans(device_number, json_plan){
    const url = `../backend/create_plan/${device_number}`+"?token="+localStorage.getItem("token");
    console.log(url);
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(json_plan)
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
      alert('Не удалось сохранить данные:\n' + err.message);
    });
  }

  document.getElementById('saveButton').addEventListener('click', function () {
    const enterpriseValue = document.getElementById('enterpriseInput').value;
    //const barcodeValue = document.getElementById('barcodeInput').value;
    const nameValue = document.getElementById('nameInput').value;
    const descriptionValue = document.getElementById('descriptionInput').value;
    const designationValue = document.getElementById('designationInput').value;

    console.log("клик был")

        // Подготовим объект tools с актуальными значениями из input'ов
    const toolsContainer = document.getElementById("selection_tools");
    const toolDivs = toolsContainer.querySelectorAll("div");
    const tools = [];

    toolDivs.forEach(div => {
        const nameDiv = div.querySelector(".toolName") || div.firstChild;
        const input = div.querySelector(".input_sum");

        if (nameDiv && input) {
          const toolName = nameDiv.textContent.trim();
          const toolCount = parseInt(input.value, 10) || 1;
          // tools[toolName] = toolCount.toString();
          tools.push({
            name: toolName,
            quantity: toolCount
          });
        }
    });

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
    let json_plan = window.jsonPlan;
    save_all_plans(device_number, json_plan)

    //Перенаправление на другую страницу:
    window.location.href='../screen_7_plans.html?token=' + localStorage.getItem('token');
  });


window.save_all_plans = save_all_plans;