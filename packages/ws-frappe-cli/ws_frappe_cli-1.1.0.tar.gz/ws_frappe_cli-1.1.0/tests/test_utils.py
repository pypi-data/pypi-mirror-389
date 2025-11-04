"""Tests for utility functions."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from ws_frappe_cli.utils import (
    print_info, print_success, print_warning, print_error,
    run_command, validate_bench_directory, prompt_yes_no
)


class TestColoredPrint:
    """Test colored print functions."""
    
    def test_print_info(self, capsys):
        print_info("Test info message")
        captured = capsys.readouterr()
        assert "Test info message" in captured.out
        assert "ℹ" in captured.out
    
    def test_print_success(self, capsys):
        print_success("Test success message")
        captured = capsys.readouterr()
        assert "Test success message" in captured.out
        assert "✓" in captured.out
    
    def test_print_warning(self, capsys):
        print_warning("Test warning message")
        captured = capsys.readouterr()
        assert "Test warning message" in captured.out
        assert "⚠" in captured.out
    
    def test_print_error(self, capsys):
        print_error("Test error message")
        captured = capsys.readouterr()
        assert "Test error message" in captured.out
        assert "✗" in captured.out


class TestRunCommand:
    """Test run_command function."""
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = run_command("echo hello", quiet=True)
        assert result is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "echo")
        result = run_command("false", quiet=True)
        assert result is False


class TestValidateBenchDirectory:
    """Test bench directory validation."""
    
    def test_validate_bench_directory_valid(self, mock_bench_dir):
        assert validate_bench_directory(mock_bench_dir) is True
    
    def test_validate_bench_directory_invalid(self, mock_non_bench_dir):
        assert validate_bench_directory(mock_non_bench_dir) is False
    
    def test_validate_bench_directory_missing_sites(self, temp_dir):
        # Create only apps directory
        apps_dir = temp_dir / "apps"
        apps_dir.mkdir()
        assert validate_bench_directory(temp_dir) is False


class TestPromptYesNo:
    """Test yes/no prompts."""
    
    @patch('builtins.input', return_value='y')
    def test_prompt_yes_no_yes(self, mock_input):
        result = prompt_yes_no("Continue?", "n")
        assert result is True
    
    @patch('builtins.input', return_value='n')
    def test_prompt_yes_no_no(self, mock_input):
        result = prompt_yes_no("Continue?", "n")
        assert result is False
    
    @patch('builtins.input', return_value='')
    def test_prompt_yes_no_default_yes(self, mock_input):
        result = prompt_yes_no("Continue?", "y")
        assert result is True
    
    @patch('builtins.input', return_value='')
    def test_prompt_yes_no_default_no(self, mock_input):
        result = prompt_yes_no("Continue?", "n")
        assert result is False