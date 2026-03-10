from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.summonerServices import get_summoner_service
import services.stubDAO

router = APIRouter()
templates = Jinja2Templates(directory="templates")
dao=stubDAO()

@router.get("/{text}", response_class=HTMLResponse)
async def read_root(request: Request, text : str):
    return templates.TemplateResponse("index.html", {"request": request, "text": text})

@router.get("/summoner/{name}", response_class=HTMLResponse)
async def get_summoner(request: Request, name: str):
    summoner=get_summoner_service(name, dao)