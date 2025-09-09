from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit
from PyQt5.QtCore import Qt

class MyLineEdit(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        print("QLineEdit received focus")

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        print("QLineEdit lost focus")

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QLineEdit Focus Events")

        layout = QVBoxLayout()
        self.line_edit = MyLineEdit()
        self.line_edit1 = MyLineEdit()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.line_edit1)
        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication([])
    window = MyWindow()
    window.show()
    app.exec_()