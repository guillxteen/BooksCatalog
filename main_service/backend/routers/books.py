from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from ..database import get_session
from ..models import Book
from ..schemas import BookCreate, BookRead, ReadStatusUpdate
from ..services import (
    clean_required_text,
    filter_books_case_insensitive,
    get_book_or_404,
    resolve_authors,
)


router = APIRouter(prefix="/api/books", tags=["Книги"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[BookRead], summary="Получить каталог книг")
def list_books(
    session: SessionDep,
    search: str | None = Query(default=None, max_length=200, description="Часть названия или имени автора"),
    year: int | None = Query(default=None, ge=0, le=2100, description="Год издания"),
    is_read: bool | None = Query(default=None, description="Отметка о прочтении"),
):
    statement = select(Book).distinct()
    if year is not None:
        statement = statement.where(Book.publication_year == year)
    if is_read is not None:
        statement = statement.where(Book.is_read == is_read)

    books = list(session.exec(statement.order_by(Book.title)).all())
    return filter_books_case_insensitive(books, search)


@router.get("/{book_id}", response_model=BookRead, summary="Получить карточку книги")
def get_book(book_id: int, session: SessionDep):
    return get_book_or_404(book_id, session)


@router.post("", response_model=BookRead, status_code=201, summary="Добавить книгу")
def create_book(payload: BookCreate, session: SessionDep):
    book = Book(
        title=clean_required_text(payload.title, "Название"),
        publication_year=payload.publication_year,
        description=payload.description.strip(),
        is_read=payload.is_read,
        authors=resolve_authors(payload.author_ids, session),
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.put("/{book_id}", response_model=BookRead, summary="Изменить книгу")
def update_book(book_id: int, payload: BookCreate, session: SessionDep):
    book = get_book_or_404(book_id, session)
    book.title = clean_required_text(payload.title, "Название")
    book.publication_year = payload.publication_year
    book.description = payload.description.strip()
    book.is_read = payload.is_read
    book.authors = resolve_authors(payload.author_ids, session)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.patch("/{book_id}/read-status", response_model=BookRead, summary="Изменить статус прочтения")
def change_read_status(book_id: int, payload: ReadStatusUpdate, session: SessionDep):
    book = get_book_or_404(book_id, session)
    book.is_read = payload.is_read
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{book_id}", status_code=204, summary="Удалить книгу")
def delete_book(book_id: int, session: SessionDep):
    book = get_book_or_404(book_id, session)
    session.delete(book)
    session.commit()

