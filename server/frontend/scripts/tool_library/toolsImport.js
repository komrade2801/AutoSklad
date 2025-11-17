function doImportTools() {
    const selectedFile = document.getElementById("importToolsFile").files[0];
    const useCount = document.getElementById("useToolCount").checked;
    const endpointUrl = "../backend/upload";
    const formData = new FormData();

    if (!selectedFile) {
        return;
    }

    formData.append("file", selectedFile);
    formData.append("use_count", useCount);

    fetch(endpointUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errData => {
                throw new Error('Ошибка сети: ' + JSON.stringify(errData));
            });
        }
        return response.json();
    })
    .then(result => {
        let url = '../screen_15_tool_library.html';
        let targetUrl = new URL(url, window.location.origin).href;
        let token = localStorage.getItem('token');
        let full_url = targetUrl + "?token=" + token;
        window.location.href = full_url;
    })
    .catch(error => {
        console.error('Ошибка при сохранении данных:', error);
        alert();
        // Обработка ошибок
    });
}

function changeTab(idToShow, idToHide) {
    elemToShow = $(idToShow);
    elemToHide = $(idToHide);
    elemToShow.show();
    elemToHide.hide();
}