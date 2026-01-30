import traceback
from Core.app_logging import get_logger
from GUI.BaseScreen import BaseScreen

logger = get_logger(__name__)
from GUI.ui_classes.Ui_screen_29_serial_options import Ui_screen_29_serial_options
from PyQt5.QtCore import QEvent, QThread, pyqtSignal
from PyQt5 import QtGui
import serial
import serial.tools.list_ports
from GUI.ico.btn_ico_insert import Insert


class SerialTestThread(QThread):
    """Поток для тестирования последовательного порта без блокировки GUI"""
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, port, baudrate, parity, data_bits, stop_bits):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.data_bits = data_bits
        self.stop_bits = stop_bits
    
    def run(self):
        try:
            # Преобразование параметров в формат pyserial
            parity_map = {'NONE': 'N', 'EVEN': 'E', 'ODD': 'O', 'MARK': 'M', 'SPACE': 'S'}
            stop_bits_map = {'1': serial.STOPBITS_ONE, '1.5': serial.STOPBITS_ONE_POINT_FIVE, '2': serial.STOPBITS_TWO}
            
            parity_char = parity_map.get(self.parity.upper(), 'N')
            stop_bits_val = stop_bits_map.get(str(self.stop_bits), serial.STOPBITS_ONE)
            data_bits_val = int(self.data_bits)
            
            # Попытка открыть порт
            ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=data_bits_val,
                parity=parity_char,
                stopbits=stop_bits_val,
                timeout=1
            )
            ser.close()
            
            self.finished.emit(True, "Порт доступен")
        except serial.SerialException as e:
            self.finished.emit(False, f"Порт недоступен: {str(e)}")
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}")


class screen_29_serial_options(BaseScreen, Ui_screen_29_serial_options):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.test_thread_reader = None
        self.test_thread_driver = None
        
        self._populate_comboboxes()
        self._setup_ui_connections()
        self._load_current_settings()

    def _populate_comboboxes(self):
        """Заполнение выпадающих списков значениями"""
        # Скорость порта
        speeds = ['9600', '19200', '38400', '57600', '115200']
        self.cmb_speed_reader.addItems(speeds)
        self.cmb_speed_driver.addItems(speeds)
        
        # Чётность
        parities = ['NONE', 'EVEN', 'ODD']
        self.cmb_parity_reader.addItems(parities)
        self.cmb_parity_driver.addItems(parities)
        
        # Биты данных
        data_bits = ['5', '6', '7', '8']
        self.cmb_data_bits_reader.addItems(data_bits)
        self.cmb_data_bits_driver.addItems(data_bits)
        
        # Стоп-биты
        stop_bits = ['1', '1.5', '2']
        self.cmb_stop_bits_reader.addItems(stop_bits)
        self.cmb_stop_bits_driver.addItems(stop_bits)
        
        # Заполнение списка доступных портов
        self._populate_ports()

    def _populate_ports(self):
        """Заполнение списка доступных последовательных портов"""
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            # Для Windows: COM1, COM2... Для Linux: /dev/ttyUSB0, /dev/ttyACM0...
            if ports:
                # Устанавливаем первый доступный порт, если поле пустое
                if not self.edit_port_reader.text():
                    self.edit_port_reader.setText(ports[0] if ports else '')
                if not self.edit_port_driver.text():
                    self.edit_port_driver.setText(ports[1] if len(ports) > 1 else ports[0] if ports else '')
        except Exception as e:
            logger.exception("Ошибка получения списка портов: %s", e)
    
    def _setup_insert_icon(self):
        """Установка SVG иконки для кнопки Insert"""
        try:
            icon = Insert()
            pixmap = icon.get_pixmap(51, 51)  # Размеры для иконки кнопки (как в UI)
            icon_obj = QtGui.QIcon()
            icon_obj.addPixmap(pixmap, QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.btn_insert.setIcon(icon_obj)
        except Exception as e:
            logger.exception("Ошибка установки иконки Insert: %s", e)

    def _setup_ui_connections(self):
        """Подключение обработчиков событий"""
        self.btn_test.clicked.connect(self._on_test_clicked)
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        self.btn_insert.clicked.connect(self._on_insert_clicked)
        self.btn_keyboard.clicked.connect(self._on_keyboard_clicked)
        
        # Установка SVG иконки для кнопки Insert
        self._setup_insert_icon()

    def _load_current_settings(self):
        """Загрузка текущих настроек из config.json"""
        try:
            from Cnf.Actions import CnfActions
            cnf = CnfActions()
            
            # Загрузка настроек считывателя (barcode)
            barcode_config = cnf.read_cnf_barcode(0)
            self.edit_port_reader.setText(barcode_config.get('port', 'COM1'))
            self.cmb_speed_reader.setCurrentText(str(barcode_config.get('baudrate', 9600)))
            # Устанавливаем значения по умолчанию для остальных параметров
            self.cmb_parity_reader.setCurrentText('NONE')
            self.cmb_data_bits_reader.setCurrentText('8')
            self.cmb_stop_bits_reader.setCurrentText('1')
            
            # Загрузка настроек драйвера (serial)
            serial_config = cnf.read_cnf_serial(0)
            self.edit_port_driver.setText(serial_config.get('port', 'COM29'))
            self.cmb_speed_driver.setCurrentText(str(serial_config.get('baudrate', 9600)))
            # Устанавливаем значения по умолчанию для остальных параметров
            self.cmb_parity_driver.setCurrentText('NONE')
            self.cmb_data_bits_driver.setCurrentText('8')
            self.cmb_stop_bits_driver.setCurrentText('1')
        except Exception as e:
            logger.exception("Ошибка загрузки настроек: %s", e)

    def _on_test_clicked(self):
        """Тестирование порта драйвера"""
        port = self.edit_port_driver.text()
        if not port:
            self.lbl_status_point_driver.setPixmap(QtGui.QPixmap("ui\\img/Ping_red.png"))
            self.lbl_info_15.setText("Ошибка: порт не указан")
            return
        
        try:
            baudrate = int(self.cmb_speed_driver.currentText())
            parity = self.cmb_parity_driver.currentText()
            data_bits = self.cmb_data_bits_driver.currentText()
            stop_bits = self.cmb_stop_bits_driver.currentText()
        except ValueError:
            self.lbl_status_point_driver.setPixmap(QtGui.QPixmap("ui\\img/Ping_red.png"))
            self.lbl_info_15.setText("Ошибка: неверные параметры")
            return
        
        # Обновление статуса
        self.lbl_status_point_driver.setPixmap(QtGui.QPixmap("ui\\img/Ping_gray.png"))
        self.lbl_info_15.setText("Проверка...")
        self.btn_test.setEnabled(False)
        
        # Запуск теста в отдельном потоке
        if self.test_thread_driver and self.test_thread_driver.isRunning():
            self.test_thread_driver.terminate()
            self.test_thread_driver.wait()
        
        self.test_thread_driver = SerialTestThread(port, baudrate, parity, data_bits, stop_bits)
        self.test_thread_driver.finished.connect(self._on_test_driver_finished)
        self.test_thread_driver.start()

    def _on_test_driver_finished(self, success, message):
        """Обработка завершения теста порта драйвера"""
        self.btn_test.setEnabled(True)
        self.lbl_info_15.setText(message)
        
        if success:
            self.lbl_status_point_driver.setPixmap(QtGui.QPixmap("ui\\img/Ping_green.png"))
        else:
            self.lbl_status_point_driver.setPixmap(QtGui.QPixmap("ui\\img/Ping_red.png"))

    def _on_ok_clicked(self):
        """Сохранение настроек через state machine"""
        # Валидация данных перед сохранением
        try:
            port_driver = self.edit_port_driver.text()
            if not port_driver:
                logger.warning("Ошибка: порт драйвера не указан")
                return {'trigger': 'error'}
            
            port_reader = self.edit_port_reader.text()
            if not port_reader:
                logger.warning("Ошибка: порт считывателя не указан")
                return {'trigger': 'error'}
            
            # Проверка корректности baudrate
            int(self.cmb_speed_driver.currentText())
            int(self.cmb_speed_reader.currentText())
            
            # Сохранение происходит через get_data() и state machine
            logger.debug("Настройки COM портов будут сохранены через state machine")
            return {'trigger': 'ok'}
        except ValueError as e:
            logger.warning("Ошибка: неверные параметры - %s", e)
            return {'trigger': 'error'}
        except Exception as e:
            logger.exception("Ошибка валидации настроек: %s", e)
            return {'trigger': 'error'}

    def _on_insert_clicked(self):
        """Обработка кнопки вставки (пока не реализовано)"""
        pass

    def _on_keyboard_clicked(self):
        """Обработка кнопки клавиатуры (пока не реализовано)"""
        pass

    def set_data(self, *args, **kwargs):
        """Устанавливает данные при переходе на экран"""
        self._load_current_settings()
        self._populate_ports()

    def get_data(self):
        """Возвращает данные с экрана для сохранения"""
        # write_cnf_serial ожидает port и baudrate как позиционные аргументы
        # Executor передает результат get_data() в action
        try:
            port_driver = self.edit_port_driver.text()
            if not port_driver:
                logger.warning("Ошибка: порт драйвера не указан")
                return None
            
            baudrate_driver = int(self.cmb_speed_driver.currentText())
            
            # Сохраняем настройки считывателя (barcode) отдельно, так как это другой action
            from Cnf.Actions import CnfActions
            cnf = CnfActions()
            port_reader = self.edit_port_reader.text()
            if not port_reader:
                logger.warning("Ошибка: порт считывателя не указан")
                return None
            
            baudrate_reader = int(self.cmb_speed_reader.currentText())
            cnf.write_cnf_barcode(port_reader, baudrate_reader)
            
            # Возвращаем кортеж для распаковки в write_cnf_serial(*args)
            return (port_driver, baudrate_driver)
        except ValueError as e:
            logger.exception("Ошибка: неверные параметры - %s", e)
            return None
        except Exception as e:
            logger.exception("Ошибка получения данных: %s", e)
            return None
