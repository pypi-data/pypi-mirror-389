"""Module that validates XML files against an XSD and applies extra custom validation rules.

This module loads an XML Schema (schema.xsd, sibling to this file) using xmlschema.XMLSchema11
and provides some helper functions to validate XML files against it.
"""

import textwrap
from collections.abc import Generator
from pathlib import Path
from typing import Optional, Union
from xml.etree import ElementTree as ET

import xmlschema
from xmlschema.validators import XsdAttributeGroup

schema_file = Path(__file__, "../schema.xsd").resolve()
XSD = xmlschema.XMLSchema11(schema_file)


class ExtraValidator:
    """Validator class that enforces custom cross-element rules inside Cube elements.

    When called during schema validation, this validator inspects elements within a Cube and
    yields xmlschema.XMLSchemaValidationError objects for the following conditions:

    - Multiple Hierarchy or HierarchyUsage elements with the same name/source within the same Cube.
    - Name collisions between Measures/CalculatedMeasures and Level/LevelUsage/Property/PropertyUsage.
      For Level elements, a derived "<name> ID" identifier is also reserved to prevent collisions.

    The validator records the resource (file path or relative path) supplied on construction
    and uses it as the error source.
    """

    def __init__(self, resource: Union[str, Path]) -> None:
        self.resource = resource

    def __call__(self, element: ET.Element, schema_element: xmlschema.XsdElement):
        """Dispatch to element-specific validators when validating the document tree."""
        if schema_element.name == "Cube":
            yield from self.validate_cube(element)

    def validate_cube(self, cube: ET.Element):
        """Validate a Cube element for duplicate/conflicting child names.

        - Collects Hierarchy/HierarchyUsage names and reports duplicates.
        - Collects Measure/CalculatedMeasure names.
        - Ensures Level/LevelUsage/Property/PropertyUsage names do not clash with measure names.
        - Reserves "<level name> ID" for Level elements to avoid accidental collisions.
        """
        cubename = cube.attrib["name"]
        result_names = {}
        hierar_names = {}

        for element in cube.iterfind("Hierarchy, HierarchyUsage"):
            name = element.get("name") or element.attrib["source"]
            obj = f"{element.tag}(name={name!r})"
            if name in hierar_names:
                yield xmlschema.XMLSchemaValidationError(
                    validator=XSD,
                    obj=obj,
                    reason=f"There's multiple {obj} in Cube {cubename!r}",
                    source=self.resource,
                )

        for element in cube.iterfind("Measure, CalculatedMeasure"):
            name = element.attrib["name"]
            obj = f"{element.tag}(name={name!r})"
            result_names[name] = obj

        for element in cube.iterfind("Level, LevelUsage, Property, PropertyUsage"):
            name = element.get("name") or element.attrib["source"]
            obj = f"{element.tag}(name={name!r})"
            if name in result_names:
                yield xmlschema.XMLSchemaValidationError(
                    validator=XSD,
                    obj=obj,
                    reason=f"Name for {obj} in Cube {cubename!r} clashes with {result_names[name]}",
                    source=self.resource,
                )
            result_names[name] = obj
            if element.tag.startswith("Level"):
                result_names[f"{name} ID"] = obj


def validate_schema(target: Path) -> None:
    """Validate a filesystem target against the loaded XSD schema.

    If target is a directory, validate all its .xml files recursively.
    If target is a file, validate just that file.
    Validation errors are printed to stdout prefixed by path.
    """
    if target.is_dir():
        for file in target.glob("**/*.xml"):
            validate_xmlfile(file, target)

    elif target.is_file():
        validate_xmlfile(target)


def validate_xmlfile(file: Path, folder: Optional[Path] = None) -> None:
    """Validate a single XML file with the XSD and the ExtraValidator.

    Resolves the path or produces a path relative to 'folder' (if provided) for error messages,
    constructs an ExtraValidator bound to that path, iterates schema errors (including extras),
    and prints human-readable reasons. Blank line separates multiple errors.
    """
    path = file.resolve() if folder is None else file.relative_to(folder)
    exval = ExtraValidator(str(path))
    errors = [
        "\n".join(_yield_error_str(error))
        for error in XSD.iter_errors(file, extra_validator=exval, use_location_hints=True)
    ]
    if errors:
        print(f"{path}:")
        for error in errors:
            print(textwrap.indent(error, "  "))


def _yield_error_str(error: xmlschema.XMLSchemaValidationError) -> Generator[str, None, None]:
    path = error.path
    sourceline = error.sourceline
    if path:
        yield f"at {path} (line {sourceline})" if sourceline else f"at {path}"

    yield f"{error.message}: {error.reason}" if error.reason else error.message

    if not isinstance(error.validator, XsdAttributeGroup):
        yield error.get_obj_as_string("  ", max_lines=4)

    yield ""
