"""Runtime helpers for the Python re-implementation of OpenLegislation models.

The module does not eagerly define any models.  Instead it exposes utilities
that materialise dataclass/enum equivalents on demand based on the
``ClassBlueprint`` metadata generated from the Java sources.  This keeps the
committed repository size manageable while still giving downstream tasks a
programmable API surface that mirrors the Java layer.
"""

from .blueprints import ClassBlueprint, EnumBlueprint, FieldBlueprint, MethodBlueprint
from .builders import build_class, build_enum

__all__ = [
    "ClassBlueprint",
    "EnumBlueprint",
    "FieldBlueprint",
    "MethodBlueprint",
    "build_class",
    "build_enum",
]
