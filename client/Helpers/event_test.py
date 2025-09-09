import sys
from PyQt5.QtWidgets import *


class Widget(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel()
        self.lineEdit = QLineEdit()
        self.lineEdit.textEdited.connect(self.my_slot_function)

        lay = QVBoxLayout(self)
        lay.addWidget(self.lineEdit)
        lay.addWidget(self.label)

    def my_slot_function(self, text):
        self.label.setText(f'Длина строки: {len(text)}')


#        print(len(self.lineEdit.text()))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())