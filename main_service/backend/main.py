from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import create_db_and_tables
from .errors import register_error_handlers
from .routers import authors, books
from .schemas import HealthResponse


FRONTEND_DIR = Path(__file__).parents[1] / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="BooksCatalog API",
    description=(
        "Основной сервис курсового проекта: управление книгами и авторами, "
        "поиск по названию и автору, фильтрация по году и статусу прочтения."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)
app.include_router(authors.router)
app.include_router(books.router)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/health", response_model=HealthResponse, tags=["Служебные"], summary="Проверить основной сервис")
def health():
    return HealthResponse(status="ok")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

