from fastapi import APIRouter

from app.api.users import router as user_router

api_router = APIRouter(prefix="/api")
api_router.include_router(user_router)
