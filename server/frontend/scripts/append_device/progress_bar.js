let isProcessing = false;

async function updateProgress() {
    const response = await fetch('/progress_search_device');
    const data = await response.json();

    // Update progress bar
    document.getElementById('progressFill').style.width = data.percentage + '%';
    document.getElementById('progressText').textContent =
        `${data.stage} (${data.percentage}%)`;

    // Если прогресс достиг 100%
    if (data.percentage >= 100) {
        show_progress_bar('none');

        // Проверка наличия устройств
        const devicesResponse = await fetch('/get_json_devices');
        const jsonDevices = await devicesResponse.json();

        if (!jsonDevices || jsonDevices.length === 0) {
            openModalNoDevicesFound();
        } else {
            createDevices('devices', jsonDevices);
        }
    }
}