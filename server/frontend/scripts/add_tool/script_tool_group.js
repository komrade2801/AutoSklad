import { jsonToolLibrary } from '../../JSONs/tool_library.js';

const searchInput = document.getElementById("search");
const suggestionsBox = document.getElementById("suggestions");

searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    // Получаем все имена групп из jsonToolLibrary
    const groupNames = Object.values(jsonToolLibrary.groups).map(group => group.name);
    // Фильтруем по запросу
    const filtered = groupNames.filter(name => name.toLowerCase().includes(query));

    if (filtered.length > 0 && query) {
        suggestionsBox.innerHTML = filtered.map(item => `<div>${item}</div>`).join("");
        suggestionsBox.style.display = "block";
    } else {
        suggestionsBox.style.display = "none";
    }
});

suggestionsBox.addEventListener("click", (event) => {
    if (event.target.tagName === "DIV") {
        searchInput.value = event.target.textContent;
        suggestionsBox.style.display = "none";
    }
});

document.querySelector(".search-icon").addEventListener("click", () => {
    const query = searchInput.value.toLowerCase();
    const groupNames = Object.values(jsonToolLibrary.groups).map(group => group.name);
    const results = groupNames.filter(name => name.toLowerCase().includes(query));
    alert("Results: " + results.join(", "));
});

document.addEventListener("click", (event) => {
    if (!event.target.closest(".search-container")) {
        suggestionsBox.style.display = "none";
    }
});