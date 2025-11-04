"""Converts a VBL Aquarium model into a C# struct."""

from __future__ import annotations

from typing import TYPE_CHECKING, get_args, get_origin

from pydantic.alias_generators import to_camel, to_pascal, to_snake

from vbl_aquarium.utils.common import get_unity_model_class_names

if TYPE_CHECKING:
    from vbl_aquarium.utils.vbl_base_model import VBLBaseModel

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


def _generate_csharp_struct(class_name: str, fields: list[str], enum: tuple[str, zip[tuple[str, str]]] | None):
    """Generate a C# struct and enum from parts.

    Args:
        class_name: The name of the class.
        fields: The fields of the class.
        enum: The enum definition used in the class.
    """
    # Build field declarations.
    field_declarations = "\n".join(f"    public {field};" for field in fields)
    constructor_arg = ", ".join(f"{field.split(' ')[0]} {to_camel(to_snake(field.split(' ')[1]))}" for field in fields)
    constructor_assignments = "\n        ".join(
        f"{field.split(' ')[1]} = {to_camel(to_snake(field.split(' ')[1]))};" for field in fields
    )

    # build enum str
    enum_str = ""
    if enum is not None:
        enum_array = "\n".join(f"    {v[0]} = {v[1]}," for v in enum[1])
        enum_str = f"""
public enum {enum[0]}
{{
{enum_array}
}}
"""

    # build the full class file string
    return f"""
[Serializable]
public struct {class_name}
{{
{field_declarations}

    public {class_name}({constructor_arg})
    {{
        {constructor_assignments}
    }}
}}{enum_str}
"""


def _parse_model(model: type[VBLBaseModel]) -> str:
    """Parse a VBLBaseModel into components for C# generation.

    Args:
        model: The model to parse.

    Returns:
        The C# struct as a string.
    """
    # Model parts.
    fields: list[str] = []
    enum: tuple[str, zip[tuple[str, str]]] | None = None

    # Compute model JSON schema.
    model_json_schema = model.model_json_schema()

    # Parse model fields.
    # noinspection PyTypeChecker
    model_field_data: dict[str, FieldInfo] = model.model_fields
    for name, data in model_field_data.items():
        field_data = ""
        field_name = alias if (alias := data.alias) else name

        # Handle enums.
        if data.annotation is not None and "enum" in str(data.annotation):
            # Get the enum parts.
            enum_name: str = data.annotation.__name__
            enum_values: list[str] = model_json_schema["$defs"][enum_name]["enum"]
            enum_keys: list[str] = model_json_schema["properties"][to_pascal(name)]["enum_keys"]

            # Update the enum.
            enum = (enum_name, zip(enum_keys, enum_values))
            field_data = f"{enum_name} {field_name}"

        # Handle bytearrays.
        elif isinstance(data.annotation, bytearray):
            field_data = f"byte[] {field_name}"

        # Handle arrays.
        elif get_origin(data.annotation) == list:
            arg_class: tuple[type, ...] = get_args(data.annotation)
            type_name = arg_class[0].__name__

            # Convert `str` to C# `string`.
            if type_name == "str":
                type_name = "string"

            field_data = f"{type_name}[] {field_name}"

        # Handle base classes.
        elif data.annotation is not None and hasattr(data.annotation, "__name__"):
            type_name = data.annotation.__name__

            # Convert `str` to C# `string`.
            if type_name == "str":
                type_name = "string"

            field_data = f"{type_name} {field_name}"

        # Raise an error if unhandled.
        else:
            raise TypeError("Unhandled field type: " + str(data.annotation))

        # Append the field data.
        fields.append(field_data)

    # Generate the C# struct.
    return _generate_csharp_struct(model.__name__, fields, enum)


def generate_csharp(model_classes: list[type[VBLBaseModel]]) -> str:
    """Generate a C# file containing structs for the given model classes.

    Args:
        model_classes: The model classes to generate C# structs for.

    Returns:
        The C# file as a string.
    """
    # Parse each model class.
    output = ["using System;"] + [_parse_model(model_class) for model_class in model_classes]

    # Add `using UnityEngine;` if Unity classes are present.
    for segment in output:
        if any(unity_class in segment for unity_class in get_unity_model_class_names()):
            output.insert(1, "using UnityEngine;")
            break

    # Return the complete C# file.
    return "\n".join(output)
