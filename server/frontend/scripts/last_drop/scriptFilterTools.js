import { jsonObjectTools } from './init.js';

document.addEventListener("DOMContentLoaded", () => {

  const toolsGroupDropdown = document.querySelector("#tools-group .dropdown-menu");
  const numberPlanDropdown = document.querySelector("#number-plan .dropdown-menu");
  const toolsContainer = document.getElementById("tools-container");

  const toolsGroupButton = document.querySelector("#tools-group .btn_vending");
  const numberPlanButton = document.querySelector("#number-plan .btn_vending");

  let selectedPlan = null;
  let selectedGroup = null;

  // Генерация списка "Группа инструмента" (groups.name, где plans.name = "None")
  const nonePlan = Object.values(jsonObjectTools.plans).find(plan => plan.name === "None");
  if (nonePlan) {
    Object.values(nonePlan.groups).forEach(group => {
      const groupItem = document.createElement("a");
      groupItem.className = "dropdown-item";
      groupItem.textContent = group.name;
      groupItem.addEventListener("click", () => {
        toolsGroupButton.textContent = group.name; // Меняем текст кнопки
      });
      toolsGroupDropdown.appendChild(groupItem);
    });
  }

  // Генерация списка "Номер чертежа" (plans.name, кроме "None")
  Object.values(jsonObjectTools.plans).forEach(plan => {
    if (plan.name !== "None") {
      const planItem = document.createElement("a");
      planItem.className = "dropdown-item";
      planItem.textContent = plan.name;
      planItem.addEventListener("click", () => {
        numberPlanButton.textContent = plan.name; // Меняем текст кнопки
      });
      numberPlanDropdown.appendChild(planItem);
    }
  });

  // Добавляем начальное состояние и логику выбора для "Свободный" / "По чертежу"
  const currentPlanDiv = document.querySelector("#plan-or-free .btn_vending");
  const dropdownItems = document.querySelectorAll("#plan-or-free .dropdown-item");
  const toolsGroupDiv = document.getElementById("tools-group");
  const numberPlanDiv = document.getElementById("number-plan");

  currentPlanDiv.textContent = "Свободный";
  toolsGroupDiv.style.display = "flex";
  numberPlanDiv.style.display = "none";

  //const dropdownItems = document.querySelectorAll("#plan-or-free .dropdown-item");
  dropdownItems.forEach(item => {
    item.addEventListener("click", (event) => {
      const selectedText = event.target.textContent;
      currentPlanDiv.textContent = selectedText;

      if (selectedText === "Свободный") {
        toolsGroupDiv.style.display = "flex";
        numberPlanDiv.style.display = "none";
      } else if (selectedText === "По чертежу") {
        toolsGroupDiv.style.display = "none";
        numberPlanDiv.style.display = "flex";
      }
    });
  });
});
