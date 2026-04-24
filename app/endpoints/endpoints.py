import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from app.api.config import settings

from app.database.DAO import DAO

from app.services.summonerServices import load_summoner_page, refresh_summoner_matches_service
from app.services.championServices import get_champion_service

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
    logger.info("Endpoint root get: %s",request)
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
        target = (
            f"/summoner/{quote(summoner_name, safe='')}"
            f"/{quote(summoner_tagline, safe='')}"
        )
        logger.info("Redirecting to summoner page", extra={"target": target})
        return RedirectResponse(url=target, status_code=303)

    # Champion path
    if champion_name:
        target = f"/champion/{quote(champion_name, safe='')}"
        logger.info("Redirecting to champion page", extra={"target": target})
        return RedirectResponse(url=target, status_code=303)

    logger.info("No search input provided, redirecting to root")
    return RedirectResponse(url=f"/", status_code=303)

@router.get("/summoner/not-found")
async def summoner_not_found(request: Request, name: str = "", tagline: str = ""):
    logger.info(
        "Summoner page requested but not found",
        extra={"searched_name": name or None, "searched_tagline": tagline or None},
    )

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
        "Endpoint started /summoner/{name}/{tagline}",
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

    logger.info(
        "Endpoint ended /summoner/{name}/{tagline}",extra= {"summoner_name": name, "tagline": tagline, "match_page":match_page})
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
    logger.info(
        "Endpoint started /summoner/{name}/{tagline}/refresh",
        extra={"summoner_name": name, "tagline": tagline},
    )

    refresh_result = refresh_summoner_matches_service(request, name, tagline, dao)
    if refresh_result.summoner is None:
        logger.info(
            "Failed to refresh summoner - not found",
            extra={"summoner_name": name, "tagline": tagline},
        )
        raise HTTPException(status_code=404, detail="Summoner not found")

    logger.info(
        "Endpoint finished /summoner/{name}/{tagline}/refresh",
        extra={
            "summoner_name": refresh_result.summoner.name,
            "summoner_tagline": refresh_result.summoner.tagline,
            "insertedCount": refresh_result.inserted_count,
            "failedCount": refresh_result.failed_count,
        },
    )

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
    logger.warning("Champion page requested but not found", extra={"searched_name": name or None})

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
    logger.info("Endpoint started /champion/{name}", extra={"name": name, "version": version, "is_ajax": ajax})

    champion = get_champion_service(name, [version], dao)

    if champion is None:
        target = f"/champion/not-found?name={quote(name, safe='')}"
        logger.info("Champion not found, redirecting", extra={"target": target})
        return RedirectResponse(url=target, status_code=303)
    
    if ajax:
        return JSONResponse(content=jsonable_encoder(champion))
    
    logger.info("Endpoint finished /champion/{name}", extra={"name": name, "version": version})
    return templates.TemplateResponse(
        request=request,
        name="champion.html",
        context={
            "championData": champion,
            "version": version
        },
    )
