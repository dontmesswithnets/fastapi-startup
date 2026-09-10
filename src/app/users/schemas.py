import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field


def normalize_email(v: Any) -> Any:
    if isinstance(v, str):
        return v.strip().lower()
    return v


NormalizedEmail = Annotated[EmailStr, BeforeValidator(normalize_email)]


class UserBase(BaseModel):
    email: NormalizedEmail


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=64)


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
