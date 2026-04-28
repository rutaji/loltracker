import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from app.api.config import settings

from app.database.DAO import DAO

from app.services.summonerServices import load_summoner_page, refresh_summoner_matches_service, load_favorite_champions
from app.services.championServices import (
    aggregate_stats_for_version,
    build_trend_series,
    get_available_versions,
    get_champion_service,
    serialize_stat,
)
from app.utils.champion_kit import resolve_champion_kit
from app.utils.champion_assets import resolve_champion_image_path
from app.utils.versioning import normalize_version

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
    favorite_champion = load_favorite_champions(summoner.puuid,dao,settings.favorite_champion_count)
    match_page = page_data.match_page

    if ajax:
        return JSONResponse(content=jsonable_encoder(match_page))

    return templates.TemplateResponse(
        request=request,
        name="summoner.html",
        context={
            "summoner": summoner,
            "matchData": match_page,
            "favoriteChampios":favorite_champion
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
    trend_champion = get_champion_service(name, None, dao)

    if trend_champion is None:
        return RedirectResponse(
            url=(
                f"/champion/not-found?name={quote(name, safe='')}"
            ),
            status_code=303
        )

    available_versions = get_available_versions(trend_champion.championStats)
    if not available_versions:
        available_versions = [normalize_version(version)]

    selected_version = normalize_version(version)
    if selected_version not in available_versions:
        selected_version = available_versions[0]

    selected_stat_models = aggregate_stats_for_version(trend_champion.championStats, selected_version)
    selected_stats = [serialize_stat(stat) for stat in selected_stat_models]

    trend_series = build_trend_series(trend_champion.championStats)
    
    champion_image_path = resolve_champion_image_path(trend_champion.id)
    champion_kit = resolve_champion_kit(trend_champion.id)
    
    if ajax:
        return JSONResponse(
            content={
                "name": trend_champion.name,
                "selectedVersion": selected_version,
                "availableVersions": available_versions,
                "championImagePath": champion_image_path,
                "championKit": champion_kit,
                "selectedVersionStats": selected_stats,
                "trendSeriesByQueue": trend_series,
                # Backward compatibility for previous JS/tests
                "championStats": selected_stats,
            }
        )
    
    return templates.TemplateResponse(
        request=request,
        name="champion.html",
        context={
            "championData": trend_champion,
            "version": selected_version,
            "available_versions": available_versions,
            "champion_image_path": champion_image_path,
            "champion_kit": jsonable_encoder(champion_kit),
            "trend_series": jsonable_encoder(trend_series),
        },
    )
