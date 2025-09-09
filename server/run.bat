@echo off
REM — переходим в папку с проектом
cd /d "C:\Users\admin\Desktop\WEB"

REM — активируем виртуальное окружение
call .venv\Scripts\activate.bat

REM — запускаем скрипт
python main.py

REM — (опционально) чтобы окно не закрывалось сразу и вы видели ошибки
pause