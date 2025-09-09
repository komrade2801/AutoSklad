// Функция для создания строк инструмента на основе JSON-данных
    export function createToolForDrop(containerId, jsonToolsDrop) {
        const container = document.getElementById(containerId);
        container.innerHTML = ''; // Очищаем контейнер перед добавлением ячеек

            const allTools = [];

            // Собираем все инструменты в один массив
            for (const planKey in jsonToolsDrop.plans) {
                const planData = jsonToolsDrop.plans[planKey];
                for (const groupKey in planData.groups) {
                    const groupData = planData.groups[groupKey];

                    for (const valueData of groupData.value) {
                        allTools.push({
                            plan: planData.name,
                            group: groupData.name,
                            tools: valueData.tools,
                            cell: valueData.cell
                        });
                    }
                }
            }

            // Сортируем инструменты по номеру ячейки перед выводом
            allTools.sort((a, b) => a.cell - b.cell);

            // Проходим по ячейкам в строке
            for (const tool of allTools) {
                //const valueData = groupData.value[valueKey];

                const toolDiv = document.createElement('div');

                // Устанавливаем флекс-контейнер для строки и класс
                toolDiv.style.display = 'flex';
                toolDiv.style.flexDirection = 'row';
                toolDiv.style.flexWrap = 'nowrap';
                //toolDiv.className = 'draggable';
                //toolDiv.draggable = "true";
                toolDiv.style.width = '100%';
                //toolDiv.style.cursor = 'pointer';
                //toolDiv.setAttribute('data-plans-index', planKey);
                toolDiv.setAttribute('data-group-index', tool.group);
                //toolDiv.setAttribute('data-value-index', valueKey);
                //toolDiv.setAttribute('data-plan-name', planData.name);
                toolDiv.style.height = '32px';
                toolDiv.style.alignItems = 'center';


                //Создаем название, номер ячейки, номер чертежа и кнопку "выгрузить"
                const nameDiv = document.createElement('div');
                const cellDiv = document.createElement('div');
                const planDiv = document.createElement('div');
                const dropButton = document.createElement('button');


                // Устанавливаем стили для названия инструмента
                nameDiv.className = 'toolName';
                nameDiv.textContent = tool.tools;
                nameDiv.style.display = 'flex';
                nameDiv.style.width = '100%';
                nameDiv.style.height = '30px';
                nameDiv.style.backgroundColor = '#D3D3D3A0';
                nameDiv.style.border = '1px solid #ffffff';
                nameDiv.style.color = '#003172';
                nameDiv.style.fontWeight = 'bold';
                nameDiv.style.fontSize = '14px';
                nameDiv.style.alignItems = 'center';
                nameDiv.style.justifyContent = 'start';
                nameDiv.style.margin = '1px';

                // Добавляем всплывающую подсказку с полным наименованием инструмента
                //nameDiv.title = `Инструмент: ${cellData.content.tool}\nЧертёж: ${cellData.content.plan}`;

                // Устанавливаем стили для номера ячейки
                cellDiv.textContent = tool.cell;
                //cellDiv.className = 'sumTool';
                cellDiv.style.display = 'flex';
                cellDiv.style.width = '52px';
                cellDiv.style.height = '30px';
                cellDiv.style.marginRight = '1px';
                cellDiv.style.border = '1px solid #FFFFFF';
                cellDiv.style.backgroundColor = '#56b358';
                cellDiv.style.alignItems = 'center';
                cellDiv.style.justifyContent = 'center';


                //Устанавливаем стили для чертежа
                planDiv.style.display = 'flex';
                planDiv.style.width = '30px';
                planDiv.style.height = '30px';
                planDiv.style.marginRight = '1px';
                planDiv.style.border = '1px solid #FFFFFF';
                planDiv.style.backgroundColor = '#56b358';
                planDiv.style.alignItems = 'center';
                planDiv.style.justifyContent = 'center';

                //Добавляем изображение иконки чертежа
                const planImage = document.createElement('img');
                planImage.src = '../assets/img/btn_info.png';
                planImage.style.width = '20px';
                planImage.style.height = '20px';
                planImage.style.objectFit = 'contain'; // Сохраняем пропорции
                planDiv.appendChild(planImage);

                //Добавляем всплывающую подсказку
                planDiv.setAttribute('data-tooltipPlan', `Чертёж: ${tool.plan}`);


                //Устанавливаем стили для кнопки выгрузки
                dropButton.style.width = '30px';
                dropButton.style.height = '30px';
                dropButton.style.marginRight = '1px';
                dropButton.style.border = '1px solid #FFFFFF';
                dropButton.style.backgroundColor = '#56b358';
                dropButton.style.display = 'flex';
                dropButton.style.alignItems = 'center';
                dropButton.style.justifyContent = 'center';

                //Добавляем иконку на кнопку
                const dropIcon = document.createElement('img');
                dropIcon.src = '../assets/img/drop.png';
                dropIcon.style.width = '20px'; // Размер иконки
                dropIcon.style.height = '20px';
                dropIcon.style.pointerEvents = 'none'; // Отключаем обработку кликов на изображении
                dropButton.appendChild(dropIcon);

                // Добавляем название и количество в строку инструмента
                toolDiv.appendChild(nameDiv);
                toolDiv.appendChild(cellDiv);
                toolDiv.appendChild(planDiv);
                toolDiv.appendChild(dropButton);

                container.appendChild(toolDiv); // Добавляем строку в контейнер
            }
        }


