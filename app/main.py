from fastapi import FastAPI
from app.router import router
from fastapi.staticfiles import StaticFiles
from app.database.database import engine
from app.database.models import Base

app = FastAPI()
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

