export function createDevices(containerId, jsonDevices) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Контейнер с id "${containerId}" не найден.`);
    return;
  }

  // Очищаем контейнер перед добавлением новых элементов
  container.innerHTML = '';

  jsonDevices.devices.forEach((device, index) => {
    try {
      const details = JSON.parse(device.details);
      const serialNumber = details.signature.serial_number;

      const deviceDiv = document.createElement('div');
      deviceDiv.textContent = `Серийный номер: ${serialNumber}`;
      deviceDiv.style.cursor = 'pointer';
      deviceDiv.style.display = 'flex';
      deviceDiv.style.width = '100%';
      deviceDiv.style.height = '60px';
      deviceDiv.style.border = '1px solid #ffffff';
      deviceDiv.style.borderRadius = '5px';
      deviceDiv.style.backgroundColor = '#D3D3D3A0';
      deviceDiv.style.color = '#003172';
      deviceDiv.style.fontWeight = 'bold';
      deviceDiv.style.alignItems = 'center';
      deviceDiv.style.justifyContent = 'start';
      deviceDiv.style.marginTop = '1px';

      deviceDiv.addEventListener('click', () => {
        openModalSignature(device, serialNumber);
      });

      container.appendChild(deviceDiv);
    } catch (e) {
      console.error(`Ошибка при обработке устройства #${index + 1}:`, e);
    }
  });
}
