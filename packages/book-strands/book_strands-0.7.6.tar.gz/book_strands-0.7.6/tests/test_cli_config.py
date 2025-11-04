import os
import tempfile
from unittest.mock import patch

from click.testing import CliRunner

from book_strands.cli import cli


def test_help_works_without_config():
    """Test that --help works even when config file doesn't exist."""
    runner = CliRunner()

    # Mock the config file path to a non-existent location
    with patch(
        "book_strands.utils.CONFIG_FILE_PATH", "~/.config/nonexistent-config.conf"
    ):
        result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Book Strands CLI tool" in result.output


def test_command_fails_without_config():
    """Test that commands fail with proper error when config file doesn't exist."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the config file path to a non-existent location
        with patch(
            "book_strands.utils.CONFIG_FILE_PATH", "~/.config/nonexistent-config.conf"
        ):
            result = runner.invoke(cli, ["agent", temp_dir, "test query"])

        assert result.exit_code == 1
        assert "ERROR:" in result.output
        assert "Config file not found" in result.output
        assert "Example configuration file content:" in result.output
        assert "user@example.com = password123" in result.output


def test_import_command_fails_without_config():
    """Test that import-local-books command fails with proper error when config file doesn't exist."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dummy input directory
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir)

        # Mock the config file path to a non-existent location
        with patch(
            "book_strands.utils.CONFIG_FILE_PATH", "~/.config/nonexistent-config.conf"
        ):
            result = runner.invoke(cli, ["import-local-books", input_dir, temp_dir])

        assert result.exit_code == 1
        assert "ERROR:" in result.output
        assert "Config file not found" in result.output
        assert "Example configuration file content:" in result.output
        assert "user@example.com = password123" in result.output


def test_command_fails_without_ebook_meta():
    """Test that commands fail with proper error when ebook-meta binary doesn't exist."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid config file
        config_file = os.path.join(temp_dir, "config.conf")
        with open(config_file, "w") as f:
            f.write("[zlib-logins]\nuser@example.com = password123\n")

        # Mock both config path and ebook-meta binary path
        with (
            patch("book_strands.utils.CONFIG_FILE_PATH", config_file),
            patch(
                "book_strands.utils.ebook_meta_binary",
                return_value="/nonexistent/ebook-meta",
            ),
        ):
            result = runner.invoke(cli, ["agent", temp_dir, "test query"])

        assert result.exit_code == 1
        assert "ERROR:" in result.output
        assert "ebook-meta binary not found" in result.output
        assert "To install Calibre" in result.output
        assert "https://calibre-ebook.com/download" in result.output
