import json
from pathlib import Path
from typing import Optional, Union

from lxml import etree


def _get_root(source_file: Union[str, Path]) -> etree._Element:
    """Parse an XML file and return its root element."""
    tree = etree.parse(source_file)
    return tree.getroot()


def xml_to_console(source_file: Union[str, Path]) -> str:
    """Convert an XML file to a JSON string."""
    root = _get_root(source_file)
    print(root.tag)
    print(f"    {root.attrib}\n")

    for event in root.iter("Event"):
        parent_event = event.tag
        parent_event_text = event.text.strip() if event.text else None
        parent_event_attrib = event.attrib if event.attrib else None

        print(parent_event)
        if parent_event_text:
            print(f"    Text: {parent_event_text}")
        elif parent_event_attrib:
            print(f"    Attrib: {parent_event_attrib}")

        for child in event:
            child_tag = child.tag
            child_text = child.text.strip() if child.text else None
            child_attrib = child.attrib if child.attrib else None

            print(f"    {child_tag}")
            if child_text:
                print(f"        Text: {child_text}")
            elif child_attrib:
                print(f"        Attrib: {child_attrib}")

            for grandchild in child:
                grandchild_tag = grandchild.tag
                grandchild_text = grandchild.text.strip() if grandchild.text else None
                grandchild_attrib = grandchild.attrib if grandchild.attrib else None

                print(f"        {grandchild_tag}")
                if grandchild_text:
                    print(f"            Text: {grandchild_text}")
                elif grandchild_attrib:
                    print(f"            Attrib: {grandchild_attrib}")


def xml_to_dict(source_file: Union[str, Path]) -> dict:
    """Recursively convert an XML element and its children to a dictionary."""
    element = (
        _get_root(source_file) if isinstance(source_file, (str, Path)) else source_file
    )

    node = {}

    for key, value in element.attrib.items():
        node[key] = value

    text = element.text.strip() if element.text else None
    if text:
        node = text

    # Recursively include child elements
    for child in element:
        child_dict = xml_to_dict(child)
        if child.tag in node:
            # If the tag already exists, convert to a list
            if not isinstance(node[child.tag], list):
                node[child.tag] = [node[child.tag]]
            node[child.tag].append(child_dict[child.tag])
        else:
            node.update(child_dict)

    return {element.tag: node}


def xml_to_json(
    source_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    indent: int = 4,
) -> str:
    """Convert an XML file to a JSON string and optionally save it to a file."""
    xml_dict = xml_to_dict(source_file)
    json_str = json.dumps(xml_dict, indent=indent)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_str)
    else:
        print(json_str)

    return json_str
