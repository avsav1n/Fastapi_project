from itertools import batched
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urlparse


class Paginator:
    def __init__(self, sequence: Iterable, values_on_page: int, url: str):
        self._sequence = sequence
        self._values_on_page = values_on_page
        self._url = url
        self._paginated_pages = self._paginate_sequence()
        self._last_page = len(self._paginated_pages)
        self._first_page = 1

    def _paginate_sequence(self) -> dict[int, tuple]:
        pages = {}
        for i, page in enumerate(batched(self._sequence, self._values_on_page), start=1):
            pages[i] = page
        return pages

    def _get_page(self, page: int) -> dict:
        previous_page: str | None = (
            self._url.replace(f"page={page}", f"page={page - 1}")
            if self._paginated_pages.get(page - 1)
            else None
        )
        next_page: str | None = (
            self._url.replace(f"page={page}", f"page={page + 1}")
            if self._paginated_pages.get(page + 1)
            else None
        )
        return {
            "quantity": len(self._sequence),
            "current": page,
            "previous": previous_page,
            "next": next_page,
            "results": self._paginated_pages.get(page, []),
        }

    def _prepare_url(self, valid_page: int, page: int):
        if "page=" in self._url and self._first_page <= page <= self._last_page:
            return
        parsed_url = urlparse(self._url)
        qs = parse_qs(parsed_url.query)
        qs["page"] = valid_page
        new_qs = urlencode(query=qs, doseq=True)
        self._url = parsed_url._replace(query=new_qs).geturl()

    def _validate_page(self, page: int) -> int:
        if page <= 0:
            valid_page = self._first_page
        elif page > self._last_page:
            valid_page = self._last_page
        else:
            valid_page = page
        self._prepare_url(valid_page=valid_page, page=page)
        return valid_page

    def get_page(self, page: int = 1) -> dict:
        valid_page = self._validate_page(page=page)
        return self._get_page(page=valid_page)
