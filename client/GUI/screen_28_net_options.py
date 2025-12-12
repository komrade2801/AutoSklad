import traceback
from GUI.BaseScreen import BaseScreen
from GUI.ui_classes.Ui_screen_28_net_options import Ui_screen_28_net_options
from PyQt5.QtCore import QEvent, QTimer, QThread, pyqtSignal
from PyQt5 import QtGui
import socket


class PingThread(QThread):
    """Поток для выполнения ping без блокировки GUI"""
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
    
    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.server_ip, self.server_port))
            sock.close()
            
            if result == 0:
                self.finished.emit(True, "Сервер доступен")
            else:
                self.finished.emit(False, "Сервер недоступен")
        except socket.gaierror:
            self.finished.emit(False, "Ошибка разрешения имени")
        except socket.timeout:
            self.finished.emit(False, "Таймаут соединения")
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}")


class screen_28_net_options(BaseScreen, Ui_screen_28_net_options):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.current_field_index = 0
        self.current_field_group = 'device'  # 'device', 'server', 'mask', 'dns', 'gate'
        self.ping_thread = None
        
        # Список полей для каждого типа адреса
        self.device_fields = [
            self.edit_IP_devise_1, self.edit_IP_devise_2,
            self.edit_IP_devise_3, self.edit_IP_devise_4
        ]
        self.server_fields = [
            self.edit_IP_server_1, self.edit_IP_server_2,
            self.edit_IP_server_3, self.edit_IP_server_4
        ]
        self.mask_fields = [
            self.edit_mask_1, self.edit_mask_2,
            self.edit_mask_3, self.edit_mask_4
        ]
        self.dns_fields = [
            self.edit_DNS_1, self.edit_DNS_2,
            self.edit_DNS_3, self.edit_DNS_4
        ]
        self.gate_fields = [
            self.edit_gate_1, self.edit_gate_2,
            self.edit_gate_3, self.edit_gate_4
        ]
        
        # Порядок групп полей: device -> server -> mask -> dns -> gate
        self.field_groups_order = ['device', 'server', 'mask', 'dns', 'gate']
        
        self._setup_ui_connections()
        self._load_current_settings()

    def _setup_ui_connections(self):
        """Подключение обработчиков для кнопок цифр и действий"""
        # Подключение цифровых кнопок
        for i in range(10):
            btn = getattr(self, f'btn_number_{i}', None)
            if btn:
                btn.clicked.connect(lambda checked, num=i: self._on_number_clicked(num))
        
        # Подключение кнопок действий
        self.btn_ping.clicked.connect(self._on_ping_clicked)
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        self.btn_return.clicked.connect(self._on_return_clicked)
        self.btn_next.clicked.connect(self._on_next_clicked)
        
        # Подключение обработчиков фокуса и изменения текста для полей
        for field in (self.device_fields + self.server_fields + 
                     self.mask_fields + self.dns_fields + self.gate_fields):
            field.installEventFilter(self)
            field.textChanged.connect(lambda text, f=field: self._on_field_text_changed(f, text))
            # Устанавливаем максимальную длину ввода (3 символа)
            field.setMaxLength(3)

    def eventFilter(self, obj, event):
        """Фильтр событий для отслеживания фокуса полей"""
        from PyQt5.QtCore import QEvent
        
        if event.type() == QEvent.FocusIn:
            # Очищаем поле при получении фокуса (начало нового ввода)
            obj.clear()
            
            # Определяем, к какой группе относится поле
            if obj in self.device_fields:
                self.current_field_group = 'device'
                self.current_field_index = self.device_fields.index(obj)
            elif obj in self.server_fields:
                self.current_field_group = 'server'
                self.current_field_index = self.server_fields.index(obj)
            elif obj in self.mask_fields:
                self.current_field_group = 'mask'
                self.current_field_index = self.mask_fields.index(obj)
            elif obj in self.gate_fields:
                self.current_field_group = 'gate'
                self.current_field_index = self.gate_fields.index(obj)
            elif obj in self.dns_fields:
                self.current_field_group = 'dns'
                self.current_field_index = self.dns_fields.index(obj)
        
        return super().eventFilter(obj, event)

    def _on_field_text_changed(self, field, text):
        """Обработка изменения текста в поле"""
        # Автоматический переход к следующему полю при заполнении (3 цифры)
        if len(text) >= 3:
            self._move_to_next_field()

    def _on_number_clicked(self, number):
        """Обработка нажатия цифровой кнопки"""
        # Получаем текущее активное поле
        current_field = self._get_current_field()
        if current_field:
            current_text = current_field.text()
            
            # Если поле уже заполнено (3 символа), сбрасываем и начинаем заново
            if len(current_text) >= 3:
                current_field.setText(str(number))
            else:
                # Добавляем цифру к текущему тексту
                current_field.setText(current_text + str(number))
            
            # Автоматический переход к следующему полю при заполнении
            if len(current_field.text()) == 3:
                self._move_to_next_field()

    def _get_current_field(self):
        """Получение текущего активного поля"""
        fields_map = {
            'device': self.device_fields,
            'server': self.server_fields,
            'mask': self.mask_fields,
            'dns': self.dns_fields,
            'gate': self.gate_fields
        }
        fields = fields_map.get(self.current_field_group, [])
        if 0 <= self.current_field_index < len(fields):
            return fields[self.current_field_index]
        return None

    def _move_to_next_field(self):
        """Переход к следующему полю в текущей группе"""
        fields_map = {
            'device': self.device_fields,
            'server': self.server_fields,
            'mask': self.mask_fields,
            'dns': self.dns_fields,
            'gate': self.gate_fields
        }
        fields = fields_map.get(self.current_field_group, [])
        
        if self.current_field_index < len(fields) - 1:
            self.current_field_index += 1
            fields[self.current_field_index].setFocus()
        else:
            # Если достигли конца группы, переходим к следующей группе
            self._move_to_next_group()

    def _move_to_next_group(self):
        """Переход к следующей группе полей"""
        try:
            current_idx = self.field_groups_order.index(self.current_field_group)
            if current_idx < len(self.field_groups_order) - 1:
                self.current_field_group = self.field_groups_order[current_idx + 1]
                self.current_field_index = 0
                next_field = self._get_current_field()
                if next_field:
                    next_field.setFocus()
        except (ValueError, AttributeError):
            pass
    
    def _move_to_previous_group(self):
        """Переход к предыдущей группе полей"""
        try:
            current_idx = self.field_groups_order.index(self.current_field_group)
            if current_idx > 0:
                self.current_field_group = self.field_groups_order[current_idx - 1]
                self.current_field_index = 3  # Последнее поле в предыдущей группе
                prev_field = self._get_current_field()
                if prev_field:
                    prev_field.setFocus()
        except (ValueError, AttributeError):
            pass
    
    def _move_to_previous_field(self):
        """Переход к предыдущему полю"""
        fields_map = {
            'device': self.device_fields,
            'server': self.server_fields,
            'mask': self.mask_fields,
            'dns': self.dns_fields,
            'gate': self.gate_fields
        }
        fields = fields_map.get(self.current_field_group, [])
        
        if self.current_field_index > 0:
            self.current_field_index -= 1
            fields[self.current_field_index].setFocus()
        else:
            # Если достигли начала группы, переходим к предыдущей группе
            self._move_to_previous_group()
    
    def _on_return_clicked(self):
        """Обработка нажатия кнопки Return (назад)"""
        self._move_to_previous_field()
    
    def _on_next_clicked(self):
        """Обработка нажатия кнопки Next (вперед)"""
        self._move_to_next_field()

    def _load_current_settings(self):
        """Загрузка текущих настроек из config.json"""
        try:
            from Cnf.Actions import CnfActions
            cnf = CnfActions()
            config = cnf.read_cnf(0)
            
            # Загрузка IP устройства (network.ip)
            device_ip = str(config.get('network', {}).get('ip', '127.0.0.1'))
            self._set_ip_fields(device_ip, *self.device_fields)
            
            # Загрузка IP сервера (server.ip)
            server_ip = str(config.get('server', {}).get('ip', '127.0.0.1'))
            self._set_ip_fields(server_ip, *self.server_fields)
            
            # Загрузка маски подсети
            network_config = config.get('network', {})
            subnet_mask = network_config.get('subnet_mask')
            if subnet_mask:
                self._set_ip_fields(str(subnet_mask), *self.mask_fields)
            else:
                self._set_ip_fields('255.255.255.0', *self.mask_fields)
            
            # Загрузка шлюза
            gateway = network_config.get('gateway')
            if gateway:
                self._set_ip_fields(str(gateway), *self.gate_fields)
            else:
                self._set_ip_fields('192.168.1.1', *self.gate_fields)
            
            # Загрузка DNS
            dns = network_config.get('dns')
            if dns:
                self._set_ip_fields(str(dns), *self.dns_fields)
            else:
                self._set_ip_fields('8.8.8.8', *self.dns_fields)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            traceback.print_exc()

    def _set_ip_fields(self, ip_str, *fields):
        """Установка IP адреса в поля ввода"""
        parts = ip_str.split('.')
        for i, field in enumerate(fields[:4]):
            if i < len(parts):
                field.setText(parts[i])
            else:
                field.setText('')

    def _get_ip_from_fields(self, *fields):
        """Получение IP адреса из полей ввода"""
        parts = [field.text() for field in fields if field.text()]
        if len(parts) == 4:
            return '.'.join(parts)
        return None

    def _on_ping_clicked(self):
        """Выполнение ping для проверки соединения"""
        server_ip = self._get_ip_from_fields(*self.server_fields)
        if not server_ip:
            self.lbl_status_text.setText("Ошибка: неверный IP")
            self.lbl_status_point.setPixmap(QtGui.QPixmap("ui\\img/Ping_red.png"))
            return
        
        # Обновление статуса
        self.lbl_status_point.setPixmap(QtGui.QPixmap("ui\\img/Ping_gray.png"))
        self.lbl_status_text.setText("Проверка...")
        self.btn_ping.setEnabled(False)
        
        # Получение порта сервера из конфигурации
        try:
            from Cnf.Actions import CnfActions
            cnf = CnfActions()
            config = cnf.read_cnf(0)
            server_port = int(config.get('server', {}).get('port', 8000))
        except:
            server_port = 8000
        
        # Запуск ping в отдельном потоке
        if self.ping_thread and self.ping_thread.isRunning():
            self.ping_thread.terminate()
            self.ping_thread.wait()
        
        self.ping_thread = PingThread(server_ip, server_port)
        self.ping_thread.finished.connect(self._on_ping_finished)
        self.ping_thread.start()

    def _on_ping_finished(self, success, message):
        """Обработка завершения ping"""
        self.btn_ping.setEnabled(True)
        self.lbl_status_text.setText(message)
        
        if success:
            self.lbl_status_point.setPixmap(QtGui.QPixmap("ui\\img/Ping_green.png"))
        else:
            self.lbl_status_point.setPixmap(QtGui.QPixmap("ui\\img/Ping_red.png"))

    def _on_ok_clicked(self):
        """Сохранение настроек через state machine"""
        # Валидация данных перед сохранением
        try:
            device_ip = self._get_ip_from_fields(*self.device_fields)
            if not device_ip:
                print("Ошибка: неверный IP адрес устройства")
                return {'trigger': 'error'}
            
            server_ip = self._get_ip_from_fields(*self.server_fields)
            if not server_ip:
                print("Ошибка: неверный IP адрес сервера")
                return {'trigger': 'error'}
            
            # Сохранение происходит через get_data() и state machine
            print("Настройки сети будут сохранены через state machine")
            return {'trigger': 'ok'}
        except Exception as e:
            print(f"Ошибка валидации настроек: {e}")
            traceback.print_exc()
            return {'trigger': 'error'}

    def set_data(self, *args, **kwargs):
        """Устанавливает данные при переходе на экран"""
        self._load_current_settings()
        # Сбрасываем позицию на начало при возврате на страницу
        # НЕ устанавливаем фокус, чтобы не стирать предзагруженные значения
        self.current_field_group = 'device'
        self.current_field_index = 0

    def get_data(self):
        """Возвращает данные с экрана для сохранения через state machine"""
        try:
            device_ip = self._get_ip_from_fields(*self.device_fields)
            server_ip = self._get_ip_from_fields(*self.server_fields)
            subnet_mask = self._get_ip_from_fields(*self.mask_fields)
            gateway = self._get_ip_from_fields(*self.gate_fields)
            dns = self._get_ip_from_fields(*self.dns_fields)
            
            # Возвращаем кортеж для распаковки в write_cnf_network(*args, **kwargs)
            # Формат: (device_ip, server_ip, subnet_mask, gateway, dns)
            return (device_ip, server_ip, subnet_mask, gateway, dns)
        except Exception as e:
            print(f"Ошибка получения данных: {e}")
            traceback.print_exc()
            return None
