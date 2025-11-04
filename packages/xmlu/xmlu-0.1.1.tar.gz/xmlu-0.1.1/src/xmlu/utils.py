import re


def convert_to_snake_case(name: str) -> str:
    """Convert any string to snake_case."""
    s = name.strip()

    # Insert underscores at CamelCase boundaries (handles acronyms too: HTTPServer -> HTTP_Server)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)

    # Replace any non-word characters (spaces, hyphens, punctuation) with underscores
    s = re.sub(r"[^\w]+", "_", s)

    # Collapse multiple underscores and trim
    s = re.sub(r"_+", "_", s).strip("_")

    return s.lower()


def convert_to_pascal_case(name: str) -> str:
    """
    Convert any string (snake/kebab/spaces/camel/Pascal) to PascalCase.
    - Preserves ALL-CAPS acronyms: 'HTTP_server' -> 'HTTPServer'
    - Handles digits: 'json2_xml' -> 'JSON2XML'
    - Collapses punctuation and separators.
    """
    if not name:
        return ""

    s = name.strip()

    # Normalize obvious separators to spaces (underscores, hyphens, punctuation)
    s = re.sub(r"[\W_]+", " ", s, flags=re.UNICODE)

    # Also split internal CamelCase boundaries
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)  # XMLHTTP -> XML HTTP
    s = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", s)  # myHTTP -> my HTTP

    parts = []
    for token in s.split():
        # Further split boundaries between letters and digits (A1B -> A 1 B)
        subtokens = re.split(r"(?<=\D)(?=\d)|(?<=\d)(?=\D)", token)
        for sub in subtokens:
            if len(sub) > 1 and sub.isupper():
                # Preserve acronyms (e.g., HTTP, XML)
                parts.append(sub)
            else:
                parts.append(sub.capitalize())

    return "".join(parts)


def infer_type(values: list[str]) -> tuple[str, bool]:
    """
    Infer the best Python type for a field based on sample values.

    Args:
        values: List of string values from XML

    Returns:
        Tuple of (type_name, is_optional)
        - type_name: "str", "int", or "bool"
        - is_optional: True if field can be None
    """
    if not values:
        return "str", True

    has_empty = "" in values or None in values
    non_empty_values = [v for v in values if v]

    if not non_empty_values:
        return "str", True

    # Check for boolean values
    bool_values = {"True", "False", "true", "false", "0", "1"}
    if all(v in bool_values for v in non_empty_values):
        return "bool", has_empty or len(values) != len(non_empty_values)

    # Check for integer values
    try:
        for v in non_empty_values[: min(10, len(non_empty_values))]:
            int(v)
        return "int", has_empty or len(values) != len(non_empty_values)
    except ValueError:
        pass

    # Default to string
    return "str", has_empty or len(values) != len(non_empty_values)
