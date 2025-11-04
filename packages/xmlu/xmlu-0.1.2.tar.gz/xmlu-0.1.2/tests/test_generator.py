import os
from pathlib import Path

import pytest

from xmlu.convert_to_pydantic import create_models_file, generate_pydantic_models


@pytest.fixture
def simple_xml_file(tmp_path: Path) -> Path:
    """Create a simple XML file with basic structure."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Name>Event 1</Name>
        <IsActive>True</IsActive>
        <Count>5</Count>
    </Event>
    <Event>
        <Name>Event 2</Name>
        <IsActive>False</IsActive>
        <Count>10</Count>
    </Event>
</Root>
"""
    file_path = tmp_path / "simple.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def optional_fields_xml_file(tmp_path: Path) -> Path:
    """Create XML with optional fields (not present in all elements)."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Name>Event 1</Name>
        <Description>Has description</Description>
    </Event>
    <Event>
        <Name>Event 2</Name>
    </Event>
    <Event>
        <Name>Event 3</Name>
        <Description>Also has description</Description>
    </Event>
</Root>
"""
    file_path = tmp_path / "optional.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def nested_structure_xml_file(tmp_path: Path) -> Path:
    """Create XML with nested Name/Value parameter structure."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Title>Event 1</Title>
        <Fields>
            <Parameter Name="Duration" Value="01:00:00" />
            <Parameter Name="Enabled" Value="True" />
        </Fields>
    </Event>
    <Event>
        <Title>Event 2</Title>
        <Fields>
            <Parameter Name="Duration" Value="02:30:00" />
            <Parameter Name="Enabled" Value="False" />
        </Fields>
    </Event>
</Root>
"""
    file_path = tmp_path / "nested.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def mixed_structure_xml_file(tmp_path: Path) -> Path:
    """Create XML with both simple and nested structures."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <EventId>1</EventId>
        <IsFixed>True</IsFixed>
        <Fields>
            <Parameter Name="Duration" Value="01:00:00" />
            <Parameter Name="Device" Value="SM-1" />
        </Fields>
        <OptionalField>Present</OptionalField>
    </Event>
    <Event>
        <EventId>2</EventId>
        <IsFixed>False</IsFixed>
        <Fields>
            <Parameter Name="Duration" Value="02:00:00" />
            <Parameter Name="Device" Value="SM-2" />
        </Fields>
    </Event>
</Root>
"""
    file_path = tmp_path / "mixed.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def nested_optional_params_xml_file(tmp_path: Path) -> Path:
    """Create XML where nested parameters are not always present."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Name>Event 1</Name>
        <Config>
            <Parameter Name="Required" Value="Always here" />
            <Parameter Name="Optional" Value="Sometimes here" />
        </Config>
    </Event>
    <Event>
        <Name>Event 2</Name>
        <Config>
            <Parameter Name="Required" Value="Always here" />
        </Config>
    </Event>
</Root>
"""
    file_path = tmp_path / "nested_optional.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def empty_events_xml_file(tmp_path: Path) -> Path:
    """Create XML with empty event elements."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event></Event>
    <Event></Event>
</Root>
"""
    file_path = tmp_path / "empty.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def type_inference_xml_file(tmp_path: Path) -> Path:
    """Create XML to test type inference (int, bool, str)."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <StringField>text value</StringField>
        <IntField>42</IntField>
        <BoolField>True</BoolField>
    </Event>
    <Event>
        <StringField>another text</StringField>
        <IntField>100</IntField>
        <BoolField>False</BoolField>
    </Event>
</Root>
"""
    file_path = tmp_path / "types.xml"
    file_path.write_text(xml_content)
    return file_path


class TestGeneratePydanticModels:
    """Tests for generate_pydantic_models function."""

    def test_simple_xml_structure(self, simple_xml_file: Path):
        """Test basic model generation from simple XML."""
        models = generate_pydantic_models(str(simple_xml_file), "Event")

        assert len(models) == 1
        Event = models[0]

        # Check model name
        assert Event.__name__ == "Event"

        # Check fields exist
        assert "Name" in Event.model_fields
        assert "IsActive" in Event.model_fields
        assert "Count" in Event.model_fields

        # Validate instance creation (types are coerced by Pydantic)
        event = Event(Name="Test", IsActive="True", Count="5")
        assert event.Name == "Test"
        assert event.IsActive is True  # Pydantic coerces "True" to bool
        assert event.Count == 5  # Pydantic coerces "5" to int

    def test_optional_fields_detection(self, optional_fields_xml_file: Path):
        """Test that optional fields are properly detected."""
        models = generate_pydantic_models(str(optional_fields_xml_file), "Event")
        Event = models[0]

        # Name is required (present in all events)
        assert Event.model_fields["Name"].is_required()

        # Description is optional (not present in all events)
        assert not Event.model_fields["Description"].is_required()

        # Should be able to create without optional field
        event = Event(Name="Test")
        assert event.Name == "Test"
        assert event.Description is None

    def test_nested_structure_detection(self, nested_structure_xml_file: Path):
        """Test detection and creation of nested models."""
        models = generate_pydantic_models(str(nested_structure_xml_file), "Event")

        # Should have parent model + nested model
        assert len(models) == 2
        Event, Fields = models

        # Check parent model
        assert Event.__name__ == "Event"
        assert "Title" in Event.model_fields
        assert "Fields" in Event.model_fields

        # Check nested model
        assert Fields.__name__ == "Fields"
        assert "Duration" in Fields.model_fields
        assert "Enabled" in Fields.model_fields

        # Validate nested instance creation
        fields = Fields(Duration="01:00:00", Enabled="True")
        event = Event(Title="Test", Fields=fields)
        assert event.Title == "Test"
        assert event.Fields.Duration == "01:00:00"

    def test_mixed_structure(self, mixed_structure_xml_file: Path):
        """Test XML with both simple and nested fields."""
        models = generate_pydantic_models(str(mixed_structure_xml_file), "Event")

        assert len(models) == 2
        Event, Fields = models

        # Check simple fields
        assert "EventId" in Event.model_fields
        assert "IsFixed" in Event.model_fields
        assert Event.model_fields["EventId"].is_required()
        assert Event.model_fields["IsFixed"].is_required()

        # Check optional field
        assert "OptionalField" in Event.model_fields
        assert not Event.model_fields["OptionalField"].is_required()

        # Check nested model reference
        assert "Fields" in Event.model_fields
        assert Event.model_fields["Fields"].is_required()

    @pytest.mark.filterwarnings("ignore::pydantic.warnings.PydanticDeprecatedSince20")
    def test_nested_optional_parameters(self, nested_optional_params_xml_file: Path):
        """Test that nested parameters can be optional."""
        models = generate_pydantic_models(str(nested_optional_params_xml_file), "Event")

        assert len(models) == 2
        Event, Config = models

        # Required parameter in nested model
        assert Config.model_fields["Required"].is_required()

        # Optional parameter in nested model
        assert not Config.model_fields["Optional"].is_required()

        # Should be able to create config without optional param
        config = Config(Required="value")
        assert config.Required == "value"
        assert config.Optional is None

    def test_empty_events(self, empty_events_xml_file: Path):
        """Test handling of empty event elements."""
        models = generate_pydantic_models(str(empty_events_xml_file), "Event")

        assert len(models) == 1
        Event = models[0]

        # Empty events should create a model with no required fields
        assert len(Event.model_fields) == 0

        # Should be able to create empty instance
        event = Event()
        assert event is not None

    def test_type_inference(self, type_inference_xml_file: Path):
        """Test that types are correctly inferred from values."""
        models = generate_pydantic_models(str(type_inference_xml_file), "Event")
        Event = models[0]

        # Check that all fields exist
        assert "StringField" in Event.model_fields
        assert "IntField" in Event.model_fields
        assert "BoolField" in Event.model_fields

        # Create instance and validate (types are coerced by Pydantic)
        event = Event(StringField="test", IntField="123", BoolField="True")
        assert event.StringField == "test"
        assert event.IntField == 123  # Pydantic coerces string to int
        assert event.BoolField is True  # Pydantic coerces string to bool

    def test_custom_parent_element(self, tmp_path: Path):
        """Test using a different parent element name."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <CustomElement>
        <Field1>Value1</Field1>
    </CustomElement>
    <CustomElement>
        <Field1>Value2</Field1>
    </CustomElement>
</Root>
"""
        file_path = tmp_path / "custom.xml"
        file_path.write_text(xml_content)

        models = generate_pydantic_models(str(file_path), "CustomElement")

        assert len(models) == 1
        assert models[0].__name__ == "CustomElement"


class TestCreateModelsFile:
    """Tests for create_models_file function."""

    def test_basic_file_creation(self, simple_xml_file: Path, tmp_path: Path):
        """Test basic model file creation."""
        models = generate_pydantic_models(str(simple_xml_file), "Event")

        # Change to tmp directory for file generation
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(str(simple_xml_file), list(models))

            # Check file was created
            assert os.path.exists(output_file)
            assert output_file == "root_models.py"

            # Read and verify file contents
            content = Path(output_file).read_text()
            assert "Auto-generated Pydantic models from Root.xml" in content
            assert "from pydantic import BaseModel" in content
            assert "class Event(BaseModel):" in content
        finally:
            os.chdir(original_dir)

    def test_file_with_optional_imports(
        self, optional_fields_xml_file: Path, tmp_path: Path
    ):
        """Test that Optional import is included when needed."""
        models = generate_pydantic_models(str(optional_fields_xml_file), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(
                str(optional_fields_xml_file), list(models)
            )

            content = Path(output_file).read_text()
            assert "from typing import Optional" in content
            assert "Optional[str]" in content
        finally:
            os.chdir(original_dir)

    def test_file_with_field_aliases(self, tmp_path: Path):
        """Test that Field aliases are included for PascalCase names."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <PascalCaseName>Value1</PascalCaseName>
    </Event>
    <Event>
        <PascalCaseName>Value2</PascalCaseName>
    </Event>
</Root>
"""
        file_path = tmp_path / "pascal.xml"
        file_path.write_text(xml_content)

        models = generate_pydantic_models(str(file_path), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(str(file_path), list(models))

            content = Path(output_file).read_text()
            assert "from pydantic import BaseModel, Field, ConfigDict" in content
            assert 'Field(alias="PascalCaseName")' in content
            assert "pascal_case_name:" in content
        finally:
            os.chdir(original_dir)

    def test_file_with_nested_models(
        self, nested_structure_xml_file: Path, tmp_path: Path
    ):
        """Test file generation with nested models."""
        models = generate_pydantic_models(str(nested_structure_xml_file), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(
                str(nested_structure_xml_file), list(models)
            )

            content = Path(output_file).read_text()

            # Both models should be present
            assert "class Fields(BaseModel):" in content
            assert "class Event(BaseModel):" in content

            # Fields should come before Event (reversed order)
            fields_pos = content.index("class Fields(BaseModel):")
            event_pos = content.index("class Event(BaseModel):")
            assert fields_pos < event_pos
        finally:
            os.chdir(original_dir)

    def test_file_config_dict_present(self, simple_xml_file: Path, tmp_path: Path):
        """Test that model_config with ConfigDict is present."""
        models = generate_pydantic_models(str(simple_xml_file), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(str(simple_xml_file), list(models))

            content = Path(output_file).read_text()
            assert "model_config = ConfigDict(" in content
            assert "str_strip_whitespace=True" in content
            assert "validate_assignment=True" in content
            assert "populate_by_name=True" in content
        finally:
            os.chdir(original_dir)

    def test_generated_file_is_importable(self, simple_xml_file: Path, tmp_path: Path):
        """Test that generated file can be imported as a Python module."""
        models = generate_pydantic_models(str(simple_xml_file), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(str(simple_xml_file), list(models))

            # Try to compile the generated file
            content = Path(output_file).read_text()
            compile(content, output_file, "exec")
        finally:
            os.chdir(original_dir)

    def test_empty_model_handling(self, empty_events_xml_file: Path, tmp_path: Path):
        """Test that empty models generate with 'pass' statement."""
        models = generate_pydantic_models(str(empty_events_xml_file), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(str(empty_events_xml_file), list(models))

            content = Path(output_file).read_text()
            assert "class Event(BaseModel):" in content
            assert "pass" in content
        finally:
            os.chdir(original_dir)

    def test_returns_correct_filename(self, simple_xml_file: Path, tmp_path: Path):
        """Test that the function returns the correct output filename."""
        models = generate_pydantic_models(str(simple_xml_file), "Event")

        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            output_file = create_models_file(str(simple_xml_file), list(models))

            # Should return lowercase version of root tag + _models.py
            assert output_file == "root_models.py"
            assert os.path.exists(output_file)
        finally:
            os.chdir(original_dir)
