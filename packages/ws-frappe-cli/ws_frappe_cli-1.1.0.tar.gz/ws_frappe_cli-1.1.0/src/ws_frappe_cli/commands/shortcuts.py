"""Shortcuts command for managing bench command shortcuts."""

import click
import os
import sys
from pathlib import Path

from ..utils import (
    Colors, print_info, print_success, print_warning, print_error,
    validate_bench_directory
)


def create_bench_shortcuts(project_dir):
    """Create system shortcuts for common bench commands.
    
    Creates executable scripts in ~/.local/bin (Linux/macOS) or user's PATH
    for quick access to bench commands.
    """
    shortcuts = {
        'bs': 'bench start',
        'bm': 'bench migrate',
        'bcc': 'bench clear-cache',
        'br': 'bench restart', 
        'bef': 'bench export-fixtures'
    }
    
    success_count = 0
    
    # Determine the bin directory based on OS
    if sys.platform.startswith('win'):
        # Windows: Use user's Scripts directory
        bin_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps"
        extension = '.cmd'
    else:
        # Linux/macOS: Use ~/.local/bin
        bin_dir = Path.home() / ".local" / "bin"
        extension = ''
    
    # Create bin directory if it doesn't exist
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    for shortcut, command in shortcuts.items():
        try:
            script_path = bin_dir / f"{shortcut}{extension}"
            
            if sys.platform.startswith('win'):
                # Windows batch script
                script_content = f"""@echo off
cd /d "{project_dir}"
if exist "env\\Scripts\\activate.bat" (
    call env\\Scripts\\activate.bat
    {command} %*
) else (
    echo Error: Virtual environment not found in {project_dir}
    echo Please run ws setup first
    exit /b 1
)
"""
            else:
                # Unix shell script
                script_content = f"""#!/bin/bash
# Bench shortcut: {shortcut} -> {command}
# Created by ws-frappe-cli

PROJECT_DIR="{project_dir}"

# Check if we're in a bench directory or navigate to the project directory
if [ ! -f "./sites/apps.txt" ] && [ ! -f "$PROJECT_DIR/sites/apps.txt" ]; then
    if [ -d "$PROJECT_DIR" ]; then
        cd "$PROJECT_DIR"
    else
        echo "Error: Bench directory not found. Please run from a bench directory or ensure $PROJECT_DIR exists."
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -f "./env/bin/activate" ]; then
    source ./env/bin/activate
elif [ -f "$PROJECT_DIR/env/bin/activate" ]; then
    source "$PROJECT_DIR/env/bin/activate"
fi

# Run the bench command
{command} "$@"
"""
            
            # Write the script
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make executable on Unix systems
            if not sys.platform.startswith('win'):
                os.chmod(script_path, 0o755)
            
            success_count += 1
            print_info(f"Created shortcut: {shortcut} -> {command}")
            
        except Exception as e:
            print_warning(f"Failed to create shortcut '{shortcut}': {e}")
    
    return success_count == len(shortcuts)


def remove_bench_shortcuts():
    """Remove bench shortcuts from the system."""
    shortcuts = ['bs', 'bm', 'bcc', 'br', 'bef']
    
    # Determine the bin directory based on OS
    if sys.platform.startswith('win'):
        bin_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps"
        extension = '.cmd'
    else:
        bin_dir = Path.home() / ".local" / "bin"
        extension = ''
    
    removed_count = 0
    for shortcut in shortcuts:
        script_path = bin_dir / f"{shortcut}{extension}"
        if script_path.exists():
            try:
                script_path.unlink()
                print_info(f"Removed shortcut: {shortcut}")
                removed_count += 1
            except Exception as e:
                print_warning(f"Failed to remove shortcut '{shortcut}': {e}")
    
    return removed_count


@click.command()
@click.option('--remove',
              is_flag=True,
              help='Remove existing bench shortcuts')
@click.option('--list',
              'list_shortcuts',
              is_flag=True,
              help='List available shortcuts')
def shortcuts(remove, list_shortcuts):
    """Manage bench command shortcuts.
    
    Create system-wide shortcuts for common bench commands:
    - bs: bench start
    - bm: bench migrate  
    - bcc: bench clear-cache
    - br: bench restart
    - bef: bench export-fixtures
    """
    if list_shortcuts:
        print()
        print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")
        print(f"{Colors.GREEN}  Available Bench Shortcuts{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")
        print()
        print(f"  {Colors.YELLOW}bs{Colors.NC}   - bench start")
        print(f"  {Colors.YELLOW}bm{Colors.NC}   - bench migrate")
        print(f"  {Colors.YELLOW}bcc{Colors.NC}  - bench clear-cache")
        print(f"  {Colors.YELLOW}br{Colors.NC}   - bench restart")
        print(f"  {Colors.YELLOW}bef{Colors.NC}  - bench export-fixtures")
        print()
        print_info("Run 'ws shortcuts' to create these shortcuts")
        print_info("Run 'ws shortcuts --remove' to remove them")
        print()
        return
    
    if remove:
        print_info("Removing bench shortcuts...")
        removed_count = remove_bench_shortcuts()
        if removed_count > 0:
            print_success(f"Removed {removed_count} shortcuts")
        else:
            print_warning("No shortcuts found to remove")
        return
    
    # Create shortcuts - check if we're in a bench directory
    current_dir = Path.cwd()
    if not validate_bench_directory(current_dir):
        print_error("This command must be run from a bench directory!")
        print_info("Please navigate to a bench directory or run 'ws setup' first.")
        sys.exit(1)
    
    print_info("Creating bench shortcuts...")
    success = create_bench_shortcuts(current_dir)
    
    if success:
        print_success("All shortcuts created successfully!")
        print()
        print_info("Available shortcuts:")
        print(f"  • {Colors.YELLOW}bs{Colors.NC}  - bench start")
        print(f"  • {Colors.YELLOW}bm{Colors.NC}  - bench migrate") 
        print(f"  • {Colors.YELLOW}bcc{Colors.NC} - bench clear-cache")
        print(f"  • {Colors.YELLOW}br{Colors.NC}  - bench restart")
        print(f"  • {Colors.YELLOW}bef{Colors.NC} - bench export-fixtures")
        
        # Add bin directory to PATH reminder
        if not sys.platform.startswith('win'):
            # Check if ~/.local/bin is in PATH
            path_env = os.environ.get('PATH', '')
            local_bin = str(Path.home() / ".local" / "bin")
            if local_bin not in path_env:
                print()
                print_warning("~/.local/bin is not in your PATH!")
                print_info("Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.):")
                print(f"    {Colors.YELLOW}export PATH=\"$HOME/.local/bin:$PATH\"{Colors.NC}")
                print_info("Then restart your terminal or run: source ~/.bashrc")
    else:
        print_error("Some shortcuts could not be created")
    
    print()


if __name__ == "__main__":
    shortcuts()