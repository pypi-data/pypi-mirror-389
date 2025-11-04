# xmlu

**XML Utility** - Transform XML files into type-safe Pydantic models with automatic type inference and structure detection.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Automatic Type Inference**: Detects `str`, `int`, and `bool` types from XML values
- **Smart Field Detection**: Identifies required vs. optional fields based on occurrence patterns
- **Nested Model Support**: Recognizes and generates nested models for XML elements with `Name`/`Value` attributes
- **Pythonic Naming**: Converts XML tags to `snake_case` with field aliases to preserve original names
- **CLI & API**: Use as a command-line tool or import as a Python library
- **Type-Safe**: Generated models use Pydantic v2 for runtime validation
- **Rich Output**: Beautiful terminal interface with progress information

## Installation

```bash
# Using uv (recommended)
uv pip install xmlu

# Using pip
pip install xmlu
```

## Quick Start

### CLI Usage

```bash
# Generate models from XML file
xmlu generate schedule.xml --parent Event

# Specify custom output file
xmlu generate data.xml --parent Item --output models.py

# Verbose mode for detailed progress
xmlu generate schedule.xml --parent Event --verbose

# Show version
xmlu version
```

### Python API

```python
from xmlu import generate_pydantic_models, create_models_file

# Generate models
models = generate_pydantic_models("schedule.xml", parent_element="Event")
Event, Fields = models

# Create a models file
output_file = create_models_file("schedule.xml", list(models))
print(f"Generated: {output_file}")

# Use the generated models
event = Event(
    is_fixed=True,
    fields=Fields(duration="01:00:00", enabled=True)
)
```

## How It Works

`xmlu` analyzes your XML structure and generates Pydantic models with intelligent defaults:

**Input XML:**

```xml
<Schedule>
    <Event>
        <EventId>1</EventId>
        <IsFixed>True</IsFixed>
        <Fields>
            <Parameter Name="Duration" Value="01:00:00" />
            <Parameter Name="Device" Value="SM-1" />
        </Fields>
    </Event>
    <Event>
        <EventId>2</EventId>
        <IsFixed>False</IsFixed>
        <Fields>
            <Parameter Name="Duration" Value="02:00:00" />
        </Fields>
    </Event>
</Schedule>
```

**Generated Pydantic Models:**

```python
"""Auto-generated Pydantic models from Schedule.xml"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class Fields(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    duration: str = Field(alias="Duration")
    device: Optional[str] = Field(None, alias="Device")  # Optional - not in all Events

class Event(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    event_id: int = Field(alias="EventId")
    is_fixed: bool = Field(alias="IsFixed")
    fields: Fields = Field(alias="Fields")
```

## Features in Detail

### Type Inference

`xmlu` automatically infers Python types:

- **Boolean**: `True`, `False`, `0`, `1` → `bool`
- **Integer**: Numeric strings → `int`
- **String**: All other values → `str`

### Optional Fields

Fields that don't appear in every XML element are marked as `Optional[T]`:

```python
# Field present in 2 out of 3 events → Optional
device: Optional[str] = None
```

### Nested Structures

XML elements with child elements containing `Name` and `Value` attributes are automatically converted to nested models:

```xml
<Fields>
    <Parameter Name="Duration" Value="01:00:00" />
    <Parameter Name="Device" Value="SM-1" />
</Fields>
```

Becomes:

```python
class Fields(BaseModel):
    duration: str
    device: str
```

### Snake Case Conversion

XML tags are converted to Pythonic `snake_case` while preserving original names via field aliases:

```python
# XML: <EventId>123</EventId>
event_id: int = Field(alias="EventId")

# Both work for parsing:
Event(event_id=123)
Event(EventId=123)
```

## CLI Commands

### `generate`

Generate Pydantic models from an XML file.

```bash
xmlu generate [FILE] [OPTIONS]
```

**Options:**

- `--parent, -p TEXT`: XML tag to use as parent model (default: "Event")
- `--output, -o PATH`: Output file path (default: auto-generated)
- `--verbose, -v`: Show detailed progress information
- `--help`: Show help message

**Examples:**

```bash
# Basic usage
xmlu generate schedule.xml

# Custom parent element
xmlu generate data.xml --parent CustomElement

# Specify output file
xmlu generate data.xml -o app/models.py

# Verbose output
xmlu generate schedule.xml --verbose
```

### `version`

Show version information.

```bash
xmlu version
```

## API Reference

### `generate_pydantic_models(file_path, parent_element="Event")`

Generate Pydantic models from an XML file.

**Parameters:**

- `file_path` (str): Path to the XML file
- `parent_element` (str): XML tag name to use as parent model

**Returns:**

- `tuple[type[BaseModel], ...]`: Tuple of Pydantic models (parent first, then nested models)

**Example:**

```python
models = generate_pydantic_models("schedule.xml", "Event")
Event, Fields = models
```

### `create_models_file(file_path, models)`

Write Pydantic models to a Python file.

**Parameters:**

- `file_path` (str): Path to source XML file (used for naming output)
- `models` (list[type[BaseModel]]): List of Pydantic models to write

**Returns:**

- `str`: Name of the generated file

**Example:**

```python
output_file = create_models_file("schedule.xml", list(models))
# Returns: "schedule_models.py"
```

### Utility Functions

#### `convert_to_snake_case(name)`

Convert any string to snake_case.

```python
from xmlu import convert_to_snake_case

convert_to_snake_case("CamelCase")      # "camel_case"
convert_to_snake_case("HTTPServer")     # "http_server"
convert_to_snake_case("kebab-case")     # "kebab_case"
```

#### `convert_to_pascal_case(name)`

Convert any string to PascalCase.

```python
from xmlu import convert_to_pascal_case

convert_to_pascal_case("snake_case")    # "SnakeCase"
convert_to_pascal_case("HTTPServer")    # "HTTPServer"
convert_to_pascal_case("kebab-case")    # "KebabCase"
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/MichielMe/xmlu.git
cd xmlu

# Install dependencies with uv
uv sync

# Run tests
make test
```

### Running Tests

```bash
# Run all tests with pytest
make test

# Or directly with uv
uv run pytest -v
```

### Project Structure

```
xmlu/
├── src/
│   └── xmlu/
│       ├── __init__.py              # Public API exports
│       ├── main.py                  # CLI application
│       ├── convert_to_pydantic.py   # Core model generation
│       └── utils.py                 # String utilities & type inference
├── tests/
│   ├── test_generator.py            # Model generation tests
│   └── test_string_utils.py         # Utility function tests
├── pyproject.toml                   # Project configuration
└── README.md
```

## Configuration

Generated models include sensible defaults:

```python
model_config = ConfigDict(
    str_strip_whitespace=True,      # Auto-strip whitespace
    validate_assignment=True,        # Validate on field assignment
    populate_by_name=True,           # Accept both snake_case and original names
)
```

## Requirements

- Python 3.12+
- lxml >= 6.0.2
- pydantic >= 2.12.3
- typer >= 0.20.0

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

**Michiel Meire**

- Email: michiel.meire1@gmail.com
- GitHub: [@MichielMe](https://github.com/MichielMe)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

- [ ] JSON output format support
- [ ] XML Schema (XSD) validation
- [ ] Support for XML attributes (not just elements)
- [ ] List/array type detection for repeated elements
- [ ] Custom type mapping configuration
- [ ] Watch mode for automatic regeneration

## Acknowledgments

Built with:

- [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
- [lxml](https://lxml.de/) - XML processing library
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting (via Typer)
