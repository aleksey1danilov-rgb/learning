from fastapi import APIRouter
from app.api.v1 import auth
from app.api.v1 import admin

# ПРЕФИКС ДОЛЖЕН БЫТЬ ЗДЕСЬ!
router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(admin.router)