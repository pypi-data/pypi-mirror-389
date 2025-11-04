import typing
from typing import Any, Optional

from lxml import etree
from pydantic import BaseModel, ConfigDict, create_model

from .utils import convert_to_snake_case, infer_type

_TYPE_MAP: dict[str, type] = {
    "str": str,
    "int": int,
    "bool": bool,
}


class _ConfiguredBase(BaseModel):
    """Base model with configured settings for dynamically created models."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


def _is_nested_structure(element: etree._Element) -> bool:
    """Check if an XML element has a nested structure with Name/Value attributes."""
    for subchild in element:
        if "Name" in subchild.attrib and "Value" in subchild.attrib:
            return True
    return False


def _analyze_xml_structure(
    tree: etree._ElementTree, parent_element: str
) -> tuple[dict[str, int], dict[str, list[str]], dict[str, dict[str, Any]], int]:
    """
    Analyze XML structure and collect field occurrences, values, and nested structures.

    Returns:
        Tuple of (parent_field_occurrences, parent_field_values, nested_structures, total_parents)
    """
    parent_field_occurrences: dict[str, int] = {}
    parent_field_values: dict[str, list[str]] = {}
    nested_structures: dict[str, dict[str, Any]] = {}
    total_parents = 0

    for parent in tree.iter(parent_element):
        total_parents += 1

        for child in parent:
            field_name = child.tag
            parent_field_occurrences[field_name] = (
                parent_field_occurrences.get(field_name, 0) + 1
            )

            if _is_nested_structure(child):
                _track_nested_structure(child, field_name, nested_structures)
            else:
                _track_simple_field(child, field_name, parent_field_values)

    return (
        parent_field_occurrences,
        parent_field_values,
        nested_structures,
        total_parents,
    )


def _track_nested_structure(
    element: etree._Element,
    field_name: str,
    nested_structures: dict[str, dict[str, Any]],
) -> None:
    """Track nested structure parameters for a field."""
    if field_name not in nested_structures:
        nested_structures[field_name] = {
            "count": 0,
            "params": {},
        }

    nested_structures[field_name]["count"] += 1

    for param_element in element:
        if "Name" in param_element.attrib:
            param_name = param_element.attrib["Name"]
            param_value = param_element.attrib.get("Value", "")

            if param_name not in nested_structures[field_name]["params"]:
                nested_structures[field_name]["params"][param_name] = {
                    "count": 0,
                    "values": [],
                }

            nested_structures[field_name]["params"][param_name]["count"] += 1
            nested_structures[field_name]["params"][param_name]["values"].append(
                param_value
            )


def _track_simple_field(
    element: etree._Element,
    field_name: str,
    parent_field_values: dict[str, list[str]],
) -> None:
    """Track simple field values with text content."""
    if element.text:
        if field_name not in parent_field_values:
            parent_field_values[field_name] = []
        parent_field_values[field_name].append(element.text.strip())


def _create_nested_models(
    nested_structures: dict[str, dict[str, Any]],
) -> dict[str, type[BaseModel]]:
    """Create Pydantic models for nested structures."""
    nested_models: dict[str, type[BaseModel]] = {}

    for nested_tag, nested_data in nested_structures.items():
        nested_fields: dict[str, tuple[Any, Any]] = {}
        total_with_nested = nested_data["count"]

        for param_name, param_data in sorted(nested_data["params"].items()):
            values = param_data["values"]
            type_str, is_optional = infer_type(values)
            python_type = _TYPE_MAP.get(type_str, str)

            is_field_optional = param_data["count"] < total_with_nested

            if is_optional or is_field_optional:
                nested_fields[param_name] = (Optional[python_type], None)
            else:
                nested_fields[param_name] = (python_type, ...)

        nested_models[nested_tag] = create_model(
            nested_tag,
            __base__=_ConfiguredBase,
            __module__="xmlu.generator",
            **nested_fields,
        )

    return nested_models


def _create_parent_model(
    parent_element: str,
    parent_field_occurrences: dict[str, int],
    parent_field_values: dict[str, list[str]],
    nested_models: dict[str, type[BaseModel]],
    total_parents: int,
) -> type[BaseModel]:
    """Create the parent Pydantic model."""
    parent_fields: dict[str, tuple[Any, Any]] = {}

    for field_name in sorted(parent_field_occurrences.keys()):
        if field_name in nested_models:
            nested_model = nested_models[field_name]
            is_optional = parent_field_occurrences[field_name] < total_parents

            if is_optional:
                parent_fields[field_name] = (Optional[nested_model], None)
            else:
                parent_fields[field_name] = (nested_model, ...)
        else:
            values = parent_field_values.get(field_name, [])
            type_str, _ = infer_type(values)
            python_type = _TYPE_MAP.get(type_str, str)

            is_optional = parent_field_occurrences[field_name] < total_parents

            if is_optional:
                parent_fields[field_name] = (Optional[python_type], None)
            else:
                parent_fields[field_name] = (python_type, ...)

    return create_model(
        parent_element,
        __base__=_ConfiguredBase,
        __module__="xmlu.generator",
        **parent_fields,
    )


def generate_pydantic_models(
    file_path: str, parent_element: str = "Event"
) -> tuple[type[BaseModel], ...]:
    """
    Generate Pydantic models from XML structure with automatic nesting detection.

    This function analyzes an XML file and creates typed Pydantic models with:
    - Automatic type inference from data values
    - Optional/Required field detection based on occurrence
    - Nested model support for elements with Name/Value parameters
    - Proper model relationships

    Args:
        file_path: Path to the XML file to parse
        parent_element: XML tag name to use as parent model (default: "Event")

    Returns:
        Tuple of Pydantic models: (ParentModel, NestedModel1, NestedModel2, ...)
        First model is always the parent, followed by any detected nested models.

    Example:
        >>> models = generate_pydantic_models("schedule.xml", "Event")
        >>> Event, Fields = models
        >>> event = Event(IsFixed=True, Fields=Fields(Duration="01:00:00"))
    """
    tree = etree.parse(file_path)

    (
        parent_field_occurrences,
        parent_field_values,
        nested_structures,
        total_parents,
    ) = _analyze_xml_structure(tree, parent_element)

    nested_models = _create_nested_models(nested_structures)

    parent_model = _create_parent_model(
        parent_element,
        parent_field_occurrences,
        parent_field_values,
        nested_models,
        total_parents,
    )

    return (parent_model, *nested_models.values())


# ============================================================================
# Model File Generation
# ============================================================================


def format_type_annotation(annotation: Any) -> tuple[str, bool]:
    """
    Convert a Pydantic type annotation to a string representation.

    Args:
        annotation: A Python type annotation (e.g., str, Optional[int], Union[...])

    Returns:
        Tuple of (type_string, is_optional)
        - type_string: String representation like "int", "Optional[str]", etc.
        - is_optional: True if the type is Optional
    """
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is typing.Union:
        # Check if it's Optional (Union[X, None])
        if type(None) in args:
            actual_type = [arg for arg in args if arg is not type(None)][0]
            if hasattr(actual_type, "__name__"):
                return f"Optional[{actual_type.__name__}]", True
            return f"Optional[{actual_type}]", True

        # Regular Union
        type_strs = [
            arg.__name__ if hasattr(arg, "__name__") else str(arg) for arg in args
        ]
        return f"Union[{', '.join(type_strs)}]", False

    if hasattr(annotation, "__name__"):
        return annotation.__name__, False

    return str(annotation), False


def _determine_imports_needed(
    models: list[type[BaseModel]],
) -> tuple[bool, bool]:
    """Determine which imports are needed based on model fields."""
    needs_optional = False
    needs_field_alias = False

    for model in models:
        for field_name, field_info in model.model_fields.items():
            _, is_optional = format_type_annotation(field_info.annotation)
            if is_optional:
                needs_optional = True

            snake_field = convert_to_snake_case(field_name)
            if snake_field != field_name:
                needs_field_alias = True

            if needs_optional and needs_field_alias:
                break
        if needs_optional and needs_field_alias:
            break

    return needs_optional, needs_field_alias


def _write_file_header(
    file_path: str, needs_optional: bool, needs_field_alias: bool
) -> tuple[str, str]:
    """Write file header with docstring and imports. Returns (root_tag, file_name)."""
    tree = etree.parse(file_path)
    root = tree.getroot()
    file_name = root.tag + "_models.py"

    with open(file_name.lower(), "w") as file:
        # Write header docstring
        file.write('"""\n')
        file.write(f"Auto-generated Pydantic models from {root.tag}.xml\n")
        file.write('"""\n')

        # Write imports
        if needs_field_alias:
            file.write("from pydantic import BaseModel, Field, ConfigDict\n")
        else:
            file.write("from pydantic import BaseModel, ConfigDict\n")

        if needs_optional:
            file.write("from typing import Optional\n")

        file.write("\n\n")

    return root.tag, file_name.lower()


def _write_model_class(
    model: type[BaseModel], needs_field_alias: bool, file_handle: Any
) -> None:
    """Write a single model class to the file."""
    file_handle.write(f"class {model.__name__}(BaseModel):\n")

    # Add ConfigDict for better JSON schema generation
    file_handle.write("    model_config = ConfigDict(\n")
    file_handle.write("        str_strip_whitespace=True,\n")
    file_handle.write("        validate_assignment=True,\n")
    file_handle.write(
        "        populate_by_name=True,  # Allow using both snake_case and original names\n"
    )
    file_handle.write("    )\n\n")

    if not model.model_fields:
        file_handle.write("    pass\n\n\n")
        return

    for field_name, field_info in model.model_fields.items():
        snake_field = convert_to_snake_case(field_name)

        # Format type annotation
        type_annotation, is_optional = format_type_annotation(field_info.annotation)

        # Check if we need Field alias
        if snake_field != field_name and needs_field_alias:
            # Use Field with alias
            if is_optional:
                file_handle.write(
                    f'    {snake_field}: {type_annotation} = Field(None, alias="{field_name}")\n'
                )
            else:
                file_handle.write(
                    f'    {snake_field}: {type_annotation} = Field(alias="{field_name}")\n'
                )
        else:
            # No alias needed
            default_value = " = None" if is_optional else ""
            file_handle.write(f"    {snake_field}: {type_annotation}{default_value}\n")

    file_handle.write("\n\n")


def create_models_file(file_path: str, models: list[type[BaseModel]]) -> str:
    """
    Write Pydantic models to a Python file with best practices.

    Generates a .py file containing:
    - Clean imports (only what's needed)
    - Proper docstring header
    - Models with ConfigDict for validation
    - Field aliases for original XML names
    - Type hints for all fields

    Args:
        file_path: Path to source XML file (used to name output file)
        models: List of Pydantic models to write

    Returns:
        Name of the generated file

    Example:
        >>> models = generate_pydantic_models("schedule.xml")
        >>> create_models_file("schedule.xml", list(models))
        'schedule_models.py'
    """
    needs_optional, needs_field_alias = _determine_imports_needed(models)
    _, file_name = _write_file_header(file_path, needs_optional, needs_field_alias)

    # Append models to file (write in reverse order - Fields before Event)
    with open(file_name, "a") as file:
        for model in reversed(models):
            _write_model_class(model, needs_field_alias, file)

    return file_name
