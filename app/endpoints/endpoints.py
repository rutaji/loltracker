from urllib.parse import quote, unquote

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from app.services.summonerServices import get_summoner_service, get_matches_service
from app.services.stubDAO import stubDAO
from app.models.summonerModels import SummonerData

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
dao=stubDAO()

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
        # Neni nutny checkovat tagline pac je required v html
        summoner = get_summoner_service(summoner_name, summoner_tagline, dao)
        if summoner:
            return RedirectResponse(
                url=(
                    f"/summoner/{quote(summoner_name, safe="")}"
                    f"/{quote(summoner_tagline, safe="")}"
                ),
                status_code=303,
            )
        return RedirectResponse(
            url=(
                f"/summoner/not-found?name={quote(summoner_name, safe="")}"
                f"&tagline={quote(summoner_tagline, safe="")}"
            ),
            status_code=303
        )

    # Champion path
    '''
    if champion_name:
        champion = get_champion_service()
        if champion:
            return RedirectResponse(
                url=f"/champion/{quote(champion_name, safe='')}",
                status_code=303,
            )
    '''

    return RedirectResponse(
        url=f"/",
        status_code=303
    )

@router.get("/summoner/{name}/{tagline}", response_class=HTMLResponse)
async def get_summoner(request: Request, name: str, tagline: str, offset: int = 0, ajax: bool = False):

    count=3

    summoner = get_summoner_service(name, tagline, dao)
    if summoner is None:
        return RedirectResponse(
            url=(
                f"/summoner/not-found?name={quote(name, safe="")}"
                f"&tagline={quote(tagline, safe="")}"
            ),
            status_code=303
        )

    match_page = get_matches_service(name, tagline, offset, count, dao)
    summoner_data = SummonerData(summoner=summoner, matchPage=match_page)

    if ajax:
        return summoner_data

    return templates.TemplateResponse(
        "summoner.html",
        {
            "request": request,
            "summoner": summoner,
            "matchData": match_page
        }
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
