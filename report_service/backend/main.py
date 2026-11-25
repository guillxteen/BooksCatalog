"""HTTP-сервис статистического отчёта по каталогу книг."""

import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel


MAIN_SERVICE_URL = os.getenv("MAIN_SERVICE_URL", "http://localhost:8000").rstrip("/")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="BooksCatalog Report Service",
    description="Получает каталог основного сервиса по HTTP и подсчитывает статусы книг.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


class CatalogReport(BaseModel):
    total: int
    read: int
    unread: int


class HealthResponse(BaseModel):
    status: str


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


def summarize_books(books: list[dict]) -> CatalogReport:
    read = sum(1 for book in books if book.get("is_read") is True)
    return CatalogReport(total=len(books), read=read, unread=len(books) - read)


@app.get(
    "/api/report",
    response_model=CatalogReport,
    tags=["Отчёты"],
    summary="Получить статистику каталога",
)
async def catalog_report():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MAIN_SERVICE_URL}/api/books")
            response.raise_for_status()
            books = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail="Основной сервис временно недоступен. Повторите попытку позже.",
        ) from error

    if not isinstance(books, list) or not all(
        isinstance(book, dict) and isinstance(book.get("is_read"), bool)
        for book in books
    ):
        raise HTTPException(status_code=502, detail="Основной сервис вернул неверный формат данных")
    return summarize_books(books)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Служебные"],
    summary="Проверить сервис отчётов",
)
def health():
    return HealthResponse(status="ok")

