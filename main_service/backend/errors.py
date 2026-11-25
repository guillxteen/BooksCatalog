from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


FIELD_NAMES = {
    "title": "Название",
    "publication_year": "Год издания",
    "description": "Описание",
    "author_ids": "Авторы",
    "name": "Имя",
    "biography": "Краткая справка",
    "is_read": "Статус прочтения",
    "year": "Год",
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError):
        messages: list[str] = []
        for error in exc.errors():
            field = str(error.get("loc", ["данные"])[-1])
            label = FIELD_NAMES.get(field, field)
            error_type = error.get("type", "")
            if error_type == "missing":
                message = "поле обязательно"
            elif error_type == "string_too_short":
                message = "значение слишком короткое"
            elif error_type == "string_too_long":
                message = "значение слишком длинное"
            elif error_type in {"greater_than_equal", "less_than_equal"}:
                message = "значение вне допустимого диапазона"
            else:
                message = "некорректное значение"
            messages.append(f"{label}: {message}")

        return JSONResponse(
            status_code=422,
            content={"detail": "; ".join(messages)},
        )

