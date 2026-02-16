from lovebirds.cli.list import table_to_html, table_to_text


class TestTableToHtml:
    def test_basic_output(self):
        headers = ["Name", "Age"]
        rows = [["Alice", 30], ["Bob", 25]]
        result = table_to_html(headers, rows)
        assert "<th>Name</th>" in result
        assert "<th>Age</th>" in result
        assert "<td>Alice</td>" in result
        assert "<td>30</td>" in result

    def test_html_escaping(self):
        headers = ["Data"]
        rows = [["<script>alert('xss')</script>"]]
        result = table_to_html(headers, rows)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_none_value(self):
        headers = ["Data"]
        rows = [[None]]
        result = table_to_html(headers, rows)
        # None values are rendered as a cross mark
        assert "\u274c" in result

    def test_empty_string_value(self):
        headers = ["Data"]
        rows = [[""]]
        result = table_to_html(headers, rows)
        # Empty strings are rendered as em-dash
        assert "\u2014" in result


class TestTableToText:
    def test_basic_output(self):
        headers = ["Name", "Age"]
        rows = [["Alice", 30], ["Bob", 25]]
        result = table_to_text(headers, rows)
        assert "Name" in result
        assert "Age" in result
        assert "Alice" in result
        assert "Bob" in result
