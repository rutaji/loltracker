from fastapi import APIRouter
from app.endpoints import endpoints

router = APIRouter()
router.include_router(endpoints.router, tags=["endpoints"])