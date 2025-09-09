import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import sys

app = QApplication(sys.argv)

web = QWebEngineView()

# Получаем абсолютный путь к index.html относительно файла main.py
script_dir = os.path.dirname(os.path.abspath(__file__))  # папка, где лежит main.py
file_path = os.path.join(script_dir, "index.html")

web.load(QUrl.fromLocalFile(file_path))

web.show()
sys.exit(app.exec_())
