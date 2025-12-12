from options import Host, RECEIVER_TIMEOUT, SENDER_TIMEOUT, AES_KEY, port
from fastapi import Request  # , HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi import FastAPI
from dbSync.Runner import start_sync, stop_sync
from DB.Engine.DeviceCRUD import EngineDevice
from typing import List
from contextlib import asynccontextmanager
import mimetypes
import json
import importlib
from DB.Data.init_db import initialize_database_if_needed
import dbSync
import faulthandler
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 1) Сразу убеждаемся, что БД создана (init_db сам перезапустит программу, если файла пока нет)
faulthandler.enable(all_threads=True, file=open("crash.log", "w"))


dbSync.init_db = True
initialize_database_if_needed()
dbSync.init_db = False

# 2) Инициализируем кэш настроек после создания БД
try:
    from DB.Engine.SettingsCRUD import EngineSettings
    settings_crud = EngineSettings()
    settings_crud.load_all_to_cache()
    print("[INFO] Settings cache initialized successfully")
except Exception as e:
    # Если таблица Settings еще не создана или произошла ошибка, продолжаем работу
    print(f"[WARN] Failed to initialize settings cache: {e}")
    print("[INFO] Continuing with default settings from options.py")

# Import routers only AFTER DB is initialized to avoid early SQL queries
front_router = importlib.import_module("frontend.front_router").front_router
backend_router = importlib.import_module("API.backend.routers").backend_router
sync_router = importlib.import_module("dbSync.Transport.routers").sync_router

# from threading import Thread Dict,
# from DB.Data.sqlite_db import SessionLocal
# from pydantic import BaseModel , UploadFile, File
# from API.vending.routers import main_router
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
# import jsbeautifier


# ------------------------------------------------------------
# 3) При старте приложения: читаем все устройства и запускаем по каждому поток sync
# ------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # сюда соберём запущенные device_id
    sync_device_ids: List[int] = []

    # ====== startup ======

    crud = EngineDevice()
    devices = crud.get_all_devices()
    for dev in devices:
        conf = json.loads(dev.details or "{}")
        net = conf.get("network", {})
        ip = net.get("ip")
        port = net.get("port")
        if not ip or not port:
            continue

        device_id = dev.number
        # вызываем start_sync (он сам создаёт внутренний поток)
        start_sync(
            device_id,
            host=ip,
            port=port,
            # TODO: доработать и добавить в базу данных таблицу Device -> details -> device_token
            token="<YOUR_JWT_TOKEN>",
            # HMAC-секрет TODO: доработать и добавить в базу данных таблицу Device -> details -> HMAC
            secret=b"supersecret",
            aes=AES_KEY,                 # <— передаём именно его
            scheduler_sender_timeout=SENDER_TIMEOUT,
            scheduler_receiver_timeout=RECEIVER_TIMEOUT
        )
        sync_device_ids.append(device_id)

    yield  # <- здесь приложение запускается и начинает принимать HTTP-запросы

    # ====== shutdown ======
    for device_id in sync_device_ids:
        stop_sync(device_id)
    # dbSync закроет свои внутренние потоки самостоятельно

# Добавляем MIME-тип для файлов .js
mimetypes.add_type("application/javascript", ".js")

app = FastAPI(title="API основного приложения",
              version="1.0", lifespan=lifespan)
app.include_router(front_router)
# app.mount("/devices", main_router)
app.mount("/backend", backend_router)
app.mount("/sync", sync_router)
app.mount("/assets", StaticFiles(directory=os.path.join(current_dir,
          "frontend", "assets")), name="assets")
app.mount("/scripts", StaticFiles(directory=os.path.join(current_dir,
          "frontend", "scripts")), name="scripts")
app.mount("/JSONs", StaticFiles(directory=os.path.join(current_dir,
          "frontend", "JSONs")), name="JSONs")
app.mount("/style", StaticFiles(directory=os.path.join(current_dir,
          "frontend", "style")), name="style")
# templates = Jinja2Templates(directory="./frontend/page")


@app.middleware("http")
async def nocache_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/scripts/") or request.url.path.startswith("/assets/") or request.url.path.startswith("/style/") or request.url.path.startswith("/JSONs/"):
        # полностью выключаем кэш
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.get("/favicon.png", include_in_schema=False)
async def get_favicon():
    return FileResponse("frontend/assets/img/web/icons8-led-16.png", media_type="image/png")


@app.get("/apple-touch-icon.png")
async def get_apple_touch_icon():
    return FileResponse("/assets/img/apple-touch-icon.png")


@app.get("/favicon-32x32.png")
async def get_favicon_32x32():
    return FileResponse("/assets/img/favicon-32x32.png")


@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("/scripts/manifest.json")


# ------------------------------------------------------------
# 5) Точка входа
# ------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host=Host, port=port)


# 4. Ловушка в самом конце
# @app.get("/{full_path:path}")
# async def catch_all(request: Request):
#     return templates.TemplateResponse("404.html", {"request": request})
#
# class CodeRequest(BaseModel):
#     code: str
#
# @app.post("/beautify")
# def beautify_code(request: CodeRequest):
#     try:
#         opts = jsbeautifier.default_options()
#         beautified_code = jsbeautifier.beautify(request.code, opts)
#         return {"beautified_code": beautified_code}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
