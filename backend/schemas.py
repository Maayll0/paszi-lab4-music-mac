
import re

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    login: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9._-]+$",
    )
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Добавьте заглавную латинскую букву")

        if not re.search(r"[a-z]", value):
            raise ValueError("Добавьте строчную латинскую букву")

        if not re.search(r"[0-9]", value):
            raise ValueError("Добавьте цифру")

        if not re.search(r"[^a-zA-Z0-9]", value):
            raise ValueError("Добавьте специальный символ")

        return value
