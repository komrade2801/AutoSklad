import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice, QThread, pyqtSignal


class SerialThread(QThread):
    data_received = pyqtSignal(bytes)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial = QSerialPort()
        self.serial.readyRead.connect(self.read_data)
        self.serial.setPortName("COM3")  # Замените на нужный порт
        self.serial.setBaudRate(9600)
        self.serial.setDataBits(QSerialPort.Data8)
        self.serial.setParity(QSerialPort.NoParity)
        self.serial.setStopBits(QSerialPort.OneStop)
        if not self.serial.open(QIODevice.ReadWrite):
            print(f"Error opening serial port: {self.serial.errorString()}")

    def read_data(self):
        data = self.serial.readAll()
        print(f"Received data: {data.data().hex()}")
        if data:
            self.data_received.emit(data.data())
        else:
            print("No data received")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Port Monitor")
        self.setGeometry(100, 100, 400, 300)

        self.label = QLabel()
        self.label.setText("Тест")
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.serial_thread = SerialThread(self)
        self.serial_thread.data_received.connect(self.display_data)
        self.serial_thread.start()

    def display_data(self, data):
        if data:
            self.label.setText(data.decode())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())