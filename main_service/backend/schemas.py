from sqlmodel import Field, SQLModel


class AuthorCreate(SQLModel):
    name: str = Field(min_length=1, max_length=200, description="Имя автора")
    biography: str = Field(default="", max_length=5000, description="Краткая справка")


class AuthorRead(AuthorCreate):
    id: int


class BookCreate(SQLModel):
    title: str = Field(min_length=1, max_length=300, description="Название книги")
    publication_year: int = Field(ge=0, le=2100, description="Год издания")
    description: str = Field(default="", max_length=10000, description="Краткое описание")
    is_read: bool = Field(default=False, description="Отметка о прочтении")
    author_ids: list[int] = Field(min_length=1, description="Идентификаторы авторов")


class BookRead(SQLModel):
    id: int
    title: str
    publication_year: int
    description: str
    is_read: bool
    authors: list[AuthorRead]


class ReadStatusUpdate(SQLModel):
    is_read: bool


class HealthResponse(SQLModel):
    status: str

