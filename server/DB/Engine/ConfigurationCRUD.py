import json
from sqlalchemy.orm import Session
from DB.Engine.CRUD import BaseCRUD
from DB.Models.Device import Device


class EngineConfiguration(BaseCRUD):
    """
    Класс EngineConfiguration предоставляет CRUD-операции для управления конфигурацией устройства.
    Конфигурация хранится в поле details таблицы Device в виде JSON-строки.

    Методы:
      - get_configuration: получает конфигурацию для указанного устройства.
      - update_configuration: обновляет конфигурацию устройства, сериализуя словарь в JSON.
      - add_configuration: устанавливает конфигурацию для устройства (если устройство существует).
      - delete_configuration: очищает поле details, что трактуется как удаление конфигурации.
    """

    def __init__(self, session: Session=None):       
        """
        
        :param session: 
        """
        
        super().__init__(session=session, model=Device)

    def get_configuration(self, device_id: int):
        """
        Получает конфигурацию устройства по его ID.
        :param device_id: Уникальный идентификатор устройства.
        :return: Словарь с конфигурацией или None, если устройство не найдено.
        """
        device = self.get(device_id)
        if not device:
            return None
        try:
            config = json.loads(device.details) if device.details else {}
        except Exception:
            config = {}
        return config

    def update_configuration(self, device_id: int, signature: dict) -> bool:
        """
        Обновляет конфигурацию устройства.
        Сериализует переданный словарь signature в JSON и сохраняет в поле details.
        :param device_id: Уникальный идентификатор устройства.
        :param signature: Словарь с конфигурационными данными.
        :return: True, если обновление прошло успешно, иначе False.
        """
        device = self.get(device_id)
        if not device:
            return False
        device.details = json.dumps(signature)
        # Обновляем поле details через базовый метод update
        return self.update(device_id, details=device.details)

    def add_configuration(self, device_id: int, configuration: dict) -> bool:
        """
        Добавляет (устанавливает) конфигурацию для устройства.
        Если устройство существует, то в поле details записывается сериализованная конфигурация.
        :param device_id: Уникальный идентификатор устройства.
        :param configuration: Словарь с конфигурационными данными.
        :return: True, если операция успешна, иначе False.
        """
        device = self.get(device_id)
        if not device:
            return False
        device.details = json.dumps(configuration)
        return self.update(device_id, details=device.details)

    def delete_configuration(self, device_id: int) -> bool:
        """
        Удаляет конфигурацию устройства, устанавливая пустую строку в поле details.
        :param device_id: Уникальный идентификатор устройства.
        :return: True, если удаление прошло успешно, иначе False.
        """
        device = self.get(device_id)
        if not device:
            return False
        device.details = ""
        return self.update(device_id, details=device.details)
