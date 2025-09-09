import os
import mimetypes

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from frontend.setting_router import setting_router
from options import Host, port

current_dir = os.path.dirname(os.path.abspath(__file__))

# Добавляем MIME-тип для файлов .js
mimetypes.add_type("application/javascript", ".js")

defaulter = FastAPI(title="Стартовые настройки", version="1.0")

defaulter.mount("/defaulter", setting_router)

defaulter.mount("/assets", StaticFiles(directory=os.path.join(current_dir, "frontend", "assets")), name="assets")
defaulter.mount("/scripts", StaticFiles(directory=os.path.join(current_dir, "frontend", "scripts")), name="scripts")
defaulter.mount("/JSONs", StaticFiles(directory=os.path.join(current_dir, "frontend", "JSONs")), name="JSONs")
defaulter.mount("/style", StaticFiles(directory=os.path.join(current_dir, "frontend", "style")), name="style")

# ------------------------------------------------------------
# 5) Точка входа
# ------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(defaulter, host=Host, port=port)
