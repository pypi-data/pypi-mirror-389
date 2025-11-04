import json
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from lxml import etree

from xmlu.convert_to_json import _get_root, xml_to_console, xml_to_dict, xml_to_json


@pytest.fixture
def simple_xml_file(tmp_path: Path) -> Path:
    """Create a simple XML file for testing."""
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
def nested_xml_file(tmp_path: Path) -> Path:
    """Create an XML file with nested structure and attributes."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Schedule Name="channel-1">
    <Events Channel="SPORZA1">
        <Event Uid="1" Type="Main Event">
            <Name>Test Event</Name>
            <Fields>
                <Parameter Name="Duration" Value="01:00:00" />
                <Parameter Name="Device" Value="SM-1" />
            </Fields>
        </Event>
    </Events>
</Schedule>
"""
    file_path = tmp_path / "nested.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def empty_xml_file(tmp_path: Path) -> Path:
    """Create an XML file with empty elements."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <EmptyEvent></EmptyEvent>
    <Event>
        <Name></Name>
    </Event>
</Root>
"""
    file_path = tmp_path / "empty.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def text_and_attributes_xml_file(tmp_path: Path) -> Path:
    """Create an XML file with both text content and attributes."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event id="1" status="active">
        <Name lang="en">Test Event</Name>
        <Description>A test event description</Description>
        <EmptyWithAttr lang="en"></EmptyWithAttr>
    </Event>
</Root>
"""
    file_path = tmp_path / "text_attr.xml"
    file_path.write_text(xml_content)
    return file_path


@pytest.fixture
def multiple_same_tags_xml_file(tmp_path: Path) -> Path:
    """Create an XML file with multiple elements with the same tag name."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Item>First Item</Item>
    <Item>Second Item</Item>
    <Item>Third Item</Item>
</Root>
"""
    file_path = tmp_path / "multiple.xml"
    file_path.write_text(xml_content)
    return file_path


class TestGetRoot:
    """Tests for the _get_root function."""

    def test_get_root_with_string_path(self, simple_xml_file: Path):
        """Test _get_root with string file path."""
        root = _get_root(str(simple_xml_file))
        assert isinstance(root, etree._Element)
        assert root.tag == "Root"

    def test_get_root_with_path_object(self, simple_xml_file: Path):
        """Test _get_root with Path object."""
        root = _get_root(simple_xml_file)
        assert isinstance(root, etree._Element)
        assert root.tag == "Root"

    def test_get_root_invalid_file(self, tmp_path: Path):
        """Test _get_root with non-existent file."""
        non_existent = tmp_path / "nonexistent.xml"
        with pytest.raises((FileNotFoundError, OSError)):
            _get_root(non_existent)

    def test_get_root_invalid_xml(self, tmp_path: Path):
        """Test _get_root with invalid XML content."""
        invalid_xml = tmp_path / "invalid.xml"
        invalid_xml.write_text("This is not XML")
        with pytest.raises(etree.XMLSyntaxError):
            _get_root(invalid_xml)


class TestXmlToDict:
    """Tests for the xml_to_dict function.

    Key behaviors tested:
    - Multiple elements with same tag become lists
    - Elements with text content become strings (attributes are lost)
    - Empty elements with attributes preserve attributes as dictionaries
    - Mixed content (text + child elements) currently causes errors
    """

    def test_simple_xml_structure(self, simple_xml_file: Path):
        """Test conversion of simple XML structure to dictionary."""
        result = xml_to_dict(simple_xml_file)

        assert "Root" in result
        assert "Event" in result["Root"]
        assert isinstance(result["Root"]["Event"], list)
        assert len(result["Root"]["Event"]) == 2

        # Check first event - the list contains dictionaries with Event key
        first_event = result["Root"]["Event"][0]
        assert first_event["Name"] == "Event 1"
        assert first_event["IsActive"] == "True"
        assert first_event["Count"] == "5"

        # Check second event
        second_event = result["Root"]["Event"][1]
        assert second_event["Name"] == "Event 2"
        assert second_event["IsActive"] == "False"
        assert second_event["Count"] == "10"

    def test_nested_xml_structure(self, nested_xml_file: Path):
        """Test conversion of nested XML structure with attributes."""
        result = xml_to_dict(nested_xml_file)

        assert "Schedule" in result
        schedule = result["Schedule"]
        assert schedule["Name"] == "channel-1"
        assert "Events" in schedule

        events = schedule["Events"]
        assert events["Channel"] == "SPORZA1"
        assert "Event" in events

        event = events["Event"]
        assert event["Uid"] == "1"
        assert event["Type"] == "Main Event"
        assert event["Name"] == "Test Event"
        assert "Fields" in event

    def test_empty_xml_elements(self, empty_xml_file: Path):
        """Test conversion of XML with empty elements."""
        result = xml_to_dict(empty_xml_file)

        assert "Root" in result
        root = result["Root"]
        assert "EmptyEvent" in root
        assert "Event" in root

        # Empty elements should result in empty dictionaries
        assert root["EmptyEvent"] == {}
        assert root["Event"]["Name"] == {}

    def test_text_and_attributes(self, text_and_attributes_xml_file: Path):
        """Test conversion of XML with both text content and attributes.

        Important behavior: When an element has text content, the text takes precedence
        and attributes are lost. Only empty elements preserve their attributes.
        """
        result = xml_to_dict(text_and_attributes_xml_file)

        assert "Root" in result
        root = result["Root"]
        assert "Event" in root

        event = root["Event"]
        assert event["id"] == "1"
        assert event["status"] == "active"
        # When an element has text content, it becomes a string, not a dict with attributes
        assert (
            event["Name"] == "Test Event"
        )  # Text content takes precedence over attributes
        assert event["Description"] == "A test event description"
        # When element is empty but has attributes, attributes are preserved
        assert isinstance(event["EmptyWithAttr"], dict)
        assert event["EmptyWithAttr"]["lang"] == "en"

    def test_multiple_same_tags(self, multiple_same_tags_xml_file: Path):
        """Test conversion of XML with multiple elements with same tag name."""
        result = xml_to_dict(multiple_same_tags_xml_file)

        assert "Root" in result
        root = result["Root"]
        assert "Item" in root

        items = root["Item"]
        assert isinstance(items, list)
        assert len(items) == 3
        assert items[0] == "First Item"
        assert items[1] == "Second Item"
        assert items[2] == "Third Item"

    def test_xml_to_dict_with_element_input(self, simple_xml_file: Path):
        """Test xml_to_dict when passing an XML element instead of file path."""
        root_element = _get_root(simple_xml_file)
        result = xml_to_dict(root_element)

        assert "Root" in result
        assert "Event" in result["Root"]
        assert isinstance(result["Root"]["Event"], list)


class TestXmlToJson:
    """Tests for the xml_to_json function."""

    def test_xml_to_json_return_string(self, simple_xml_file: Path):
        """Test that xml_to_json returns valid JSON string."""
        with patch("builtins.print") as mock_print:
            json_str = xml_to_json(simple_xml_file)

        # Should return a valid JSON string
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert "Root" in parsed
        assert "Event" in parsed["Root"]

        # Should have printed the JSON
        mock_print.assert_called_once_with(json_str)

    def test_xml_to_json_save_to_file(self, simple_xml_file: Path, tmp_path: Path):
        """Test xml_to_json saving output to file."""
        output_file = tmp_path / "output.json"

        with patch("builtins.print") as mock_print:
            json_str = xml_to_json(simple_xml_file, output_file)

        # File should be created
        assert output_file.exists()

        # File content should match returned string
        file_content = output_file.read_text(encoding="utf-8")
        assert file_content == json_str

        # Should not print when saving to file
        mock_print.assert_not_called()

        # Verify JSON is valid
        parsed = json.loads(file_content)
        assert "Root" in parsed

    def test_xml_to_json_custom_indent(self, simple_xml_file: Path):
        """Test xml_to_json with custom indentation."""
        with patch("builtins.print") as mock_print:
            json_str = xml_to_json(simple_xml_file, indent=2)

        # Should use custom indentation
        lines = json_str.split("\n")
        # Check that indentation is 2 spaces
        indented_lines = [
            line
            for line in lines
            if line.startswith("  ") and not line.startswith("    ")
        ]
        assert len(indented_lines) > 0

    def test_xml_to_json_with_path_object(self, simple_xml_file: Path, tmp_path: Path):
        """Test xml_to_json with Path objects for both input and output."""
        output_file = tmp_path / "output.json"

        with patch("builtins.print"):
            json_str = xml_to_json(simple_xml_file, output_file)

        assert output_file.exists()
        file_content = output_file.read_text(encoding="utf-8")
        assert file_content == json_str

    def test_xml_to_json_complex_structure(self, nested_xml_file: Path):
        """Test xml_to_json with complex nested structure."""
        with patch("builtins.print"):
            json_str = xml_to_json(nested_xml_file)

        parsed = json.loads(json_str)
        assert "Schedule" in parsed

        schedule = parsed["Schedule"]
        assert schedule["Name"] == "channel-1"
        assert "Events" in schedule

        events = schedule["Events"]
        assert events["Channel"] == "SPORZA1"
        assert "Event" in events


class TestXmlToConsole:
    """Tests for the xml_to_console function."""

    def test_xml_to_console_output(self, simple_xml_file: Path):
        """Test xml_to_console prints expected output."""
        with patch("builtins.print") as mock_print:
            xml_to_console(simple_xml_file)

        # Check that print was called multiple times
        assert mock_print.call_count > 5

        # Check some expected output patterns
        calls = [call.args[0] for call in mock_print.call_args_list]

        # Should print root tag
        assert "Root" in calls

        # Should print Event tags
        event_calls = [call for call in calls if call == "Event"]
        assert len(event_calls) == 2

    def test_xml_to_console_with_attributes(self, nested_xml_file: Path):
        """Test xml_to_console with XML containing attributes."""
        with patch("builtins.print") as mock_print:
            xml_to_console(nested_xml_file)

        calls = [call.args[0] for call in mock_print.call_args_list if call.args]

        # Should print root tag
        assert "Schedule" in calls

    def test_xml_to_console_empty_elements(self, empty_xml_file: Path):
        """Test xml_to_console with empty XML elements."""
        with patch("builtins.print") as mock_print:
            xml_to_console(empty_xml_file)

        # Should not raise any exceptions
        assert mock_print.call_count > 0

    def test_xml_to_console_with_path_object(self, simple_xml_file: Path):
        """Test xml_to_console with Path object input."""
        with patch("builtins.print") as mock_print:
            xml_to_console(simple_xml_file)

        assert mock_print.call_count > 0


class TestIntegration:
    """Integration tests for the entire conversion workflow."""

    def test_round_trip_consistency(self, simple_xml_file: Path):
        """Test that converting XML to dict and then to JSON produces consistent results."""
        # Convert to dict
        xml_dict = xml_to_dict(simple_xml_file)

        # Convert to JSON string
        with patch("builtins.print"):
            json_str = xml_to_json(simple_xml_file)

        # Parse JSON back to dict
        json_dict = json.loads(json_str)

        # Should be identical
        assert xml_dict == json_dict

    def test_file_operations_with_real_xml(self, tmp_path: Path):
        """Test file operations with a more realistic XML structure."""
        # Create a more complex XML similar to the project's use case
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Schedule Name="test-schedule">
    <Events Channel="TEST">
        <Event Uid="1" Type="Test Event">
            <ScheduleName>Test Schedule</ScheduleName>
            <EventKind>MainEvent</EventKind>
            <Fields>
                <Parameter Name="Duration" Value="00:01:00:00" />
                <Parameter Name="Device" Value="TEST-1" />
                <Parameter Name="Enabled" Value="True" />
            </Fields>
        </Event>
    </Events>
</Schedule>
"""
        xml_file = tmp_path / "test_schedule.xml"
        xml_file.write_text(xml_content)

        json_file = tmp_path / "test_schedule.json"

        # Convert to JSON
        with patch("builtins.print"):
            json_str = xml_to_json(xml_file, json_file)

        # Verify file was created
        assert json_file.exists()

        # Verify content is valid JSON
        parsed = json.loads(json_file.read_text())
        assert "Schedule" in parsed
        assert parsed["Schedule"]["Name"] == "test-schedule"

    def test_error_handling_invalid_xml(self, tmp_path: Path):
        """Test error handling with invalid XML."""
        invalid_xml = tmp_path / "invalid.xml"
        invalid_xml.write_text("<root><unclosed>")

        with pytest.raises(etree.XMLSyntaxError):
            xml_to_dict(invalid_xml)

        with pytest.raises(etree.XMLSyntaxError):
            xml_to_json(invalid_xml)

        with pytest.raises(etree.XMLSyntaxError):
            xml_to_console(invalid_xml)

    def test_unicode_handling(self, tmp_path: Path):
        """Test handling of Unicode characters in XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Name>Événement spécial</Name>
        <Description>测试事件</Description>
        <Notes>Тестовое событие</Notes>
    </Event>
</Root>
"""
        xml_file = tmp_path / "unicode.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        # Should handle Unicode without issues
        result = xml_to_dict(xml_file)
        assert "Root" in result

        with patch("builtins.print"):
            json_str = xml_to_json(xml_file)

        parsed = json.loads(json_str)
        event = parsed["Root"]["Event"]
        assert event["Name"] == "Événement spécial"
        assert event["Description"] == "测试事件"
        assert event["Notes"] == "Тестовое событие"


class TestEdgeCases:
    """Tests for edge cases and special scenarios.

    Note: Some tests document current limitations of the xml_to_dict function,
    particularly around mixed content handling where text and child elements coexist.
    """

    def test_xml_with_whitespace_text(self, tmp_path: Path):
        """Test XML with whitespace-only text content."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Name>   </Name>
        <Description>
        </Description>
        <Notes>Valid Content</Notes>
    </Event>
</Root>
"""
        xml_file = tmp_path / "whitespace.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        event = result["Root"]["Event"]

        # Whitespace-only content should result in empty dict
        assert event["Name"] == {}
        assert event["Description"] == {}
        assert event["Notes"] == "Valid Content"

    def test_xml_with_namespaces(self, tmp_path: Path):
        """Test XML with namespaces."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root xmlns:test="http://example.com/test">
    <test:element>Namespaced Content</test:element>
    <regular>Regular Content</regular>
</root>
"""
        xml_file = tmp_path / "namespaces.xml"
        xml_file.write_text(xml_content)

        # Should handle namespaced elements
        result = xml_to_dict(xml_file)
        assert "root" in result

    def test_xml_with_cdata(self, tmp_path: Path):
        """Test XML with CDATA sections."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <Description><![CDATA[Some <b>HTML</b> content & special chars]]></Description>
    </Event>
</Root>
"""
        xml_file = tmp_path / "cdata.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        event = result["Root"]["Event"]
        # CDATA content should be preserved as text
        assert "Some <b>HTML</b> content & special chars" in event["Description"]

    def test_xml_with_comments(self, tmp_path: Path):
        """Test XML with comments (should be ignored)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <!-- This is a comment -->
    <Event>
        <Name>Test Event</Name>
        <!-- Another comment -->
    </Event>
</Root>
"""
        xml_file = tmp_path / "comments.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        # Comments should not affect the structure
        assert "Root" in result
        assert result["Root"]["Event"]["Name"] == "Test Event"

    def test_deeply_nested_xml(self, tmp_path: Path):
        """Test deeply nested XML structure."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Level1>
    <Level2>
        <Level3>
            <Level4>
                <Level5>
                    <DeepValue>Deep Content</DeepValue>
                </Level5>
            </Level4>
        </Level3>
    </Level2>
</Level1>
"""
        xml_file = tmp_path / "deep.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)

        # Navigate through the nested structure
        deep_value = result["Level1"]["Level2"]["Level3"]["Level4"]["Level5"][
            "DeepValue"
        ]
        assert deep_value == "Deep Content"

    def test_xml_with_mixed_content_limitation(self, tmp_path: Path):
        """Test XML with mixed text and element content (current limitation)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Mixed>
        Text before 
        <Element>Element Content</Element>
        Text after
    </Mixed>
</Root>
"""
        xml_file = tmp_path / "mixed.xml"
        xml_file.write_text(xml_content)

        # Mixed content causes issues in the current implementation
        # The function tries to set node to text but then update it with child elements
        # This is a known limitation that should be documented
        with pytest.raises(
            AttributeError, match="'str' object has no attribute 'update'"
        ):
            xml_to_dict(xml_file)

    def test_xml_with_only_text_content(self, tmp_path: Path):
        """Test XML with only text content (works correctly)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <TextOnly>Just some text content</TextOnly>
    <AnotherText>More text</AnotherText>
</Root>
"""
        xml_file = tmp_path / "text_only.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        assert result["Root"]["TextOnly"] == "Just some text content"
        assert result["Root"]["AnotherText"] == "More text"

    def test_large_attribute_values(self, tmp_path: Path):
        """Test XML with large attribute values."""
        large_value = "x" * 1000  # 1000 character attribute value
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event largeattr="{large_value}">
        <Name>Test</Name>
    </Event>
</Root>
"""
        xml_file = tmp_path / "large_attr.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        event = result["Root"]["Event"]
        assert event["largeattr"] == large_value
        assert len(event["largeattr"]) == 1000

    def test_special_characters_in_tag_names(self, tmp_path: Path):
        """Test XML with special characters in tag names."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event_1>
        <Field-Name>Hyphenated</Field-Name>
        <Field.Name>Dotted</Field.Name>
    </Event_1>
</Root>
"""
        xml_file = tmp_path / "special_tags.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        event = result["Root"]["Event_1"]
        assert event["Field-Name"] == "Hyphenated"
        assert event["Field.Name"] == "Dotted"


class TestPerformanceConsiderations:
    """Tests for performance and memory usage considerations."""

    def test_multiple_identical_elements_performance(self, tmp_path: Path):
        """Test performance with many identical elements."""
        # Create XML with many similar elements
        events = []
        for i in range(100):
            events.append(
                f"""
        <Event>
            <Id>{i}</Id>
            <Name>Event {i}</Name>
            <Active>true</Active>
        </Event>"""
            )

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Root>{''.join(events)}
</Root>
"""
        xml_file = tmp_path / "many_events.xml"
        xml_file.write_text(xml_content)

        # Should handle many elements without issues
        result = xml_to_dict(xml_file)
        assert len(result["Root"]["Event"]) == 100

        # Test JSON conversion
        with patch("builtins.print"):
            json_str = xml_to_json(xml_file)

        parsed = json.loads(json_str)
        assert len(parsed["Root"]["Event"]) == 100

    def test_memory_usage_with_large_text_content(self, tmp_path: Path):
        """Test memory usage with large text content."""
        large_text = "A" * 10000  # 10KB of text
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Event>
        <LargeText>{large_text}</LargeText>
    </Event>
</Root>
"""
        xml_file = tmp_path / "large_text.xml"
        xml_file.write_text(xml_content)

        result = xml_to_dict(xml_file)
        assert len(result["Root"]["Event"]["LargeText"]) == 10000

        # Should also work with JSON conversion
        with patch("builtins.print"):
            json_str = xml_to_json(xml_file)

        assert len(json_str) > 10000  # JSON should contain the large text
