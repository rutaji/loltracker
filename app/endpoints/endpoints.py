import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from app.api.config import settings

from app.database.DAO import DAO

from app.services.summonerServices import load_summoner_page, refresh_summoner_matches_service
from app.services.championServices import build_trend_series, get_champion_service, serialize_stat
from app.utils.champion_assets import resolve_champion_image_path
from app.utils.versioning import version_sort_key

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)


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
    logger.info("request at root: %s",request)
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
    logger.info(
        "Fetching summoner data",
        extra={
            "summoner_name": name,
            "tagline": tagline,
            "offset": offset,
            "is_ajax": ajax
        }
    )

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


@router.post("/summoner/{name}/{tagline}/refresh")
async def refresh_summoner(
    request: Request,
    name: str,
    tagline: str,
    dao: DAO = Depends(get_dao),
):
    refresh_result = refresh_summoner_matches_service(request, name, tagline, dao)
    if refresh_result.summoner is None:
        raise HTTPException(status_code=404, detail="Summoner not found")

    return JSONResponse(
        content={
            "insertedCount": refresh_result.inserted_count,
            "failedCount": refresh_result.failed_count,
            "summonerName": refresh_result.summoner.name,
            "summonerTagline": refresh_result.summoner.tagline,
        }
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
    trend_champion = get_champion_service(name, None, dao)

    if champion is None and trend_champion is not None:
        available_versions = sorted(
            {stat.version for stat in trend_champion.championStats},
            key=version_sort_key,
            reverse=True,
        )
        if available_versions:
            version = available_versions[0]
            champion = get_champion_service(name, [version], dao)

    if champion is None:
        return RedirectResponse(
            url=(
                f"/champion/not-found?name={quote(name, safe='')}"
            ),
            status_code=303
        )

    if trend_champion is None:
        trend_champion = champion

    available_versions = sorted(
        {stat.version for stat in trend_champion.championStats},
        key=version_sort_key,
        reverse=True,
    )
    if not available_versions:
        available_versions = [version]

    selected_stats = [serialize_stat(stat) for stat in champion.championStats]
    trend_series = build_trend_series(trend_champion.championStats)
    champion_image_path = resolve_champion_image_path(champion.name)
    
    if ajax:
        return JSONResponse(
            content={
                "name": champion.name,
                "selectedVersion": version,
                "availableVersions": available_versions,
                "championImagePath": champion_image_path,
                "selectedVersionStats": selected_stats,
                "trendSeriesByMode": trend_series,
                # Backward compatibility for previous JS/tests
                "championStats": selected_stats,
            }
        )
    
    return templates.TemplateResponse(
        request=request,
        name="champion.html",
        context={
            "championData": champion,
            "version": version,
            "available_versions": available_versions,
            "champion_image_path": champion_image_path,
            "trend_series": jsonable_encoder(trend_series),
        },
    )
