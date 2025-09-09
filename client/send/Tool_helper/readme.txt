Приложение предназначено для запуска на Raspberry Pi model 4b
Образ для работы максимальный, наименование Raspberry Pi OS Full(64bit)
Установка необходимых библиотек для работы осуществляется следующим образом:
sudo apt-get update
sudo apt-get install python3-pip
pip3 install --break-system-packages pydantic
pip3 install --break-system-packages transitions
pip3 install --break-system-packages sqlalchemy

