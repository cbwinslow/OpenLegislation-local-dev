#!/usr/bin/env python3
"""Generate Python port blueprints from the Java source tree."""

from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from python_port.blueprints import ClassBlueprint, EnumBlueprint, EnumValue, FieldBlueprint, MethodBlueprint

if importlib.util.find_spec("javalang") is None:  # pragma: no cover - dependency check
    raise SystemExit("The 'javalang' package is required. Install it with 'pip install javalang'.")

import javalang  # type: ignore[import]


def _type_to_string(node: Optional[javalang.tree.Type]) -> str:
    if node is None:
        return "Any"
    name = getattr(node, "name", None)
    if isinstance(name, list):
        base = ".".join(name)
    else:
        base = name or "Any"
    arguments = getattr(node, "arguments", None) or []
    if arguments:
        arg_names = [getattr(arg.type, "name", "Any") for arg in arguments if getattr(arg, "type", None)]
        return f"{base}[{', '.join(arg_names)}]"
    return base


def _extract_class(package: str, declaration: javalang.tree.ClassDeclaration) -> ClassBlueprint:
    fields: List[FieldBlueprint] = []
    for field in declaration.fields:
        type_hint = _type_to_string(field.type)
        for declarator in field.declarators:
            fields.append(FieldBlueprint(name=declarator.name, type_hint=type_hint))
    methods: List[MethodBlueprint] = []
    for method in declaration.methods:
        parameters = [param.name for param in method.parameters]
        return_type = _type_to_string(method.return_type)
        methods.append(MethodBlueprint(name=method.name, parameters=parameters, return_type=return_type))
    bases = [base.name for base in declaration.extends or []]
    return ClassBlueprint(
        name=declaration.name,
        package=package,
        fields=fields,
        methods=methods,
        bases=bases,
    )


def _extract_enum(package: str, declaration: javalang.tree.EnumDeclaration) -> EnumBlueprint:
    values: List[EnumValue] = []
    for constant in declaration.constants:
        arguments = [str(arg) for arg in constant.arguments or []]
        values.append(EnumValue(name=constant.name, arguments=arguments))
    return EnumBlueprint(name=declaration.name, package=package, values=values)


def parse_java_file(path: Path) -> Dict[str, List[Dict[str, str]]]:
    source = path.read_text(encoding="utf-8")
    tree = javalang.parse.parse(source)
    package = tree.package.name if tree.package else ""
    classes: List[ClassBlueprint] = []
    enums: List[EnumBlueprint] = []
    for type_decl in tree.types:
        if isinstance(type_decl, javalang.tree.ClassDeclaration):
            classes.append(_extract_class(package, type_decl))
        elif isinstance(type_decl, javalang.tree.EnumDeclaration):
            enums.append(_extract_enum(package, type_decl))
    return {"classes": classes, "enums": enums}


def build_blueprints(java_root: Path) -> Dict[str, List[Dict[str, str]]]:
    aggregate_classes: List[ClassBlueprint] = []
    aggregate_enums: List[EnumBlueprint] = []
    for java_file in java_root.rglob("*.java"):
        result = parse_java_file(java_file)
        aggregate_classes.extend(result["classes"])
        aggregate_enums.extend(result["enums"])
    return {
        "classes": [asdict(cls) for cls in aggregate_classes],
        "enums": [asdict(enum) for enum in aggregate_enums],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java-root", type=Path, default=Path("src/main/java"), help="Path to the Java source tree")
    parser.add_argument("--output", type=Path, default=Path("python_port/blueprints.json"), help="Destination JSON path")
    args = parser.parse_args()

    blueprints = build_blueprints(args.java_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(blueprints, indent=2), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
