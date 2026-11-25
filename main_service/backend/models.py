from sqlmodel import Field, Relationship, SQLModel


class BookAuthorLink(SQLModel, table=True):
    __tablename__ = "book_authors"

    book_id: int = Field(foreign_key="books.id", primary_key=True)
    author_id: int = Field(foreign_key="authors.id", primary_key=True)


class Author(SQLModel, table=True):
    __tablename__ = "authors"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=200, index=True)
    biography: str = Field(default="", max_length=5000)

    books: list["Book"] = Relationship(
        back_populates="authors",
        link_model=BookAuthorLink,
    )


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=300, index=True)
    publication_year: int = Field(ge=0, le=2100, index=True)
    description: str = Field(default="", max_length=10000)
    is_read: bool = Field(default=False, index=True)

    authors: list[Author] = Relationship(
        back_populates="books",
        link_model=BookAuthorLink,
    )

