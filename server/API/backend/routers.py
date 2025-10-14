from fastapi import FastAPI #APIRouter,

from API.backend.endpoints.all_device import all_device_router
from API.backend.endpoints.all_groups import all_groups_router
from API.backend.endpoints.all_users import all_users_router
from API.backend.endpoints.mass_drop import mass_drop_router
from API.backend.endpoints.mass_load import mass_load_router
from API.backend.endpoints.tools import tools_router
from API.backend.endpoints.history import history_router
from API.backend.endpoints.all_plans import all_plans_router
from API.backend.endpoints.all_tools import all_tools_router
from API.backend.endpoints.history_loads import history_loads_router
from API.backend.endpoints.actual_norms import norms_router
from API.backend.endpoints.cells_map import cells_map_router
from API.backend.endpoints.history_error import history_error_router
from API.backend.endpoints.history_operation import history_operation_router
from API.backend.endpoints.history_write_off import history_write_off_router
from API.backend.endpoints.json_random_load import json_random_load_router
from API.backend.endpoints.tool_library import tool_library_router
from API.backend.endpoints.tools_in_vending import tools_in_vending_router


# Импортируем все файлы с роутерами

# Создаем главный роутер, к которому подключаем все остальные
# backend_router = APIRouter()
backend_router = FastAPI(title="API для обеспечения работы фронтенда", version="1.0")
# Подключаем все маршрутизаторы
# main_router.include_router(db_router)
backend_router.include_router(all_users_router)
backend_router.include_router(norms_router)
backend_router.include_router(tools_router)
backend_router.include_router(history_router)
backend_router.include_router(all_plans_router)
backend_router.include_router(all_tools_router)
backend_router.include_router(all_groups_router)
backend_router.include_router(history_loads_router)
backend_router.include_router(cells_map_router)
backend_router.include_router(history_error_router)
backend_router.include_router(history_operation_router)
backend_router.include_router(history_write_off_router)
backend_router.include_router(json_random_load_router)
backend_router.include_router(tool_library_router)
backend_router.include_router(tools_in_vending_router)
backend_router.include_router(mass_load_router)
backend_router.include_router(mass_drop_router)
backend_router.include_router(all_device_router)
