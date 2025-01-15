from functools import singledispatchmethod
from typing import NamedTuple

import sqlalchemy as sq
from sqlalchemy import Select
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression, UnaryExpression

from server.models import ORM_MODEL


class OrderingField(NamedTuple):
    field: str
    direction: str


class Filter:
    _searching_fields = {
        "User": ("username",),
        "Advertisement": ("title", "description", "price"),
    }

    def __init__(self, model: ORM_MODEL, search_by: str = None, order_by: str = None):
        self._model = model
        self._model_columns = self._model.__table__.columns
        self._base_query: Select = sq.select(self._model)
        self._search_param = search_by
        self._ordering_fields = order_by
        self._searching_fields: tuple = self._searching_fields[self._model.__tablename__]

    @singledispatchmethod
    def _get_expression(self, search_param, field):
        raise NotImplementedError(f"Not implemented for {type(field)}")

    @_get_expression.register
    def _(self, search_param: str, field: InstrumentedAttribute) -> BinaryExpression:
        return field.icontains(search_param)

    @_get_expression.register
    def _(self, search_param: int, field: InstrumentedAttribute) -> BinaryExpression:
        return field == int(search_param)

    def _validate_order_filed(self, field: str) -> OrderingField | None:
        if field[0] == "-":
            direction, tmp_field = "desc", field[1:]
        elif field[0] == "+":
            direction, tmp_field = "asc", field[1:]
        else:
            direction, tmp_field = "asc", field
        if tmp_field in self._model_columns:
            return OrderingField(tmp_field, direction)

    def _validate_search_param_type(
        self, search_param: str, field_type: str | int
    ) -> str | int | None:
        if not isinstance(search_param, field_type):
            try:
                search_param = field_type(search_param)
            except ValueError:
                return
        return search_param

    @property
    def _filter_conditions(self) -> list[BinaryExpression]:
        conditions = []
        for field in self._searching_fields:
            field: InstrumentedAttribute = getattr(self._model, field)
            field_type: str | int = field.type.python_type
            valid_search_param: str | int | None = self._validate_search_param_type(
                self._search_param, field_type
            )
            if valid_search_param is None:
                continue
            conditions.append(self._get_expression(valid_search_param, field))
        return conditions

    @property
    def _ordering_conditions(self) -> list[InstrumentedAttribute | UnaryExpression]:
        conditions = []
        fields = [field.strip() for field in self._ordering_fields.split(",")]
        for field in fields:
            validated_field: OrderingField | None = self._validate_order_filed(field=field)
            if validated_field is None:
                continue
            expression: InstrumentedAttribute = getattr(self._model, validated_field.field)
            if validated_field.direction == "desc":
                expression = expression.desc()
            conditions.append(expression)
        return conditions

    @property
    def select_expression(self) -> Select:
        expression = self._base_query
        if self._search_param is not None and (conditions := self._filter_conditions):
            expression = expression.where(sq.or_(False, *conditions))
        if self._ordering_fields is not None and (conditions := self._ordering_conditions):
            expression = expression.order_by(*conditions)
        return expression
