export function createTableRandomLoad(data, containerId) {
        let table = '<table style="width: 100%; border-style: solid;">';
        table += '<tr><th>Ячейка</th><th>Инструмент</th><th>Группа</th><th>Чертёж</th></tr>';

        // Сортировка по номеру ячейки
        const sortedKeys = Object.keys(data.operation).sort((a, b) => a - b);

        sortedKeys.forEach(key => {
            const { cell, tool, plan, group } = data.operation[key];
            table += `<tr>
                        <td>${cell}</td>
                        <td>${tool}</td>
                        <td>${group}</td>
                        <td>${plan}</td>
                      </tr>`;
        });

        table += '</table>';

        // Вставка в указанный контейнер
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = table;
        } else {
            console.error(`Контейнер с id "${containerId}" не найден.`);
        }
    }