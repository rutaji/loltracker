from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from app.api.config import settings

from app.database.DAO import DAO

from app.services.summonerServices import load_summoner_page
from app.services.championServices import get_champion_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_dao():
    dao = DAO.get_dao()
    try:
        yield dao
    except Exception:
        dao.rollback()
        raise
    finally:
        dao.close()


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.post("/", response_class=RedirectResponse)
async def search(
    summoner_name: str = Form(default=""),
    summoner_tagline: str = Form(default=""),
    champion_name: str = Form(default=""),
):
    summoner_name = summoner_name.strip()
    summoner_tagline = summoner_tagline.strip()
    champion_name = champion_name.strip()

    # Summoner path
    if summoner_name:
        return RedirectResponse(
            url=(
                f"/summoner/{quote(summoner_name, safe='')}"
                f"/{quote(summoner_tagline, safe='')}"
            ),
            status_code=303,
        )

    # Champion path
    if champion_name:
        return RedirectResponse(
            url=f"/champion/{quote(champion_name, safe='')}",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/",
        status_code=303
    )

@router.get("/summoner/not-found")
async def summoner_not_found(request: Request, name: str = "", tagline: str = ""):

    return templates.TemplateResponse(
        request=request,
        name="summoner_not_found.html",
        context={
            "searched_name": name,
            "searched_tagline": tagline,
        },
    )

@router.get("/summoner/{name}/{tagline}", response_class=HTMLResponse)
async def get_summoner(
    request: Request,
    name: str,
    tagline: str,
    offset: int = 0,
    ajax: bool = False,
    dao: DAO = Depends(get_dao),
):
    count = settings.matches_per_page

    page_data = load_summoner_page(request, name, tagline, offset, count, dao)
    summoner = page_data.summoner
    if summoner is None:
        return RedirectResponse(
            url=(
                f"/summoner/not-found?name={quote(name, safe='')}"
                f"&tagline={quote(tagline, safe='')}"
            ),
            status_code=303
        )
    match_page = page_data.match_page

    if ajax:
        return JSONResponse(content=jsonable_encoder(match_page))

    return templates.TemplateResponse(
        request=request,
        name="summoner.html",
        context={
            "summoner": summoner,
            "matchData": match_page
        },
    )

@router.get("/champion/not-found")
async def champion_not_found(request: Request, name: str = ""):

    return templates.TemplateResponse(
        request=request,
        name="champion_not_found.html",
        context={
            "searched_name": name,
        },
    )

@router.get("/champion/{name}")
async def get_champion(
    request: Request,
    name: str,
    version: str = settings.default_champion_version,
    ajax: bool = False,
    dao: DAO = Depends(get_dao),
):
    champion = get_champion_service(name, [version], dao)

    if champion is None:
        return RedirectResponse(
            url=(
                f"/champion/not-found?name={quote(name, safe='')}"
            ),
            status_code=303
        )
    
    if ajax:
        return JSONResponse(content=jsonable_encoder(champion))
    
    return templates.TemplateResponse(
        request=request,
        name="champion.html",
        context={
            "championData": champion,
            "version": version
        },
    )
