import pytest

from xmlu.utils import convert_to_pascal_case, convert_to_snake_case


class TestSnakeCase:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("CamelCase", "camel_case"),
            ("HTTPServerError", "http_server_error"),
            ("version2Update", "version2_update"),
            (" already  spaced  name ", "already_spaced_name"),
            ("dash-and—punctuation’s OK!", "dash_and_punctuation_s_ok"),
            ("MixOf CAPS And_Symbols", "mix_of_caps_and_symbols"),
            ("snake_case_already", "snake_case_already"),
            ("__Leading__and__trailing__", "leading_and_trailing"),
            ("kebab-case-name", "kebab_case_name"),
            ("JSON2XMLConverter", "json2_xml_converter"),
            ("ÅngströmUnit", "ångström_unit"),
            ("", ""),
            ("'quotes' “and” «other»", "quotes_and_other"),
            ("multiple___underscores", "multiple_underscores"),
            ("ends-with-punct!!!", "ends_with_punct"),
        ],
    )
    def test_examples(self, raw, expected):
        assert convert_to_snake_case(raw) == expected

    def test_idempotence(self):
        samples = [
            "CamelCase",
            "already_snake_case",
            "HTTPServer",
            " has  spaces ",
            "dash-and—punctuation’s OK!",
        ]
        for s in samples:
            once = convert_to_snake_case(s)
            twice = convert_to_snake_case(once)
            assert once == twice

    @pytest.mark.parametrize(
        "raw",
        [
            "A",  # single letter
            "Z9",  # letter + number
            "___A___B___",  # extra underscores
            "—EM–Dash—",  # various dashes
            "O'Connor",  # apostrophe path
        ],
    )
    def test_no_leading_or_trailing_underscores(self, raw):
        out = convert_to_snake_case(raw)
        assert not out.startswith("_")
        assert not out.endswith("_")
        assert "__" not in out  # collapsed underscores


class TestPascalCase:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("camelCase", "CamelCase"),
            ("CamelCase", "CamelCase"),
            ("snake_case_name", "SnakeCaseName"),
            ("kebab-case-name", "KebabCaseName"),
            (" already   spaced  name ", "AlreadySpacedName"),
            ("HTTPServerError", "HTTPServerError"),  # keep existing CAPS
            ("http_server_error", "HttpServerError"),  # do not promote to HTTP
            ("JSON2XML_converter", "JSON2XMLConverter"),  # digits + acronyms
            ("version2_update", "Version2Update"),
            ("mixOf CAPS And_Symbols", "MixOfCAPSAndSymbols"),
            ("O'Connor", "OConnor"),
            ("ends-with-punct!!!", "EndsWithPunct"),
            ("Ångström_unit", "ÅngströmUnit"),
            ("", ""),
        ],
    )
    def test_examples(self, raw, expected):
        assert convert_to_pascal_case(raw) == expected

    def test_idempotence(self):
        samples = [
            "CamelCase",
            "snake_case",
            "HTTPServer",
            "json2_xml",
            " spaced  out ",
        ]
        for s in samples:
            once = convert_to_pascal_case(s)
            twice = convert_to_pascal_case(once)
            assert once == twice
