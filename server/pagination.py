from math import ceil
from typing import TypeAlias
from urllib.parse import parse_qs, urlencode, urlparse

from sqlalchemy import Select

from server.config import VALUES_ON_PAGE


class Paginator:
    """Класс пагинации результатов запроса в базу данных

    Количество выводимых записей на одной странице задается параметром server.config.VALUES_ON_PAGE.
    Выбор необходимой страницы задается в query-string с помощью параметра 'page'.
    При отсутствии параметра 'page' в query-string выводится первая страница.
    При параметре 'page' превышающем количество существующих страниц выводится последняя страница.
    Для корректной выдачи результатов, необходимо явно определить общее количество
        доступных записей в атрибуте quantity_objects
            paginator = Paginator(...)
            paginator.quantity_objects = ...
            query = paginator.paginate_query(query)

    :url: URL по которому осуществлен HTTP-запрос
    :pagination_params: словарь с параметрами query-string, опционально содержащий ключ 'page'
    """

    def __init__(self, url: str, pagination_params: dict):
        self.quantity_objects: int = None
        self._page: int = pagination_params.get("page", 1)
        self._limit: int = VALUES_ON_PAGE
        self._last_page: int = None
        self._url: str = url

    def _calculate_offset(self) -> int:
        """Метод расчета смещения

        :return int: смещение, соответствующее заданной странице
        """
        if self.quantity_objects is None:
            raise TypeError("Attribute quantity_objects not defined")
        self._last_page: int = ceil(self.quantity_objects / self._limit)
        if self._page > self._last_page:
            self._page = self._last_page
        self._offset = (self._page - 1 if self._page > 0 else 0) * self._limit
        return self._offset

    def paginate_query(self, query: Select) -> Select:
        """Метод преобразования объекта запроса, добавляющий условия пагинации

        :param Select query: объект запрос
        :return Select: преобразованный объект запроса
        """
        offset = self._calculate_offset()
        return query.limit(self._limit).offset(offset)

    def get_paginated_page(self, values: list) -> dict:
        self._validate_url()
        return {
            "quantity": self.quantity_objects,
            "current_page": self._page,
            "previous": self._get_url(self._page - 1),
            "next": self._get_url(self._page + 1),
            "results": values,
        }

    def _get_url(self, page: int) -> str:
        """Метод преобразования URL

        Осуществляет замену параметра query-string 'page'.

        :param int page: номер страницы
        :return str: преобразованный URL
        """
        return (
            self._url.replace(f"page={self._page}", f"page={page}")
            if 1 <= page <= self._last_page
            else None
        )

    def _validate_url(self):
        """Метод преобразования URL

        Проверяет и преобразует параметр query-string 'page' реальному значению.
        """
        parsed_url = urlparse(self._url)
        qs = parse_qs(parsed_url.query)
        qs["page"] = self._page
        new_qs = urlencode(query=qs, doseq=True)
        self._url = parsed_url._replace(query=new_qs).geturl()


PAGINATOR_CLASS: TypeAlias = Paginator
