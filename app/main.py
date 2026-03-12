from fastapi import FastAPI
from app.router import router
from fastapi.staticfiles import StaticFiles
from app.database.database import engine,Base
import app.database.models as _  # import necessary for creating models

app = FastAPI()
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)