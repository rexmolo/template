from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class Envelope(BaseModel, Generic[T]):
    data: T | None = None
    error: ErrorBody | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


def ok(data: T, meta: dict[str, Any] | None = None) -> Envelope[T]:
    return Envelope(data=data, meta=meta or {})
