jsonData = {
	"rows":
	{
		"1": {
			"cells":
			{
				"1": {
					"id": "1",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content":
					{
						"tool": "Молоток",
						"plan": "хххх.DDDDDD.DD СБ"
					}
				},
				"2": {
					"id":"2",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Гвоздь",
						"plan": "хххх.DDDDDD.DD СБ"
					}
				},
				"3": {
					"id":"3",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Сверло",
						"plan": "None"
					}
				},
				"4": {
					"id":"4",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Ключ",
						"plan": "хххх.DDDDDD.DD СБ"
					}
				}
			}
		},
		"2": {
			"cells":
			{
				"1": {
					"number":"5",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Зубило",
						"plan": "None"
					}
				},
				"2": {
					"number":"6",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Мечик",
						"plan": "хххх.DDDDDD.DD СБ"
					}
				},
				"3": {
					"number": "7",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Долото",
						"plan": "хххх.DDDDDD.DD СБ"
					}
				},
				"4": {
					"number": "8",
					"type": "small",
					"backgroundColor": "RGB(204, 204, 204)",
					"content": {
						"tool": "Наковальня",
						"plan": "None"
					}
				}
			}
		},
		"3": {
			"cells":
			{
				"1": {
					"number":"9",
					"type": "big",
					"backgroundColor": "RGB(153, 153, 153)",
					"content": {
						"tool": "None",
						"plan": "None"
					}
				},
				"2": {
					"number": "10",
					"type": "big",
					"backgroundColor": "RGB(153, 153, 153)",
					"content": {
						"tool": "None",
						"plan": "None"
					}
				},
				"3": {
					"number": "11",
					"type": "big",
					"backgroundColor": "RGB(153, 153, 153)",
					"content": {
						"tool": "None",
						"plan": "None"
					}
				},
				"4": {
					"number": "12",
					"type": "big",
					"backgroundColor": "RGB(153, 153, 153)",
					"content": {
						"tool": "None",
						"plan": "None"
					}
				}
			}
		}
	}
};
/*function generateJsonCells(rowsCount, cellsCount) {
      const jsonObject = { rows: {} };

      for (let row = 1; row <= rowsCount; row++) {
        jsonObject.rows[row] = { cells: {} };

        for (let cell = 1; cell <= cellsCount; cell++) {
          jsonObject.rows[row].cells[cell] = {
            number: (row - 1) * cellsCount + cell, // Уникальный номер в зависимости от строки и ячейки
            type: "big", // Или "small", в зависимости от требований
            backgroundColor: '#696969', // Общий цвет
            content: {
              tool: "None",
              plan: "None"
            }
          };
        }
      }

      return jsonObject; //JSON.stringify(, null, 2) Форматированное представление
    }

    // Функция для создания ячеек на основе JSON-данных
    function createCells(containerId, jsonObject) {
        const container = document.getElementById(containerId);
        container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек

        // Проходим по строкам в JSON
        for (const rowKey in jsonObject.rows) {
            const rowData = jsonObject.rows[rowKey];
            const rowDiv = document.createElement('div');
            rowDiv.style.display = 'flex'; // Устанавливаем флекс-контейнер для строки

            // Проходим по ячейкам в строке
            for (const cellKey in rowData.cells) {
                const cellData = rowData.cells[cellKey];
                const cellDiv = document.createElement('div');

                // Устанавливаем класс и уникальный ID для ячейки
                cellDiv.className = 'droppable';
                cellDiv.id = `cell${cellData.number}`;

                // Устанавливаем стили для ячейки
                cellDiv.style.display = 'flex'; // Включает Flexbox
                cellDiv.style.width = '44px';
                cellDiv.style.height = cellData.type === 'big' ? '70px' : '50px';
                cellDiv.style.border = '1px solid #FFFFFF';
                cellDiv.style.backgroundColor = cellData.backgroundColor;
                cellDiv.style.alignItems = 'center';
                cellDiv.style.justifyContent = 'center';
                cellDiv.style.margin = '1px';

                // Добавляем текстовое содержимое (номер ячейки)
                cellDiv.textContent = cellData.number;

                // Добавляем всплывающую подсказку с информацией о содержимом
                cellDiv.title = `Инструмент: ${cellData.content.tool}\nПлан: ${cellData.content.plan}`;

                 rowDiv.appendChild(cellDiv); // Добавляем ячейку в строку
            }

            container.appendChild(rowDiv); // Добавляем строку в контейнер
        }
    }*/