# import traceback
import traceback
from typing import List

# from sqlalchemy.orm import Session
from fastapi import APIRouter, Request, status  # Depends, HTTPException,
from sqlalchemy.exc import IntegrityError
import secrets
from API.backend.request_models import (UserResponse, RoleResponse, UserUpdate,
                                        UserPartialUpdate, UserCreate, RoleUpdate,
                                        RoleCreate, RightsCreate, RightsResponse,
                                        RightsUpdate, AllUserResponse,
                                        UserCredentialsInput, UserCredentialsResponse)  # AuthResponse,
from Core.authorization import AuthService, TokenData
# from DB.Data.db_depends import get_db
from DB.session import get_db
from DB.Engine.RightsCRUD import EngineRights
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.UserCRUD import EngineUser
# import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta  # datetime,
# путь и название модели может отличаться
from API.backend.request_models import AuthResponse
import barcode
from barcode.codex import Code128
from barcode.writer import ImageWriter
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


# from frontend.front_router import validation_user
# from get_token import SECRET_KEY
auth_service = AuthService()
# Настройки для JWT
# SECRET_KEY = "your_secret_key_here"

all_users_router = APIRouter(tags=["all_users"])


# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


@all_users_router.get("/authorization", response_model=AuthResponse)
def user_authorization(login: str, password: str, db: Session = Depends(get_db)):
    """
    Возвращает данные авторизации: токен, redirect_url и информацию о пользователе, если логин/пароль корректны.
    """
    try:
        if login == '' or password == '':
            raise HTTPException(status_code=402, detail="Некорректные данные")

        # Инициализируем движки для работы с пользователями и ролями
        e_user = EngineUser()
        e_role = EngineRole()

        # 1. Получаем пользователя по логину
        user = e_user.get_user_by_code(int(login))
        if not user:
            raise HTTPException(
                status_code=401, detail="Пользователь не найден")

        # Проверяем пароль
        if str(user.password) != str(password):
            raise HTTPException(status_code=511, detail="Неверный пароль")

        # 2. Получаем роль пользователя
        role = e_role.get_role_by_id(user.role_id)
        if not role:
            raise HTTPException(status_code=401, detail="Роль не найдена")

        # Подготовим данные для формирования ответа
        user_response = {
            "index": user.id,
            "barcode": user.barcode,
            "code": user.code,
            "first_name": user.first_name,
            "password": user.password,
            "second_name": user.second_name,
            "family": user.family,
            "role_id": role.id
        }

        # Генерируем JWT-токен
        token_data = TokenData(
            user_id=user.id, user_barcode=user.barcode, role_id=user.role_id)
        token = auth_service.create_access_token(
            token_data=token_data,
            expires_delta=timedelta(
                minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        # Определяем redirect_url на основе идентификатора роли
        if role.id == 1:
            redirect_url = '/screen_14_history_load.html'
        elif role.id == 2:
            redirect_url = '/screen_14_history_load.html'
        elif role.id == 3:
            redirect_url = '/screen_14_history_load.html'
        elif role.id == 4:
            redirect_url = '/screen_14_history_load.html'
        else:
            redirect_url = '/'

        return AuthResponse(token=token, redirect_url=redirect_url, user=user_response)
    except RuntimeError as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e), "traceback": tb})
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e), "traceback": tb})


@all_users_router.get("/all_users", response_model=AllUserResponse)
def all_users(db: Session = Depends(get_db)):
    """
    Возвращает полный список пользователей системы с расширенной информацией.

    Логика работы:
    1. Инициализация движков работы с пользователями и ролями
    2. Получение списка всех зарегистрированных пользователей
    3. Для каждого пользователя:
       - Получение связанной роли через Role_id
       - Формирование объекта UserResponse с полными данными
    4. Упаковка результатов в модель AllUserResponse

    Возвращает:
    - Объект AllUserResponse со списком пользователей в поле 'users'

    Исключения:
    - HTTP 401: Если не найдено ни одного пользователя в системе

    Пример ответа:
    {
        "users": [
            {
                "index": 1,
                "barcode": "123456",
                "code": "user1",
                "first_name": "Иван",
                ...
            }
        ]
    }
    """
    # Инициализируем движки для работы с пользователями и ролями
    e_user = EngineUser()
    e_role = EngineRole()

    users = e_user.get_all_users()
    if not users:
        raise HTTPException(status_code=401, detail="Пользователи не найдены")

    all_user_response = []
    for user in users:
        role = e_role.get_role_by_id(user.role_id)
        user_response = UserResponse(
            index=user.id,
            barcode=user.barcode,
            code=user.code,
            first_name=user.first_name,
            password='****',  # user.password
            second_name=user.second_name,
            family=user.family,
            role=role.name
        )
        all_user_response.append(user_response)

    return AllUserResponse(users=all_user_response)


@all_users_router.get(
    "/user_barcode",
    responses={200: {"content": {"image/png": {}}}},
    response_class=StreamingResponse,
)
def user_barcode(user_id: int, db: Session = Depends(get_db)):
    # 1) Получаем пользователя
    e_user = EngineUser()
    user = e_user.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Генерируем штрих-код как PIL.Image
    data = str(user.barcode)
    barcode_obj = Code128(data, writer=ImageWriter())
    code_img: Image.Image = barcode_obj.render()
    w, h = code_img.size

    # 3) Дорисовываем подпись (имя и фамилию)
    padding = 40
    canvas = Image.new("RGBA", (w, h + padding), "WHITE")
    canvas.paste(code_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    try:
        # Попробуем системный шрифт
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except (OSError, IOError):
        # Аварийно — встроенный bitmap-шрифт
        try:
            # Windows
            font = ImageFont.truetype("arial.ttf", 32)
        except (OSError, IOError):
            # Ничего другого не нашли — используем дефолт (без контроля размера)
            font = ImageFont.load_default()
    text = f"{user.first_name} {user.family}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (w - text_w) // 2
    y = h + (padding - text_h) // 2
    draw.text((x, y), text, fill="black", font=font)

    # 4) Сохраняем в BytesIO и возвращаем
    out_buf = BytesIO()
    canvas.convert("RGB").save(out_buf, format="PNG")
    out_buf.seek(0)
    return StreamingResponse(out_buf, media_type="image/png")


@all_users_router.post("/create_user", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    e_user = EngineUser(session=db)
    e_role = EngineRole(session=db)
    try:
        created_user = e_user.create_user(user)
        if not created_user:
            raise HTTPException(
                status_code=400, detail="Ошибка создания пользователя")
        role = e_role.get_role_by_id(created_user.role_id)
        role_name = role.name
        return UserResponse(
            index=created_user.id,
            barcode=created_user.barcode,
            code=created_user.code,
            first_name=created_user.first_name,
            password=created_user.password,
            second_name=created_user.second_name,
            family=created_user.family,
            role=role_name,
        )
    except IntegrityError as ie:
        # например, код занят
        raise HTTPException(status_code=409, detail="Code already exists or duplicate data")
    except Exception as e:
        # любые другие ошибки
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Unexpected server error")


# PUT эндпоинт для полного обновления данных пользователя
@all_users_router.put("/update_user/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Полностью обновляет данные пользователя по его идентификатору.

    :param user_id: Идентификатор пользователя.
    :param user_data: Объект с новыми данными пользователя.
    :param db: Сессия для работы с базой данных.
    :return: Обновленный пользователь.
    """
    e_user = EngineUser()
    updated_user = e_user.put_user(user_id, user_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return updated_user


# PATCH эндпоинт для частичного обновления данных пользователя
@all_users_router.patch("/patch_user/{user_id}", response_model=UserResponse)
def patch_user(user_id: int, user_data: UserPartialUpdate, db: Session = Depends(get_db)):
    """
    Частично обновляет данные пользователя по его идентификатору.

    :param user_id: Идентификатор пользователя.
    :param user_data: Объект с данными для частичного обновления.
    :param db: Сессия для работы с базой данных.
    :return: Обновленный пользователь.
    """
    e_user = EngineUser()
    patched_user = e_user.patch_user(user_id, user_data)
    if not patched_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return patched_user


@all_users_router.delete("/delete_user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Удаляет пользователя по идентификатору.

    :param user_id: Идентификатор пользователя.
    :param db: Сессия базы данных.
    :return: Сообщение об успешном удалении.
    """
    e_user = EngineUser()
    if not e_user.delete_user(user_id):
        raise HTTPException(status_code=404, detail="Пользователя не найден")
    return {"detail": "Запись о пользователя успешно удалена"}


# ### Эндпоинты для Rights

@all_users_router.post("/create_right", response_model=RightsResponse)
def create_right(right: RightsCreate, db: Session = Depends(get_db)):
    """
    Создает новое право доступа.

    :param right: Данные для создания нового права доступа.
    :param db: Сессия базы данных.
    :return: Созданное право доступа.
    """
    e_rights = EngineRights()
    # Метод add_right возвращает True/False. При успешном добавлении рекомендуется получить созданный объект.
    # index = right.id,
    if not e_rights.add_right(
            name=right.Name,  # Name
            # status=right.status,  # Description
            role_id=right.Role_id,  # Role_id
            page_id=right.page_id,  # page_id
            description=right.Description,  # status
    ):
        raise HTTPException(
            status_code=400, detail="Ошибка создания записи о праве доступа")
    new_right = e_rights.get_right_by_id(right.id)
    if not new_right:
        raise HTTPException(
            status_code=500, detail="Ошибка получения созданной записи о праве доступа")
    return new_right


@all_users_router.get("/get_right/{right_id}", response_model=RightsResponse)
def get_right(right_id: int, db: Session = Depends(get_db)):
    """
    Возвращает право доступа по его идентификатору.

    :param right_id: Идентификатор права доступа.
    :param db: Сессия базы данных.
    :return: Объект права доступа.
    """
    e_rights = EngineRights()
    right = e_rights.get_right_by_id(right_id)
    if not right:
        raise HTTPException(status_code=404, detail="Право доступа не найдено")
    return right


@all_users_router.get("/list_rights", response_model=List[RightsResponse])
def list_rights(db: Session = Depends(get_db)):
    """
    Возвращает список всех прав доступа.

    :param db: Сессия базы данных.
    :return: Список объектов прав доступа.
    """
    e_rights = EngineRights()
    rights = e_rights.get_all_rights()
    return rights


@all_users_router.put("/update_right/{right_id}", response_model=RightsResponse)
def update_right(right_id: int, right_data: RightsUpdate, db: Session = Depends(get_db)):
    """
    Полностью обновляет данные права доступа по идентификатору.

    :param right_id: Идентификатор права доступа.
    :param right_data: Объект с новыми данными для обновления.
    :param db: Сессия базы данных.
    :return: Обновленное право доступа.
    """
    e_rights = EngineRights()
    updated = e_rights.update_right(
        right_id,
        name=right_data.Name,
        description=right_data.Description,
        role_id=right_data.Role_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Право доступа не найдено")
    updated_right = e_rights.get_right_by_id(right_id)
    return updated_right


@all_users_router.delete("/delete_right/{right_id}")
def delete_right(right_id: int, db: Session = Depends(get_db)):
    """
    Удаляет право доступа по идентификатору.

    :param right_id: Идентификатор права доступа.
    :param db: Сессия базы данных.
    :return: Сообщение об успешном удалении.
    """
    e_rights = EngineRights()
    if not e_rights.delete_right(right_id):
        raise HTTPException(status_code=404, detail="Право доступа не найдено")
    return {"detail": "Запись о праве доступа успешно удалена"}


# ### Эндпоинты для Role

@all_users_router.post("/create_role", response_model=RoleResponse)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    """
    Создает новую роль.

    :param role: Данные для создания новой роли.
    :param db: Сессия базы данных.
    :return: Созданная роль.
    """
    e_role = EngineRole()
    if not e_role.add_role(
        id=role.id,
        name=role.Name,
        description=role.Description,
        parent_role_id=role.ParentRole_id
    ):
        raise HTTPException(status_code=400, detail="Ошибка создания роли")
    # Предполагается, что уникальность названия роли позволяет получить вновь созданную роль.
    roles = e_role.all()
    new_role = next((r for r in roles if r.Name == role.name), None)
    if not new_role:
        raise HTTPException(
            status_code=500, detail="Ошибка получения созданной роли")
    return new_role


@all_users_router.get("/get_role/{role_id}", response_model=RoleResponse)
def get_role(request: Request, role_id: int, db: Session = Depends(get_db)):
    """
    Возвращает роль по её идентификатору.

    :param request:
    :param role_id: Идентификатор роли.
    :param db: Сессия базы данных.
    :return: Объект роли.
    """
    e_role = EngineRole()
    role = e_role.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    return RoleResponse(index=role.id, name=role.name, description=role.description, parent_role_id=role.parent_role_id)


@all_users_router.get("/list_roles", response_model=List[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    """
    Возвращает список всех ролей.
    """
    e_role = EngineRole()
    roles = e_role.get_all_roles()  # список SQLAlchemy Role

    # Преобразуем каждый ORM-объект в Pydantic-модель
    response = []
    for role in roles:
        response.append(RoleResponse(
            index=role.id,
            name=role.name,  # атрибут вашей модели
            description=role.description,  # атрибут вашей модели
            parent_role_id=role.parent_role_id  # если у вас поле называется иначе, поправьте
        ))

    return response


@all_users_router.put("/update_role/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    """
    Полностью обновляет данные роли по идентификатору.

    :param role_id: Идентификатор роли.
    :param role_data: Объект с новыми данными роли.
    :param db: Сессия базы данных.
    :return: Обновленная роль.
    """
    e_role = EngineRole()
    updated = e_role.update_role(
        role_id,
        name=role_data.Name,
        description=role_data.Description,
        parent_role_id=role_data.ParentRole_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    updated_role = e_role.get_role_by_id(role_id)
    return updated_role


@all_users_router.delete("/delete_role/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    """
    Удаляет роль по её идентификатору.

    :param role_id: Идентификатор роли.
    :param db: Сессия базы данных.
    :return: Сообщение об успешном удалении роли.
    """
    e_role = EngineRole()
    if not e_role.delete_role(role_id):
        raise HTTPException(status_code=404, detail="Роль не найдена")
    return {"detail": "Роль успешно удалена"}


def generate_login_password(first_name: str, patronymic: str, last_name: str, barcode: str, exists_check=None):
    """
    Генерирует логин и пароль на основе переданных параметров с учетом уникальности логина.

    Параметры:
      - first_name (str): Имя.
      - patronymic (str): Отчество.
      - last_name (str): Фамилия.
      - barcode (str): Штрих-код в формате строки, например '2348615250945'.
      - exists_check (callable, optional): Функция для проверки уникальности логина.
            Принимает строку логина и возвращает True, если логин уже существует, и False иначе.

    Возвращает:
      - tuple: Кортеж из двух строк, представляющих логин (4 цифры) и пароль (4 цифры).

    Алгоритм:
      1. Логин: суммируются ASCII-коды первых символов имени, отчества и фамилии; затем результат берется по модулю 10000.
      2. Пароль: суммируются ASCII-коды всех символов полного имени (конкатенация имени, отчества и фамилии)
         плюс числовое значение последних 4 цифр штрих-кода; итоговое число берется по модулю 10000.
      3. Если функция exists_check передана, и сгенерированный логин уже существует, к логину добавляется
         случайное число (соль) и результат нормируется по модулю 10000. Проверка повторяется до нахождения уникального логина.
      4. Результаты приводятся к 4-значному формату (с лидирующими нулями при необходимости).
    """
    try:
        # Проверка корректности штрих-кода
        if len(barcode) < 4 or not barcode.isdigit():
            raise ValueError(
                "Штрих-код должен состоять минимум из 4 цифр и содержать только числа.")

        # Базовая генерация логина по первым символам имени, отчества и фамилии
        login_value = (
            ord(first_name[0]) + ord(patronymic[0]) + ord(last_name[0])) % 10000

        # Генерация пароля: сумма ASCII-кодов полного имени + последние 4 цифры штрих-кода
        full_name = first_name + patronymic + last_name
        name_sum = sum(ord(char) for char in full_name)
        barcode_value = int(barcode[-4:])
        password_value = (name_sum + barcode_value) % 10000

        # Если передана функция проверки уникальности, проверяем логин на наличие совпадений
        if exists_check is not None:
            max_attempts = 10  # ограничиваем число попыток для избежания зацикливания
            attempts = 0
            while exists_check(int(str(login_value).zfill(4))):
                if attempts >= max_attempts:
                    raise ValueError(
                        "Не удалось сгенерировать уникальный логин после нескольких попыток.")
                # Добавляем случайное число в качестве соли и пересчитываем значение логина
                random_salt = secrets.randbelow(10000)
                login_value = (login_value + random_salt) % 10000
                attempts += 1

        # Приведение к 4-значному формату
        login = str(login_value).zfill(4)
        password = str(password_value).zfill(4)

        return login, password
    except Exception as e:
        raise ValueError(f"Ошибка при генерации логина и пароля: {e}")


@all_users_router.post("/generate_credentials", response_model=UserCredentialsResponse, status_code=status.HTTP_200_OK)
def generate_credentials(data: UserCredentialsInput, db: Session = Depends(get_db)):
    """
    Генерирует уникальные логин и пароль для пользователя на основе входных данных.

    Логика работы:
      1. Принимает входные параметры (имя, отчество, фамилия, штрих-код).
      2. Используется функция generate_login_password для базовой генерации логина и пароля.
      3. Встроена проверка наличия совпадений логина:
         - Если сгенерированный логин уже существует в базе (проверка через EngineUser), применяется случайная соль.
         - При исчерпании числа попыток выдается ошибка.
      4. Возвращается объект с уникальными логином и паролем.

    Параметры:
      - data (UserCredentialsInput): Входные данные пользователя.
      - db (Session): Сессия для работы с базой данных.

    Возвращает:
      - UserCredentialsResponse: Объект, содержащий сгенерированные поля login и password.

    Исключения:
      - HTTP 400: При ошибках генерации уникальных значений логина и пароля.
    """
    # Инициализируем движок для работы с пользователями
    e_user = EngineUser()

    def exists_check(login: int) -> bool:
        # Предполагается, что уникальное значение пользователя хранится в поле Code
        # Если метод get_user_by_code возвращает пользователя, значит логин уже занят
        return e_user.get_user_by_code(login) is not None

    try:
        login, password = generate_login_password(
            data.first_name,
            data.patronymic,
            data.last_name,
            data.barcode,
            exists_check=exists_check
        )
        return UserCredentialsResponse(login=login, password=password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
