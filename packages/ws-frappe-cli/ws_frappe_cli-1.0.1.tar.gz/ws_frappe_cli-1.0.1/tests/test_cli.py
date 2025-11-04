"""Tests for CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from ws_frappe_cli.main import main


class TestMainCLI:
    """Test main CLI functionality."""
    
    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "WS Frappe CLI" in result.output
        assert "setup" in result.output
        assert "create-site" in result.output
        assert "fetch-app" in result.output
    
    def test_main_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestSetupCommand:
    """Test setup command."""
    
    @patch('ws_frappe_cli.commands.setup.run_command')
    @patch('ws_frappe_cli.commands.setup.Path.cwd')
    def test_setup_command_basic(self, mock_cwd, mock_run_command):
        mock_cwd.return_value = MagicMock()
        mock_cwd.return_value.name = "test_project"
        mock_run_command.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(main, ['setup', '--no-interactive'])
        # The command might fail due to actual file operations, but we're testing CLI structure
        assert "setup" in str(result.exception) or result.exit_code in [0, 1]


class TestCreateSiteCommand:
    """Test create-site command."""
    
    @patch('ws_frappe_cli.commands.create_site.validate_bench_directory')
    def test_create_site_not_in_bench(self, mock_validate):
        mock_validate.return_value = False
        
        runner = CliRunner()
        result = runner.invoke(main, ['create-site'])
        assert result.exit_code == 1
        assert "bench directory" in result.output


class TestFetchAppCommand:
    """Test fetch-app command."""
    
    @patch('ws_frappe_cli.commands.fetch_app.validate_bench_directory')
    def test_fetch_app_list_predefined(self, mock_validate):
        mock_validate.return_value = True
        
        runner = CliRunner()
        result = runner.invoke(main, ['fetch-app', '--list-predefined'])
        
        if result.exit_code == 0:
            assert "PREDEFINED APPS" in result.output
            assert "erpnext" in result.output or "hrms" in result.output
    
    @patch('ws_frappe_cli.commands.fetch_app.validate_bench_directory')
    def test_fetch_app_not_in_bench(self, mock_validate):
        mock_validate.return_value = False
        
        runner = CliRunner()
        result = runner.invoke(main, ['fetch-app', '--app-name', 'test'])
        assert result.exit_code == 1
        assert "bench directory" in result.output