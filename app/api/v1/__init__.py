from fastapi import APIRouter
from app.api.v1 import auth
from app.api.v1 import admin
from app.api.v1 import registration 

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(admin.router)
router.include_router(registration.router) 