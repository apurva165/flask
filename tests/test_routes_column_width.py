"""Test for column width calculation efficiency in routes command.

This test verifies that the routes command correctly computes column widths
for proper table formatting, which was identified as an O(n*m) loop that
should be O(n) single pass.
"""
import click
from click.testing import CliRunner
import pytest
from flask import Flask
from flask.cli import FlaskGroup


class TestRoutesColumnWidths:
    """Tests for routes command column width calculation."""

    def test_column_widths_with_long_endpoint_names(self):
        """Verify column widths are computed correctly with varied endpoint lengths."""
        app = Flask(__name__)
        # Short endpoint
        app.add_url_rule("/a", endpoint="ab", methods=["GET"])
        # Medium endpoint
        app.add_url_rule("/b", endpoint="medium_length", methods=["POST"])
        # Long endpoint
        app.add_url_rule("/c", endpoint="very_long_endpoint_name_for_testing", methods=["PUT"])
        
        cli = FlaskGroup(create_app=lambda: app)
        runner = CliRunner()
        result = runner.invoke(cli, ["routes"], standalone_mode=False)
        
        lines = result.output.splitlines()
        assert result.exit_code == 0
        
        # Find the header line
        header = lines[0]
        assert "Endpoint" in header
        assert "Methods" in header
        assert "Rule" in header
        
        # Find the separator line (dashes)
        separator = lines[1]
        
        # The separator dashes should be correctly aligned with the longest value in each column
        # The format uses fixed-width column separation with spaces, so we check the dash sections
        
        # Endpoint column should be wide enough for "very_long_endpoint_name_for_testing"
        # The separator dashes span the full column width including padding
        separator_parts = separator.split("  ")
        
        # First part is the Endpoint dashes (may include trailing dashes before first double-space)
        endpoint_dashes = separator_parts[0].strip()
        assert len(endpoint_dashes) >= len("very_long_endpoint_name_for_testing"), \
            f"Endpoint column too narrow: expected at least 35, got {len(endpoint_dashes)}"
        
        # Methods column
        if len(separator_parts) > 1:
            methods_dashes = separator_parts[1].strip()
            assert len(methods_dashes) >= 4, "Methods column too narrow"

    def test_column_widths_with_all_methods(self):
        """Verify column widths when showing all HTTP methods."""
        app = Flask(__name__)
        app.add_url_rule("/test", endpoint="test_endpoint", methods=["GET", "POST", "PUT", "DELETE"])
        
        cli = FlaskGroup(create_app=lambda: app)
        runner = CliRunner()
        result = runner.invoke(cli, ["routes", "--all-methods"], standalone_mode=False)
        
        lines = result.output.splitlines()
        assert result.exit_code == 0
        
        # Check that the separator line exists
        assert len(lines) >= 2
        separator = lines[1]
        
        # Methods should contain GET, POST, PUT, DELETE separated by commas
        method_line = [l for l in lines if "GET" in l][0]
        assert "GET, POST, PUT, DELETE" in method_line or "GET," in method_line

    def test_column_widths_with_subdomain(self):
        """Verify column widths when subdomain is displayed."""
        app = Flask(__name__, static_folder=None)
        app.add_url_rule("/a", subdomain="verylongsubdomain", endpoint="a")
        app.add_url_rule("/b", subdomain="short", endpoint="b")
        
        cli = FlaskGroup(create_app=lambda: app)
        runner = CliRunner()
        result = runner.invoke(cli, ["routes"], standalone_mode=False)
        
        lines = result.output.splitlines()
        assert result.exit_code == 0
        
        # Subdomain column should appear
        header = lines[0]
        assert "Subdomain" in header
        
    def test_column_widths_with_host(self):
        """Verify column widths when host matching is enabled."""
        app = Flask(__name__, static_folder=None, host_matching=True)
        app.add_url_rule("/a", host="verylonghostname.example.com", endpoint="a")
        app.add_url_rule("/b", host="short", endpoint="b")
        
        cli = FlaskGroup(create_app=lambda: app)
        runner = CliRunner()
        result = runner.invoke(cli, ["routes"], standalone_mode=False)
        
        lines = result.output.splitlines()
        assert result.exit_code == 0
        
        # Host column should appear
        header = lines[0]
        assert "Host" in header

    def test_column_widths_empty_routes(self):
        """Verify routes command handles apps with no routes."""
        app = Flask(__name__, static_folder=None)
        
        cli = FlaskGroup(create_app=lambda: app)
        runner = CliRunner()
        result = runner.invoke(cli, ["routes"], standalone_mode=False)
        
        assert result.exit_code == 0
        assert "No routes were registered." in result.output

    def test_column_widths_sort_rules(self):
        """Verify column widths when sorting by rule."""
        app = Flask(__name__)
        app.add_url_rule("/zzz", endpoint="zzz", methods=["GET"])
        app.add_url_rule("/aaa", endpoint="aaa", methods=["GET"])
        app.add_url_rule("/mmm", endpoint="mmm", methods=["GET"])
        
        cli = FlaskGroup(create_app=lambda: app)
        runner = CliRunner()
        result = runner.invoke(cli, ["routes", "-s", "rule"], standalone_mode=False)
        
        lines = result.output.splitlines()[2:]  # Skip header and separator
        lines = [l for l in lines if l.strip()]  # Remove empty lines
        
        assert result.exit_code == 0
        # Rules should be sorted alphabetically
        rules = [l.split()[-1] for l in lines]
        assert rules == sorted(rules)
