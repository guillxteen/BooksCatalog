from fastapi import HTTPException
from sqlmodel import Session, select

from .models import Author, Book


def clean_required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail=f"Поле «{field_name}» не может быть пустым")
    return cleaned


def get_author_or_404(author_id: int, session: Session) -> Author:
    author = session.get(Author, author_id)
    if author is None:
        raise HTTPException(status_code=404, detail="Автор не найден")
    return author


def get_book_or_404(book_id: int, session: Session) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return book


def resolve_authors(author_ids: list[int], session: Session) -> list[Author]:
    unique_ids = list(dict.fromkeys(author_ids))
    if not unique_ids:
        raise HTTPException(status_code=422, detail="Укажите хотя бы одного автора")

    authors = list(session.exec(select(Author).where(Author.id.in_(unique_ids))).all())
    if len(authors) != len(unique_ids):
        found_ids = {author.id for author in authors}
        missing_ids = [author_id for author_id in unique_ids if author_id not in found_ids]
        raise HTTPException(
            status_code=422,
            detail=f"Авторы с идентификаторами {missing_ids} не найдены",
        )
    return authors


def filter_books_case_insensitive(books: list[Book], search: str | None) -> list[Book]:
    if not search or not search.strip():
        return books

    needle = search.strip().casefold()
    return [
        book
        for book in books
        if needle in book.title.casefold()
        or any(needle in author.name.casefold() for author in book.authors)
    ]

