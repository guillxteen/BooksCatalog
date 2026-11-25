from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models import Author
from ..schemas import AuthorCreate, AuthorRead
from ..services import clean_required_text, get_author_or_404


router = APIRouter(prefix="/api/authors", tags=["Авторы"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[AuthorRead], summary="Получить каталог авторов")
def list_authors(session: SessionDep):
    return session.exec(select(Author).order_by(Author.name)).all()


@router.post("", response_model=AuthorRead, status_code=201, summary="Добавить автора")
def create_author(payload: AuthorCreate, session: SessionDep):
    author = Author(
        name=clean_required_text(payload.name, "Имя"),
        biography=payload.biography.strip(),
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


@router.put("/{author_id}", response_model=AuthorRead, summary="Изменить автора")
def update_author(author_id: int, payload: AuthorCreate, session: SessionDep):
    author = get_author_or_404(author_id, session)
    author.name = clean_required_text(payload.name, "Имя")
    author.biography = payload.biography.strip()
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


@router.delete("/{author_id}", status_code=204, summary="Удалить автора")
def delete_author(author_id: int, session: SessionDep):
    author = get_author_or_404(author_id, session)
    if author.books:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить автора, пока с ним связаны книги",
        )
    session.delete(author)
    session.commit()

