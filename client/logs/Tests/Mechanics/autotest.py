import sys
import time
import threading
from PyQt5.QtCore import QCoreApplication

from BarcodeScanner.serial_manager import SerialManager
from Core.platforms import detect


class TestMechanics:
    def __init__(self, port="COM30"):
        self.manager = SerialManager(port=port, baudrate=9600, timeout=1)
        # Подключаем сигнал, который посылает SerialManager при получении ответа
        self.manager.signal_received.connect(self.handle_response)

        self.log = []  # Лог результатов тестов
        self.test_cells = list(range(1, 217))  # Ячейки от 1 до 216
        self.current_cell = None
        self.responses = []  # Список для накопления двух ответов для текущей ячейки
        self.response_event = threading.Event()

    def handle_response(self, response):
        """
        Обработчик сигнала, который вызывается при получении ответа от устройства.
        В нашем случае система выдаёт два сообщения: одно с кодом 1 (принято)
        и другое с кодом 2 (исполнено). Мы просто добавляем ответ в список.
        """
        self.responses.append(response)
        print(f"Ячейка {self.current_cell}: получен ответ -> {response}")
        self.log.append(f"Ячейка {self.current_cell}: {response}")
        # Если получили два ответа, сигнализируем о завершении ожидания для этой ячейки
        if len(self.responses) >= 2:
            self.response_event.set()

    def run_tests(self):
        """Последовательно проходит по ячейкам от 1 до 216, отправляет команды и логгирует ответы."""
        self.manager.start()  # Запускаем поток SerialManager
        try:
            for cell in self.test_cells:
                self.current_cell = cell
                self.responses = []
                # Отправляем команду (команда формируется внутри SerialManager)
                command = f"send:{cell}"
                print(f"\nОтправка команды для ячейки {cell}")
                self.manager.command_queue.put(command)
                # Ждем до 50 секунд для получения двух ответов
                self.response_event.clear()
                if self.response_event.wait(timeout=50):
                    print(f"Ячейка {cell}: получены оба ответа")
                else:
                    timeout_msg = f"Ячейка {cell}: не получены оба ответа, получено: {self.responses}"
                    print(timeout_msg)
                    self.log.append(timeout_msg)
                time.sleep(1)  # Небольшая задержка между тестами
        finally:
            self.manager.stop()
            self.manager.join()
            print("\nТестирование завершено. Лог результатов:")
            for entry in self.log:
                print(entry)


if __name__ == '__main__':
    current_platform = detect()

    # Создаем QCoreApplication для корректной работы сигналов PyQt
    app = QCoreApplication(sys.argv)
    tester = None
    if current_platform == 'Windows':
        tester = TestMechanics(port="COM29")
    else:
        tester = TestMechanics(port="/dev/ttyUSB0")
    # Запускаем тесты в отдельном потоке, чтобы не блокировать цикл событий Qt
    test_thread = threading.Thread(target=tester.run_tests)
    test_thread.start()
    sys.exit(app.exec_())
