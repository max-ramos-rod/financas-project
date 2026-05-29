from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class PagedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PageMeta
