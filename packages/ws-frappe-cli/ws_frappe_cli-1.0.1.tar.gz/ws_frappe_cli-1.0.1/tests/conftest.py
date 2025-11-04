"""Test configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_bench_dir(temp_dir):
    """Create a mock bench directory structure."""
    # Create bench directory structure
    sites_dir = temp_dir / "sites"
    apps_dir = temp_dir / "apps"
    
    sites_dir.mkdir()
    apps_dir.mkdir()
    
    # Create apps.txt file
    apps_txt = sites_dir / "apps.txt"
    apps_txt.write_text("frappe\nerpnext\n")
    
    # Create mock app directories
    frappe_dir = apps_dir / "frappe"
    erpnext_dir = apps_dir / "erpnext"
    frappe_dir.mkdir()
    erpnext_dir.mkdir()
    
    # Create mock site
    test_site = sites_dir / "test.localhost"
    test_site.mkdir()
    
    return temp_dir


@pytest.fixture
def mock_non_bench_dir(temp_dir):
    """Create a non-bench directory for testing validation."""
    return temp_dir