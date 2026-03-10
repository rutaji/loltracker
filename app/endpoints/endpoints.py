from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.services.summonerServices import get_summoner_service
from app.services.stubDAO import stubDAO

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
dao=stubDAO()

@router.get("/{text}", response_class=HTMLResponse)
async def read_root(request: Request, text : str):
    return templates.TemplateResponse("index.html", {"request": request, "text": text})

@router.get("/summoner/{name}", response_class=HTMLResponse)
async def get_summoner(request: Request, name: str, offset: int = 0, ajax: bool = False):

    count=3

    data=get_summoner_service(name, dao, offset, count)

    if ajax:
        return JSONResponse(data["matchData"])

    return templates.TemplateResponse(
        "summoner.html",
        {
            "request": request,
            "summoner": data["summoner"],
            "matchData": data["matchData"]
        }
    )