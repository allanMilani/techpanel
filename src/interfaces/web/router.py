from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from src.application import ConflictAppError
from src.application.dtos import LoginInputDTO
from src.application.use_cases.auth.login import Login
from src.application.use_cases.auth.register_user import RegisterUser
from src.application.dtos.auth_dto import RegisterUserInputDTO
from src.application.use_cases.projects.list_projects import ListProjects
from src.application.use_cases.servers.list_servers import ListServers
from src.interfaces.api.dependencies import (
    get_list_projects,
    get_list_servers_use_case,
    get_login_use_case,
    get_register_user_use_case,
)

templates = Jinja2Templates(directory="src/interfaces/web/templates")
router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"flash": None},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    login_use_case: Annotated[Login, Depends(get_login_use_case)],
) -> Response:
    try:
        out = await login_use_case.execute(
            LoginInputDTO(email=email, password=password)
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"flash": "Credenciais inválidas"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    response = RedirectResponse(url="/app", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("access_token", out.access_token, httponly=True, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"flash": None},
    )


@router.post("/register")
async def register_submit(
    request: Request,
    email: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    register_use_case: Annotated[RegisterUser, Depends(get_register_user_use_case)],
) -> Response:
    try:
        await register_use_case.execute(
            RegisterUserInputDTO(email=email, password=password)
        )
    except ConflictAppError:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"flash": "E-mail ja cadastrado"},
            status_code=status.HTTP_409_CONFLICT,
        )
    except Exception:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"flash": "Nao foi possivel concluir o cadastro"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/app", response_class=HTMLResponse)
async def app_dashboard(
    request: Request,
    list_servers_use_case: Annotated[ListServers, Depends(get_list_servers_use_case)],
    list_projects_use_case: Annotated[ListProjects, Depends(get_list_projects)],
) -> HTMLResponse:
    # Keep web pages resilient in tests/dev even when data dependencies are unavailable.
    try:
        servers = await list_servers_use_case.execute()
    except Exception:
        servers = []
    try:
        projects = await list_projects_use_case.execute()
    except Exception:
        projects = []
    return templates.TemplateResponse(
        request=request,
        name="app/dashboard.html",
        context={
            "servers": servers,
            "projects": projects,
            "flash": None,
        },
    )


@router.get("/app/executions/{execution_id}/panel", response_class=HTMLResponse)
async def execution_panel(
    request: Request,
    execution_id: UUID,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="app/partials/execution_panel.html",
        context={"execution_id": execution_id},
    )


@router.get("/app/projects/{project_id}/history", response_class=HTMLResponse)
async def project_history(
    request: Request,
    project_id: UUID,
) -> HTMLResponse:
    _ = project_id
    history: list[object] = []
    return templates.TemplateResponse(
        request=request,
        name="app/partials/history_table.html",
        context={"history": history},
    )
