import sys
import serial
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget


class SerialThread(QThread):
    data_received = pyqtSignal(str)  # Сигнал для передачи данных в главный поток

    def __init__(self, port, baudrate):
        super().__init__()
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self.running = True

    def run(self):
        while self.running:
            if self.serial.in_waiting > 0:
                data = self.serial.readline().decode('utf-8').strip()
                self.data_received.emit(data)  # Отправка данных через сигнал

    def stop(self):
        self.running = False
        self.serial.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("COM Port Reader")
        self.resize(400, 300)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.start_button = QPushButton("Start", self)
        self.stop_button = QPushButton("Stop", self)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.serial_thread = None

        self.start_button.clicked.connect(self.start_serial)
        self.stop_button.clicked.connect(self.stop_serial)

    def start_serial(self):
        # Укажите порт и скорость передачи данных
        port = "COM1"  # Замените на ваш порт
        baudrate = 9600
        self.serial_thread = SerialThread(port, baudrate)
        self.serial_thread.data_received.connect(self.update_text)
        self.serial_thread.start()

    def stop_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None

    def update_text(self, data):
        self.text_edit.append(f"Received: {data}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
