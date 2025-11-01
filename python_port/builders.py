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
    Map a string type hint (optionally suffixed with '?') to the corresponding Python type.
    
    Parameters:
        type_hint (str): A type hint string from a blueprint; may include a trailing '?' to indicate nullable.
    
    Returns:
        The Python type corresponding to the hint if known (from PYTHON_TYPE_NAMESPACE), otherwise `typing.Any`.
    """
    origin = type_hint.replace("?", "")
    if origin in PYTHON_TYPE_NAMESPACE:
        return PYTHON_TYPE_NAMESPACE[origin]
    return Any


def build_class(blueprint: ClassBlueprint) -> type:
    """
    Create a Python dataclass type that mirrors the structure described by the given ClassBlueprint.
    
    The resulting class includes fields and a class docstring from the blueprint; any methods from the blueprint are attached as stubs that raise NotImplementedError when called.
    
    Parameters:
        blueprint (ClassBlueprint): Blueprint describing the class name, fields, methods, and documentation.
    
    Returns:
        type: A new dataclass type constructed from the blueprint.
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
            Placeholder method that indicates a blueprint-declared method has not been implemented in the Python port.
            
            Parameters:
                _method_name (str): The original method name from the blueprint used in the error message.
            
            Raises:
                NotImplementedError: Always raised with a message stating that `_method_name` is not implemented.
            """
            raise NotImplementedError(f"Method {_method_name} is not implemented in the Python port yet")

        setattr(cls, method.name, _method_stub)
    return cls


def build_enum(blueprint: EnumBlueprint) -> type:
    """
    Constructs a Python Enum type from EnumBlueprint metadata.
    
    Each entry in the blueprint's values becomes an enum member. If a value has no arguments the member's value is the member name; if it has arguments the member's value is a tuple of those arguments.
    
    Parameters:
        blueprint (EnumBlueprint): Metadata describing the enum name and its values.
    
    Returns:
        type: An Enum subclass whose members mirror the blueprint's values (member value is the name or a tuple of arguments).
    """

    enum_members = {value.name: value.name if not value.arguments else tuple(value.arguments) for value in blueprint.values}
    return Enum(blueprint.name, enum_members)  # type: ignore[misc]