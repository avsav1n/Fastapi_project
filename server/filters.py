from abc import ABC, abstractmethod
from functools import singledispatchmethod
from typing import NamedTuple, TypeAlias

import sqlalchemy as sq
from sqlalchemy import Select
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from server.models import ORM_MODEL


class OrderingField(NamedTuple):
    field: str
    direction: str


class BaseFilter(ABC):
    """Базовый класс для классов-фильтрации"""

    @abstractmethod
    def get_filter_conditions(self) -> list:
        pass


class SearchFilter(BaseFilter):
    """Класс фильтрации, осуществляющий поиск по контексту заданных полей ORM-моделей

    Выбор значения по которому осуществляется фильтрация задается в query-string с помощью
        параметра 'search'.

    :model: ORM-модель, к которой осуществляется запрос
    :search_fields: поля ORM-модели, по которым проводится поиск
    :searching_param: параметр фильтрации, переданный в query-string
    """

    def __init__(self, model: ORM_MODEL, search_fields: tuple[str], searching_param: str | None):
        self._model: ORM_MODEL = model
        self._search_fields: tuple[str] = search_fields
        self._searching_param: str | None = searching_param

    @singledispatchmethod
    def _get_condition(self, search_param):
        """Метод одиночной диспетчеризации"""
        raise NotImplementedError(f"Not implemented for {type(search_param)}")

    @_get_condition.register
    def _(self, search_param: str, field: InstrumentedAttribute) -> BinaryExpression:
        """Обработчик метода одиночной диспетчеризации

        :param str search_param: значение параметра поиска типа STR
        :param InstrumentedAttribute field: поле поиска
        :return BinaryExpression: условие SQLAlchemy для использования в where фильтре
        """
        return field.icontains(search_param)

    @_get_condition.register
    def _(self, search_param: int, field: InstrumentedAttribute) -> BinaryExpression:
        """Обработчик метода одиночной диспетчеризации

        :param str search_param: значение параметра поиска типа INT
        :param InstrumentedAttribute field: поле поиска
        :return BinaryExpression: условие фильтрации
        """
        return field == int(search_param)

    def _convert_searching_param(
        self, search_param: str, field_type: str | int
    ) -> str | int | None:
        """Метод пребразования значения параметра поиска в тип, соответствующий типу поля ORM-модели

        :param str search_param: значение параметра поиска типа STR
        :param str | int field_type: тип поля ORM-модели
        :return str | int | None: значение параметра поиска, соответствующее типу поля ORM-модели
            или None
        """
        if not isinstance(search_param, field_type):
            try:
                search_param: int = field_type(search_param)
            except ValueError:
                return
        return search_param

    def get_filter_conditions(self) -> list[BinaryExpression]:
        """Метод формирования условий фильтрации

        :return list[BinaryExpression]: список условий
        """
        conditions = []
        if self._searching_param is not None:
            for field in self._search_fields:
                field: InstrumentedAttribute = getattr(self._model, field)
                field_type: str | int = field.type.python_type
                search_param: str | int | None = self._convert_searching_param(
                    self._searching_param, field_type
                )
                if search_param is None:
                    continue
                conditions.append(self._get_condition(search_param, field))
        else:
            conditions.append(True)
        return conditions


class OrderingFilter(BaseFilter):
    """Класс фильтрации, осуществляющий упорядочивание результатов по полям ORM-моделей

    Выбор значения по которому осуществляется упорядочивание задается в query-string с помощью
        параметра 'order_by'.
    Класс поддерживание последовательное указание нескольких полей подряд через запятую:
        http://localhost:8000/advertisement/order_by=id,-title

    :model: ORM-модель, к которой осуществляется запрос
    :ordering_params: параметры упорядочивания, переданные в query-string
    """

    def __init__(self, model: ORM_MODEL, ordering_params: tuple[str] | None):
        self._model: ORM_MODEL = model
        self._ordering_params: tuple[str] | None = ordering_params

    def _check_field(self, field: str) -> OrderingField | None:
        """Метод валидации и преобразования полученных параметров упорядочивания

        :param str field: параметр упорядочивания
        :return OrderingField | None: подготовленный параметр упорядочивания или None
        """
        if field[0] == "-":
            direction, tmp_field = "desc", field[1:]
        elif field[0] == "+":
            direction, tmp_field = "asc", field[1:]
        else:
            direction, tmp_field = "asc", field
        if tmp_field in self._model.__table__.columns:
            return OrderingField(tmp_field, direction)

    def get_filter_conditions(self) -> list[InstrumentedAttribute | UnaryExpression]:
        """Метод формирования условий упорядочивания

        :return list[InstrumentedAttribute | UnaryExpression]: список условий
        """
        conditions = []
        if self._ordering_params is not None:
            for field in self._ordering_params:
                validated_field: OrderingField | None = self._check_field(field=field)
                if validated_field is None:
                    continue
                expression: InstrumentedAttribute = getattr(self._model, validated_field.field)
                if validated_field.direction == "desc":
                    expression = expression.desc()
                conditions.append(expression)
        return conditions


class FilterSet:
    """Класс-набор фильтров"""

    search_filter_cls = SearchFilter
    ordering_filter_cls = OrderingFilter

    def __init__(self, model: ORM_MODEL, search_fields: tuple[str], filter_params: dict):
        self._model: ORM_MODEL = model
        self._ordering_params: tuple[str] | None = filter_params.get("order_by")
        self._searching_param: str | None = filter_params.get("search")
        self._search_fields: tuple[str] = search_fields

    @property
    def search_filter(self):
        """Свойство создания объекта self.search_filter_cls

        :return _type_: объект self.search_filter_cls
        """
        return self.search_filter_cls(
            model=self._model,
            search_fields=self._search_fields,
            searching_param=self._searching_param,
        )

    @property
    def ordering_filter(self):
        """Свойство создания объекта self.ordering_filter_cls

        :return _type_: объект self.ordering_filter_cls
        """
        return self.ordering_filter_cls(model=self._model, ordering_params=self._ordering_params)

    def filter_query(self, query: Select) -> Select:
        """Метод преобразования объекта запроса, добавляющий условия фильтрации

        :param Select query: объект запроса
        :return Select: преобразованный объект запроса
        """
        return query.where(sq.or_(False, *self.search_filter.get_filter_conditions())).order_by(
            *self.ordering_filter.get_filter_conditions()
        )


FILTERSET_CLASS: TypeAlias = FilterSet
