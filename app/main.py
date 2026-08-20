from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.routers import pages
from app.api.v1 import router as api_router
from app.core.database import engine, Base
from app.core.middleware import RegistrationCheckMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Avito Learning",
    description="Платформа для обучения сотрудников",
    version="1.0.0"
)

app.add_middleware(RegistrationCheckMiddleware)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)

app.include_router(api_router)
app.include_router(pages.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/pages/")

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Сервер работает!"}