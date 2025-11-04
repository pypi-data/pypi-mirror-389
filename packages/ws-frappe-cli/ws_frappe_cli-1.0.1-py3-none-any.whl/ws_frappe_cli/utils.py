"""Utility functions and classes shared across the CLI."""

import sys
import subprocess
from pathlib import Path


# Color codes for better UX
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_info(message):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.NC} {message}")


def print_success(message):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_warning(message):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


def print_error(message):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def run_command(cmd, cwd=None, shell=True, check=True, quiet=False):
    """Run a command and handle errors."""
    try:
        if quiet:
            result = subprocess.run(
                cmd,
                shell=shell,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                cmd,
                shell=shell,
                cwd=cwd,
                check=check,
                text=True
            )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        if hasattr(e, 'stderr') and e.stderr:
            print(e.stderr)
        return False


def get_project_root():
    """Get the project root directory."""
    return Path.cwd()


def validate_bench_directory(path=None):
    """Validate if the current directory is a bench directory."""
    if path is None:
        path = get_project_root()
    else:
        path = Path(path)
    
    bench_markers = [
        path / "sites" / "apps.txt",
        path / "apps",
        path / "sites"
    ]
    
    return all(marker.exists() for marker in bench_markers)


def prompt_input(prompt, default="", is_password=False):
    """Prompt for input with a default value."""
    import getpass
    
    if default:
        display_prompt = f"{Colors.BLUE}?{Colors.NC} {prompt} [{Colors.GREEN}{default}{Colors.NC}]: "
    else:
        display_prompt = f"{Colors.BLUE}?{Colors.NC} {prompt}: "
    
    if is_password:
        user_input = getpass.getpass(display_prompt)
    else:
        user_input = input(display_prompt).strip()
    
    return user_input if user_input else default


def prompt_yes_no(prompt, default="n"):
    """Prompt yes/no questions."""
    if default.lower() == "y":
        display_prompt = f"{Colors.BLUE}?{Colors.NC} {prompt} [{Colors.GREEN}Y{Colors.NC}/n]: "
    else:
        display_prompt = f"{Colors.BLUE}?{Colors.NC} {prompt} [y/{Colors.GREEN}N{Colors.NC}]: "
    
    response = input(display_prompt).strip().lower()
    
    if not response:
        response = default
    
    return response in ['y', 'yes']