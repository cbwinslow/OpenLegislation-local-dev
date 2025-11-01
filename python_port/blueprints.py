"""Lightweight data structures that describe the Python port of Java models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


JAVA_TO_PYTHON_TYPE_MAP: Dict[str, str] = {
    "int": "int",
    "long": "int",
    "short": "int",
    "byte": "int",
    "double": "float",
    "float": "float",
    "boolean": "bool",
    "char": "str",
    "String": "str",
    "BigDecimal": "Decimal",
    "LocalDate": "date",
    "LocalDateTime": "datetime",
    "Instant": "datetime",
}


@dataclass
class FieldBlueprint:
    name: str
    type_hint: str
    default: Optional[str] = None
    doc: Optional[str] = None


@dataclass
class MethodBlueprint:
    name: str
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    doc: Optional[str] = None


@dataclass
class ClassBlueprint:
    name: str
    package: str
    fields: List[FieldBlueprint] = field(default_factory=list)
    methods: List[MethodBlueprint] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    doc: Optional[str] = None

    @property
    def qualified_name(self) -> str:
        """
        Fully qualified name combining the package and the entity name.
        
        Returns:
            The fully qualified name as "package.name" if `package` is non-empty, otherwise just `name`.
        """
        return f"{self.package}.{self.name}" if self.package else self.name


@dataclass
class EnumValue:
    name: str
    arguments: List[str] = field(default_factory=list)


@dataclass
class EnumBlueprint:
    name: str
    package: str
    values: List[EnumValue] = field(default_factory=list)
    doc: Optional[str] = None

    @property
    def qualified_name(self) -> str:
        """
        Fully qualified name combining the package and the entity name.
        
        Returns:
            The fully qualified name as "package.name" if `package` is non-empty, otherwise just `name`.
        """
        return f"{self.package}.{self.name}" if self.package else self.name