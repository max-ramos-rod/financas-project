from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, Field

from app.core.pagination import PageMeta

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    data: T
    meta: dict[str, Any] = Field(default_factory=dict)


class PaginatedResponseEnvelope(BaseModel, Generic[T]):
    data: List[T]
    meta: PageMeta


PagedResponse = PaginatedResponseEnvelope


def success_response(data: Any, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return ResponseEnvelope[Any](data=data, meta=meta or {}).model_dump(mode="json")


def paginated_response(data: Any, meta: PageMeta) -> dict[str, Any]:
    return PaginatedResponseEnvelope[Any](data=data, meta=meta).model_dump(mode="json")
