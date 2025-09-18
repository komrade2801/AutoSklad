# frontend/front_router.py
import os
from pathlib import Path
from fastapi import APIRouter, Request, Depends, BackgroundTasks, Query, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from Core.authorization import AuthService
from Core.default import run_setup_process, progress_data, progress_lock

from Core.Parser import HtmlTitleParser, NavigationService
from DB.Engine.RoleCRUD import EngineRole
from DB.Engine.UserCRUD import EngineUser
from DB.Engine.PageCRUD import EnginePage
from DB.Engine.RightsCRUD import EngineRights

# # from DB.Data.db_depends import get_db
# from DB.session import get_db
from DB.session import get_db
from Core.Parser import HtmlTitleParser

auth_service = AuthService()
e_right = EngineRights()

front_router = APIRouter(tags=["gui"])
templates = Jinja2Templates(directory=os.path.join(
    os.path.dirname(__file__), "page"), auto_reload=True)

# определяем папку этого модуля
BASE_DIR = Path(__file__).parent
PAGE_DIR = BASE_DIR / "page"

svc = NavigationService(PAGE_DIR)
list_page = svc.get_root_pages()
# --- Инициализация страниц в БД и регистрация маршрутов ---
_pages_dir = os.path.join(os.path.dirname(__file__), "page")
e_page = EnginePage()

# Определяем стартовый индекс (1-базный), учитывая уже существующие записи
try:
    existing_ids = e_page.get_all_ids()
    next_index = (max(existing_ids) if existing_ids else 0) + 1
except Exception:
    next_index = 1


# Регистрируем динамически все экраны из _screens

def template_endpoint(template_name: str):
    """
    Декоратор для GET-точки доступа, который:
      1. Проверяет пользователя.
      2. Перенаправляет на "/" если нет токена.
      3. При err–payload возвращает страницу ошибки.
      4. Иначе рендерит нужный шаблон.
    """

    async def endpoint(request: Request):
        v = auth_service.validation_user(request)
        if isinstance(v, RedirectResponse):
            return v
        if isinstance(v, dict) and v.get("status") == "error":
            return templates.TemplateResponse(v["url"], {"request": request})
        rights = e_right.get_rights_by_role(v.role_id)
        welcome = False
        for right in rights:
            page = e_page.get_page_by_id(page_id=right.page_id)
            if page is None:
                # либо пропустить такое право
                continue
            if page.name in template_name:
                welcome = True
                break
        if welcome:
            return templates.TemplateResponse(template_name, {"request": request})
        else:
            return RedirectResponse("/403.html", status_code=302)

    return endpoint


for file_name in sorted(os.listdir(_pages_dir)):
    if file_name.startswith("screen") and file_name.endswith(".html"):
        # если нет в БД — создаём
        if not e_page.find_page(name=file_name):
            # parser = HtmlTitleParser(f"../frontend/page/{file_name}")
            parser = HtmlTitleParser(str(PAGE_DIR / file_name))
            description = parser.get_title()
            e_page.add_page(
                name=file_name, description=description, index=next_index)
            next_index += 1
        # регистрируем маршрут
        front_router.add_api_route(
            f"/{file_name}",
            template_endpoint(file_name),
            methods=["GET"],
            response_class=HTMLResponse,
            name=file_name
        )

# Корневой эндпоинт — авторизация


@front_router.get("/", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("authorisation.html", {"request": request})


@front_router.get("/mass_locked.html", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("/mass_locked.html", {"request": request})


@front_router.get("/403.html", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("403.html", {"request": request})


@front_router.get("/404.html", response_class=HTMLResponse)
async def auth_page(request: Request):
    return templates.TemplateResponse("404.html", {"request": request})


@front_router.get("/error_token.html", response_class=HTMLResponse)
async def error_token(request: Request):
    return templates.TemplateResponse("error_token.html", {"request": request})


@front_router.get("/assets/html/nav_btn.html", response_class=HTMLResponse)
async def nav_btn(request: Request, db=Depends(get_db)):
    # 1) Верификация пользователя
    v = auth_service.validation_user(request)
    if isinstance(v, RedirectResponse):
        return v
    if isinstance(v, dict) and v.get("status") == "error":
        return templates.TemplateResponse(v["url"], {"request": request})

    # 2) Получаем права и страницы
    rights_engine = EngineRights()
    page_engine = EnginePage()

    rights = rights_engine.get_rights_by_role_id(v.role_id)
    if not rights:
        return RedirectResponse("/403.html", status_code=302)

    # 3) Собираем все страницы, на которые есть право
    allowed = []
    for r in rights:
        p = page_engine.get_page_by_id(r.page_id)
        if p:
            nested = svc.is_nested(p.name)
            if not nested:
                # p.name — файл, p.description — текст
                allowed.append((p.name, p.description))

    # 4) Передаём в шаблон список tuples (page, label)
    return templates.TemplateResponse(
        "nav_btn.html",
        {
            "request": request,
            "buttons": allowed
        }
    )


@front_router.get("/assets/html/navbar.html", response_class=HTMLResponse)
async def navbar(
        request: Request,
        db=Depends(get_db),
        screen_key: str = Query(..., description="Ключ текущего экрана"),
):
    # 1) Верификация пользователя
    v = auth_service.validation_user(request)
    if isinstance(v, RedirectResponse):
        return v
    if isinstance(v, dict) and v.get("status") == "error":
        return templates.TemplateResponse(v["url"], {"request": request})

    role_id = v.role_id
    user_id = v.user_id

    # 2) Получаем список доступных страниц
    rights_engine = EngineRights()
    page_engine = EnginePage()

    # rights = rights_engine.get_rights_by_role_id(role_id)
    # if not rights:
    #     return RedirectResponse("/403.html", status_code=302)
    #
    # buttons = []
    # for r in rights:
    #     p = page_engine.get_page_by_id(r.page_id)
    #     if not p or svc.is_nested(p.name):
    #         continue
    #     buttons.append((p.name, p.description))

    # 3) Получаем данные о текущей странице
    current_page = None
    ids = page_engine.get_all_ids()
    for index in ids:
        page = page_engine.get_page_by_id(index)
        if screen_key in page.name:
            current_page = page
            break

    if not current_page:
        return RedirectResponse("/404.html", status_code=302)
    # = get_by_name( + ".html")
    screen_name = current_page.description if current_page else ""

    # 4) Получаем информацию о пользователе
    user_engine = EngineUser()
    # предполагается, что есть BaseCRUD.get
    user = user_engine.get_user_by_id(user_id)
    user_fullname = f"{user.second_name} {user.first_name} {user.family}"
    e_role = EngineRole()
    user_role = e_role.get_role_by_id(role_id).name
    # 5) Рендерим шаблон
    return templates.TemplateResponse(
        "navbar.html",
        {
            "request": request,
            # "buttons": buttons,
            "screen_key": screen_key,
            "screen_name": screen_name,
            "user_role": user_role,
            "user_fullname": user_fullname,
        }
    )


@front_router.get("/progress")
async def get_progress():
    with progress_lock:
        return {
            "status": progress_data["status"],
            "stage": progress_data["current_stage"],
            "messages": progress_data["messages"][-5:],
            "percentage": progress_data["percentage"]
        }


@front_router.post("/start")
async def start_setup(background_tasks: BackgroundTasks):
    with progress_lock:
        if progress_data["status"] == "in_progress":
            return {"error": "Operation already in progress"}

        # Сброс прогресса
        progress_data.update({
            "status": "in_progress",
            "messages": [],
            "current_stage": "",
            "percentage": 0
        })

        background_tasks.add_task(run_setup_process)
        return {"message": "Database setup started"}


@front_router.get("/get_interface", response_class=HTMLResponse)
async def get_interface():
    return """
    <html>
    <head>
        <title>DB Setup Progress</title>
        <style>
            .container { width: 80%; margin: 50px auto; }
            .progress-bar { 
                height: 30px; 
                background: #eee;
                border-radius: 15px;
                overflow: hidden;
                position: relative;
            }
            .progress-fill {
                height: 100%;
                background: #4CAF50;
                transition: width 0.3s ease;
            }
            .progress-text {
                margin: 10px 0;
                text-align: center;
            }
            .messages {
                height: 150px;
                overflow-y: auto;
                border: 1px solid #ddd;
                padding: 10px;
                margin: 20px 0;
            }
            button {
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:disabled {
                background: #cccccc;
                cursor: not-allowed;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Database Setup Progress</h1>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">0%</div>
            <div class="messages" id="messages"></div>
            <button onclick="startSetup()" id="startButton">Start Setup</button>
        </div>
        <script>
            let isProcessing = false;

            async function updateProgress() {
                const response = await fetch('/progress');
                const data = await response.json();

                // Update progress bar
                document.getElementById('progressFill').style.width = data.percentage + '%';
                document.getElementById('progressText').textContent = 
                    `${data.stage} (${data.percentage}%)`;

                // Update messages
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = data.messages
                    .map(msg => `<div>${msg}</div>`)
                    .join('');

                // Auto-scroll messages
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Update button state
                const button = document.getElementById('startButton');
                if (data.status === 'in_progress') {
                    button.disabled = true;
                    button.textContent = 'Processing...';
                    setTimeout(updateProgress, 1000);
                } else {
                    button.disabled = false;
                    button.textContent = 'Start Setup';
                }
            }

            async function startSetup() {
                if (isProcessing) return;

                isProcessing = true;
                document.getElementById('startButton').disabled = true;

                try {
                    const response = await fetch('/start', {
                        method: 'POST'
                    });
                    const result = await response.json();

                    if (result.error) {
                        alert(result.error);
                    } else {
                        updateProgress();
                    }
                } catch (error) {
                    alert('Error starting setup: ' + error.message);
                } finally {
                    isProcessing = false;
                }
            }
        </script>
    </body>
    </html>
    """
