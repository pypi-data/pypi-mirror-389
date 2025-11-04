import os
import tempfile
from unittest import mock
from unittest.mock import patch

import pytest
from strands.types.event_loop import Usage

from book_strands.constants import SUPPORTED_FORMATS
from book_strands.utils import (
    calculate_bedrock_cost,
    check_requirements,
    ensure_file_has_extension,
    file_extension,
    is_valid_ebook,
)


def test_file_extension():
    """Test file_extension function."""
    assert file_extension("/path/to/file.txt") == ".txt"
    assert file_extension("/path/to/file.TXT") == ".txt"
    assert file_extension("/path/to/file") == ""
    assert file_extension("/path.to/file") == ""
    assert file_extension("/path/to/file.tar.gz") == ".gz"


def test_calculate_bedrock_cost():
    """Test calculate_bedrock_cost function."""
    # Create a mock model and usage
    mock_model = mock.MagicMock()
    mock_model.get_config.return_value = {"model_id": "us.amazon.nova-pro-v1:0"}

    # Test with some token usage
    usage = Usage(inputTokens=1000, outputTokens=500, totalTokens=1500)
    cost = calculate_bedrock_cost(usage, mock_model)
    expected_cost = (1000 / 1000 * 0.0008) + (500 / 1000 * 0.0032)
    assert cost == expected_cost

    # Test with zero tokens
    usage = {"inputTokens": 0, "outputTokens": 0}
    cost = calculate_bedrock_cost(usage, mock_model)
    assert cost == 0

    # Test with unknown model
    mock_model.get_config.return_value = {"model_id": "unknown_model"}
    usage = {"inputTokens": 1000, "outputTokens": 500}
    cost = calculate_bedrock_cost(usage, mock_model)
    assert cost == 0


def test_ensure_file_has_extension():
    """Test ensure_file_has_extension function."""
    # Test adding extension
    assert ensure_file_has_extension("/path/to/file", "txt") == "/path/to/file.txt"

    # Test with extension that already has a dot
    assert ensure_file_has_extension("/path/to/file", ".txt") == "/path/to/file.txt"

    # Test replacing extension
    assert (
        ensure_file_has_extension("/path/to/file.pdf", "epub") == "/path/to/file.epub"
    )

    # Test with same extension
    assert ensure_file_has_extension("/path/to/file.txt", "txt") == "/path/to/file.txt"


def test_is_valid_ebook():
    """Test is_valid_ebook function."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
        tmp.write(b"dummy content")
        valid_path = tmp.name

    try:
        # Test with valid file
        result = is_valid_ebook(valid_path)
        assert result["status"] == "success"

        # Test with non-existent file
        result = is_valid_ebook("/nonexistent/file.epub")
        assert result["status"] == "error"
        assert "Source file not found" in result["message"]

        # Test with unsupported format
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
            tmp.write(b"dummy content")
            invalid_path = tmp.name

        try:
            result = is_valid_ebook(invalid_path)
            assert result["status"] == "error"
            assert "Unsupported file format" in result["message"]
            assert all(fmt in result["message"] for fmt in SUPPORTED_FORMATS)
        finally:
            os.unlink(invalid_path)
    finally:
        os.unlink(valid_path)


def test_check_requirements_all_good():
    """Test check_requirements when both config and binary exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid config file
        config_file = os.path.join(temp_dir, "config.conf")
        with open(config_file, "w") as f:
            f.write("[zlib-logins]\nuser@example.com = password123\n")

        # Create a mock executable binary
        binary_file = os.path.join(temp_dir, "ebook-meta")
        with open(binary_file, "w") as f:
            f.write('#!/bin/bash\necho "mock ebook-meta"')
        os.chmod(binary_file, 0o755)

        with (
            patch("book_strands.utils.CONFIG_FILE_PATH", config_file),
            patch("book_strands.utils.ebook_meta_binary", return_value=binary_file),
        ):
            # Should not exit or raise exception
            check_requirements()


def test_check_requirements_missing_config():
    """Test check_requirements when config file is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock executable binary
        binary_file = os.path.join(temp_dir, "ebook-meta")
        with open(binary_file, "w") as f:
            f.write('#!/bin/bash\necho "mock ebook-meta"')
        os.chmod(binary_file, 0o755)

        with (
            patch("book_strands.utils.CONFIG_FILE_PATH", "/nonexistent/config.conf"),
            patch("book_strands.utils.ebook_meta_binary", return_value=binary_file),
        ):
            with pytest.raises(SystemExit) as exc_info:
                check_requirements()
            assert exc_info.value.code == 1


def test_check_requirements_missing_binary():
    """Test check_requirements when ebook-meta binary is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid config file
        config_file = os.path.join(temp_dir, "config.conf")
        with open(config_file, "w") as f:
            f.write("[zlib-logins]\nuser@example.com = password123\n")

        with (
            patch("book_strands.utils.CONFIG_FILE_PATH", config_file),
            patch(
                "book_strands.utils.ebook_meta_binary",
                return_value="/nonexistent/ebook-meta",
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                check_requirements()
            assert exc_info.value.code == 1


def test_check_requirements_non_executable_binary():
    """Test check_requirements when ebook-meta binary exists but is not executable."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a valid config file
        config_file = os.path.join(temp_dir, "config.conf")
        with open(config_file, "w") as f:
            f.write("[zlib-logins]\nuser@example.com = password123\n")

        # Create a non-executable binary
        binary_file = os.path.join(temp_dir, "ebook-meta")
        with open(binary_file, "w") as f:
            f.write('#!/bin/bash\necho "mock ebook-meta"')
        os.chmod(binary_file, 0o644)  # Not executable

        with (
            patch("book_strands.utils.CONFIG_FILE_PATH", config_file),
            patch("book_strands.utils.ebook_meta_binary", return_value=binary_file),
        ):
            with pytest.raises(SystemExit) as exc_info:
                check_requirements()
            assert exc_info.value.code == 1


def test_check_requirements_both_missing():
    """Test check_requirements when both config and binary are missing."""
    with (
        patch("book_strands.utils.CONFIG_FILE_PATH", "/nonexistent/config.conf"),
        patch(
            "book_strands.utils.ebook_meta_binary",
            return_value="/nonexistent/ebook-meta",
        ),
    ):
        with pytest.raises(SystemExit) as exc_info:
            check_requirements()
        assert exc_info.value.code == 1
