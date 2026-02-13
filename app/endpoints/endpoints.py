from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/{text}", response_class=HTMLResponse)
async def read_root(request: Request, text : str):
    return templates.TemplateResponse("index.html", {"request": request, "text": text})