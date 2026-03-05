Host = "127.0.0.1"
port = 8000
FullScreen = False
db_path = "web_vending.db"
db_path_work = "vending.db"
db_path_test = ":memory:"
SECRET_KEY = "g\xa8\xc9\x04H\xf0F\xe1\xfb\xb6J\xbc\xae\xfaP\xec'\x08\xcb\xa1\xfc\xbe\xea\x96'"
BASE_URL = f"http://{Host}"
SENDER_TIMEOUT = 15
RECEIVER_TIMEOUT = 30
# Таймаут HTTP для push-запросов (отправка команд на сервер); увеличен для больших батчей
PUSH_HTTP_TIMEOUT = 120
# Таймаут запроса импорта Excel (секунды); на клиенте рекомендуется такой же (например 600 = 10 мин)
UPLOAD_REQUEST_TIMEOUT_SEC = 600
AES_KEY = b"16byteslongkey!!"

# ------------------------------MySQL-----------------------------
# Конфигурация базы данных
DB_HOST = "127.0.0.1"  # Адрес сервера MySQL
DB_PORT = 3306  # Порт MySQL (по умолчанию 3306)
DB_NAME = "vending"  # Имя базы данных
DB_USER = "root"  # Имя пользователя базы данных
DB_PASSWORD = "Fury1488!"  # Пароль пользователя базы данных
# -----------------------------------------------------------------
