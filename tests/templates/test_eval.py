import pytest
from dataclasses import dataclass
from enum import Enum

import jinja2

from lovebirds.templates.eval import (
    eval_string,
    eval_variables,
    make_environment,
    to_dict_recursive,
)


class Color(Enum):
    red = "RED"
    blue = "BLUE"


@dataclass
class Point:
    x: int
    y: int

    @property
    def magnitude(self):
        return (self.x**2 + self.y**2) ** 0.5


class TestToDictRecursive:
    def test_primitives_pass_through(self):
        assert to_dict_recursive(42) == 42
        assert to_dict_recursive("hello") == "hello"
        assert to_dict_recursive(3.14) == 3.14
        assert to_dict_recursive(True) is True
        assert to_dict_recursive(None) is None

    def test_enum_returns_name(self):
        assert to_dict_recursive(Color.red) == "red"

    def test_dict_recurses(self):
        result = to_dict_recursive({"color": Color.blue, "count": 5})
        assert result == {"color": "blue", "count": 5}

    def test_list_recurses(self):
        result = to_dict_recursive([Color.red, 1, "text"])
        assert result == ["red", 1, "text"]

    def test_dataclass_to_dict(self):
        p = Point(x=3, y=4)
        result = to_dict_recursive(p)
        assert result["x"] == 3
        assert result["y"] == 4
        assert result["magnitude"] == 5.0

    def test_non_dataclass_object_raises(self):
        class Foo:
            pass

        with pytest.raises(ValueError, match="Cannot represent object"):
            to_dict_recursive(Foo())


class TestEvalString:
    def test_expression_with_percent(self):
        result = eval_string("%2+3", {})
        assert result == 5

    def test_template_rendering(self):
        result = eval_string("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_undefined_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="UndefinedError"):
            eval_string("{{ missing }}", {})

    def test_undefined_allowed_returns_undefined(self):
        # allow_undefined only works for %-prefixed expressions (not templates)
        result = eval_string("%missing", {}, allow_undefined=True)
        assert isinstance(result, jinja2.runtime.Undefined)

    def test_source_in_error_message(self):
        with pytest.raises(RuntimeError, match="my_source"):
            eval_string("{{ missing }}", {}, source="my_source")


class TestEvalVariables:
    def test_simple_substitution(self):
        # Dependencies must be ordered before templates when using {{ }} syntax
        variables = {"name": "World", "greeting": "Hello {{ name }}!"}
        result, complete = eval_variables(variables)
        assert complete is True
        assert result["greeting"] == "Hello World!"
        assert result["name"] == "World"

    def test_forward_references_with_expressions(self):
        # Forward references work with simple %-prefixed variable lookups;
        # the first pass returns Undefined, the second pass resolves.
        variables = {
            "greeting": "%name",
            "name": "Alice",
        }
        result, complete = eval_variables(variables)
        assert complete is True
        assert result["greeting"] == "Alice"
        assert result["name"] == "Alice"

    def test_nested_dicts(self):
        # Put dependency before the nested structure so it's available in root
        variables = {"val": "resolved", "outer": {"inner": "{{ val }}"}}
        result, complete = eval_variables(variables)
        assert complete is True
        assert result["outer"]["inner"] == "resolved"

    def test_nested_dict_non_string_values(self):
        variables = {"outer": {"count": 42, "flag": True}}
        result, complete = eval_variables(variables)
        assert complete is True
        assert result["outer"]["count"] == 42
        assert result["outer"]["flag"] is True

    def test_non_string_values_pass_through(self):
        variables = {"count": 42, "flag": True}
        result, complete = eval_variables(variables)
        assert complete is True
        assert result["count"] == 42
        assert result["flag"] is True


class TestMakeEnvironment:
    def test_returns_jinja_environment(self, tmp_path):
        env = make_environment([str(tmp_path)])
        assert isinstance(env, jinja2.Environment)

    def test_strict_undefined(self, tmp_path):
        env = make_environment([str(tmp_path)])
        assert env.undefined is jinja2.StrictUndefined

    def test_percent_line_prefix(self, tmp_path):
        env = make_environment([str(tmp_path)])
        assert env.line_statement_prefix == "%"
