from dataclasses import dataclass

from fastapi import Query

from src.application.dtos.pagination_dto import DEFAULT_PER_PAGE, MAX_PER_PAGE


@dataclass(frozen=True, slots=True)
class Pagination:
    page: int
    per_page: int


def get_pagination(
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE),
) -> Pagination:
    return Pagination(page=page, per_page=per_page)
