from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Импортируем Pydantic‑модели для запросов и ответов
from API.backend.request_models import NormDataResponse, NormDataCreate, NormDataUpdate
# from DB.session import get_db
# # from DB.Data.db_depends import get_db
from DB.session import get_db
from Logic.NormCRUD import EngineNorm

norms_router = APIRouter(prefix="/norms", tags=["Norms"])

@norms_router.get("/get_all", response_model=NormDataResponse)
def get_all_norms(db: Session = Depends(get_db)):
    """
    Получает агрегированные данные норм для всех пользователей.
    Формат ответа соответствует примеру JSON:
    {
        "user":
        {
            "0": { "username": "Иванов Иван", "tools": { "0": {...}, ... } },
            "1": { ... },
            ...
        }
    }
    """
    norm_crud = EngineNorm()
    data = norm_crud.get_all_norm_data()
    if not data or not data.get("user"):
        raise HTTPException(status_code=404, detail="Нормы не найдены")
    return data

@norms_router.get("/get/{user_id}", response_model=NormDataResponse)
def get_norm_for_user(user_id: int, db: Session = Depends(get_db)):
    """
    Получает агрегированные данные норм для конкретного пользователя по его ID.
    """
    norm_crud = EngineNorm()
    data = norm_crud.get_norm_data_from_user(user_id)
    # Если инструменты отсутствуют – считаем, что данных нет
    if not data or not data.get("tools"):
        raise HTTPException(status_code=404, detail="Норма для пользователя не найдена")
    return data

@norms_router.post("/post/{user_id}", response_model=NormDataResponse)
def create_norm_for_user(user_id: int, norm_data: NormDataCreate, db: Session = Depends(get_db)):
    """
    Создаёт (устанавливает) агрегированные данные нормы для пользователя.
    Ожидается, что norm_data содержит ключ "tools" с набором инструментов.
    """
    norm_crud = EngineNorm()
    success = norm_crud.set_norm_data_from_user(user_id, norm_data.to_dict())
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось создать норму")
    return norm_crud.get_norm_data_from_user(user_id)

@norms_router.put("/put/{user_id}", response_model=NormDataResponse)
def update_norm_for_user(user_id: int, norm_data: NormDataUpdate, db: Session = Depends(get_db)):
    """
    Обновляет агрегированные данные нормы для пользователя.
    Ожидается, что norm_data содержит ключ "tools" с набором инструментов для обновления.
    """
    norm_crud = EngineNorm()
    success = norm_crud.update_norm_data_from_user(user_id, norm_data.to_dict())
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось обновить норму")
    return norm_crud.get_norm_data_from_user(user_id)

@norms_router.delete("/delete/{user_id}/{tool_name}")
def delete_tool_norm_for_user(user_id: int, tool_name: str, db: Session = Depends(get_db)):
    """
    "Удаляет" (или обновляет) норму инструмента для пользователя по его названию.
    В данном примере метод find_and_update_tool_in_norm_from_user обновляет запись, например,
    устанавливая значение sum_of_use в 0, что можно трактовать как удаление.
    """
    norm_crud = EngineNorm()
    success = norm_crud.delete_last_tool(user_id, tool_name)
    if not success:
        raise HTTPException(status_code=404, detail="Инструмент не найден или не обновлён")
    return {"message": "Инструмент успешно удалён/обновлён"}

@norms_router.delete("/delete/{user_id}")
def delete_tools_norm_in_user(user_id: int, db: Session = Depends(get_db)):
    """
    "Удаляет" (или обновляет) норму инструмента для пользователя по его названию.
    В данном примере метод find_and_update_tool_in_norm_from_user обновляет запись, например,
    устанавливая значение sum_of_use в 0, что можно трактовать как удаление.
    """
    norm_crud = EngineNorm()
    success = norm_crud.delete_all_tools(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Инструмент не найден или не обновлён")
    return {"message": "Инструмент успешно удалён/обновлён"}
