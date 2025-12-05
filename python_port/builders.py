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
    """
    Resolve a string type hint to a Python type from the module's type namespace.
    
    Args:
        type_hint (str): A type hint string; a trailing '?' (nullable marker) is ignored.
    
    Returns:
        Any: The corresponding Python type from PYTHON_TYPE_NAMESPACE if found; otherwise `typing.Any`.
    """
    origin = type_hint.replace("?", "")
    if origin in PYTHON_TYPE_NAMESPACE:
        return PYTHON_TYPE_NAMESPACE[origin]
    return Any


def build_class(blueprint: ClassBlueprint) -> type:
    """
    Build a Python dataclass that represents the given ClassBlueprint.
    
    Creates a new dataclass type whose fields and their annotations reflect the blueprint.
    The resulting class will include method stubs for each blueprint method that raise
    NotImplementedError when invoked.
    
    Args:
        blueprint (ClassBlueprint): Blueprint describing the class name, fields, methods,
            and optional documentation to use for the dataclass.
    
    Returns:
        type: The constructed dataclass type corresponding to the blueprint.
    
    Side effects:
        Attaches NotImplementedError-raising method stubs to the created class for every
        method listed in the blueprint.
    """

    fields: Iterable[Tuple[str, type, field]] = []
    field_specs = []
    for field_blueprint in blueprint.fields:
        annotation = _resolve_type(field_blueprint.type_hint)
        default_value = field(default=None) if field_blueprint.default is None else field(default=field_blueprint.default)
        field_specs.append((field_blueprint.name, annotation, default_value))
    cls = make_dataclass(blueprint.name, field_specs, bases=tuple(), namespace={"__doc__": blueprint.doc or ""})
    for method in blueprint.methods:
        def _method_stub(self, *args, _method_name=method.name, **kwargs):  # type: ignore[override]
            """
            Attachable method stub that raises a NotImplementedError indicating the original blueprint method is not implemented.
            
            Args:
                self: Instance the stub is bound to.
                *args: Positional arguments accepted by the stub and ignored.
                **kwargs: Keyword arguments accepted by the stub and ignored.
                _method_name (str): Name of the blueprint method this stub represents (used only in the error message).
            
            Raises:
                NotImplementedError: Always raised with a message stating that `_method_name` is not implemented in the Python port.
            """
            raise NotImplementedError(f"Method {_method_name} is not implemented in the Python port yet")

        setattr(cls, method.name, _method_stub)
    return cls


def build_enum(blueprint: EnumBlueprint) -> type:
    """
    Create a Python Enum type that corresponds to an EnumBlueprint.
    
    Each entry in `blueprint.values` becomes an enum member whose value is the original
    value name when there are no arguments, or a tuple of the value's arguments when present.
    
    Args:
        blueprint (EnumBlueprint): Blueprint describing the enum name and its values.
    
    Returns:
        type: A new Enum subclass with members defined from the blueprint.
    
    Raises:
        ValueError: If `blueprint.name` is not a valid identifier for an enum type.
    """

    enum_members = {value.name: value.name if not value.arguments else tuple(value.arguments) for value in blueprint.values}
    return Enum(blueprint.name, enum_members)  # type: ignore[misc]