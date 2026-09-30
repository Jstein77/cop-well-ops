from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.auth import User, get_current_user
from app.templating import templates

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request, user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"user": user})


@router.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}
