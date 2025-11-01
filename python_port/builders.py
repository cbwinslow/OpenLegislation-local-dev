"""Utilities that materialise dataclasses and enums from blueprint metadata."""

from __future__ import annotations

from dataclasses import dataclass, field, make_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Iterable, Tuple

from .blueprints import ClassBlueprint, EnumBlueprint, FieldBlueprint, JAVA_TO_PYTHON_TYPE_MAP


PYTHON_TYPE_NAMESPACE: Dict[str, Any] = {
    "int": int,
    "float": float,
    "bool": bool,
    "str": str,
    "Decimal": Decimal,
    "date": date,
    "datetime": datetime,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
}


def _resolve_type(type_hint: str) -> Any:
    origin = type_hint.replace("?", "")
    if origin in PYTHON_TYPE_NAMESPACE:
        return PYTHON_TYPE_NAMESPACE[origin]
    return Any


def build_class(blueprint: ClassBlueprint) -> type:
    """Create a dataclass that mirrors a Java POJO definition."""

    fields: Iterable[Tuple[str, type, field]] = []
    field_specs = []
    for field_blueprint in blueprint.fields:
        annotation = _resolve_type(field_blueprint.type_hint)
        default_value = field(default=None) if field_blueprint.default is None else field(default=field_blueprint.default)
        field_specs.append((field_blueprint.name, annotation, default_value))
    cls = make_dataclass(blueprint.name, field_specs, bases=tuple(), namespace={"__doc__": blueprint.doc or ""})
    for method in blueprint.methods:
        def _method_stub(self, *args, _method_name=method.name, **kwargs):  # type: ignore[override]
            raise NotImplementedError(f"Method {_method_name} is not implemented in the Python port yet")

        setattr(cls, method.name, _method_stub)
    return cls


def build_enum(blueprint: EnumBlueprint) -> type:
    """Create a Python Enum equivalent for a Java enum definition."""

    enum_members = {value.name: value.name if not value.arguments else tuple(value.arguments) for value in blueprint.values}
    return Enum(blueprint.name, enum_members)  # type: ignore[misc]
