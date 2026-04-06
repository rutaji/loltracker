import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from app.router import router
from fastapi.staticfiles import StaticFiles
from app.database.database import engine
from app.database.models import Base
from app.riot.riotApiClient import RiotApiClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        raise RuntimeError("RIOT_API_KEY is missing from the .env file.")

    app.state.api_client = RiotApiClient(api_key=api_key, regional_routing="europe")
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

