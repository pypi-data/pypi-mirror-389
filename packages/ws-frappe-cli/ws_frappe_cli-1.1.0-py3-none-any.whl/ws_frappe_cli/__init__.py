"""
WS Frappe CLI - A command-line tool for Frappe/ERPNext development environment management.

This package provides utilities for setting up, configuring, and managing
Frappe/ERPNext development environments.
"""

__version__ = "0.10.0"
__author__ = "HHH"
__email__ = "hasanhajhasan98@gmail.com"
__description__ = "A command-line tool for Frappe/ERPNext development environment management"

from .main import main, cli

__all__ = ["main", "cli"]