"""Setup command for initializing Frappe/ERPNext development environment."""

import click
import sys
import shutil
import os
from pathlib import Path

from ..utils import (
    Colors, print_info, print_success, print_warning, print_error,
    run_command
)


def create_bench_shortcuts(project_dir):
    """Create system shortcuts for common bench commands.
    
    Creates executabl    print(f"     {Colors.YELLOW}ws create-site{Colors.NC}")
    print("   • Install apps:")
    print(f"     {Colors.YELLOW}ws fetch-app{Colors.NC}")cripts in ~/.local/bin (Linux/macOS) or user's PATH
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
    
    # Add bin directory to PATH reminder
    if success_count > 0 and not sys.platform.startswith('win'):
        # Check if ~/.local/bin is in PATH
        path_env = os.environ.get('PATH', '')
        local_bin_str = str(bin_dir)
        if local_bin_str not in path_env:
            print()
            print_warning("~/.local/bin is not in your PATH!")
            print_info("Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.):")
            print(f"    {Colors.YELLOW}export PATH=\"$HOME/.local/bin:$PATH\"{Colors.NC}")
            print_info("Then restart your terminal or run: source ~/.bashrc")
    
    return success_count == len(shortcuts)


@click.command()
@click.argument('project_name')
@click.option('--frappe-version', 
              default='v15.78.1',
              help='Frappe version to install (default: v15.78.1)')
@click.option('--python-path',
              default='python3',
              help='Path to Python executable (default: python3)')
@click.option('--force',
              is_flag=True,
              help='Force setup even if directory exists')
@click.option('--install-docs',
              is_flag=True,
              default=True,
              help='Install TECHNICAL_DOCS.md template (default: True)')
@click.option('--init-git',
              is_flag=True,
              help='Initialize Git repository')
@click.option('--create-shortcuts',
              is_flag=True,
              help='Create system shortcuts for bench commands (bs, bm, bcc, br, bef)')
def setup(project_name, frappe_version, python_path, force, install_docs, init_git, create_shortcuts):
    """Setup Frappe/ERPNext development environment.
    
    This command creates a new project directory, sets up a virtual environment,
    installs frappe-bench, initializes a new bench with the specified Frappe version,
    and optionally installs documentation templates and initializes a Git repository.
    
    Arguments:
        PROJECT_NAME: Name of the project directory to create
    """
    # Get the current working directory where the command is run
    current_dir = Path.cwd()
    
    # Create project directory path
    project_dir = current_dir / project_name
    
    print()
    print(f"{Colors.BLUE}{'=' * 63}{Colors.NC}")
    print(f"{Colors.GREEN}  Frappe/ERPNext Environment Setup{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 63}{Colors.NC}")
    print()
    print_info(f"Project Name: {project_name}")
    print_info(f"Current Directory: {current_dir}")
    print_info(f"Project Directory: {project_dir}")
    print_info(f"Frappe Version: {frappe_version}")
    print()
    
    # Check if project directory already exists
    if project_dir.exists() and not force:
        print_warning(f"Directory '{project_name}' already exists!")
        if not click.confirm("Do you want to continue anyway?"):
            print_info("Setup cancelled.")
            return
    
    # Create project directory
    print_info(f"Creating project directory: {project_name}")
    project_dir.mkdir(exist_ok=True)
    print_success("Project directory created")
    print()
    
    # Check if virtual environment already exists
    env_dir = project_dir / "env"
    if env_dir.exists() and not force:
        print_warning("Virtual environment already exists!")
        if not click.confirm("Do you want to continue anyway?"):
            print_info("Setup cancelled.")
            return
    
    # ═══════════════════════════════════════════════════════════
    # CREATE VIRTUAL ENVIRONMENT
    # ═══════════════════════════════════════════════════════════
    print_info("Setting up virtual environment...")
    
    if not run_command(f'{python_path} -m venv "{env_dir}"', cwd=project_dir):
        print_error("Failed to create virtual environment!")
        sys.exit(1)
    
    print_success("Virtual environment created")
    print()
    
    # Paths to executables in virtual environment
    python_exe = env_dir / "bin" / "python"
    pip_exe = env_dir / "bin" / "pip"
    
    # ═══════════════════════════════════════════════════════════
    # UPGRADE PIP
    # ═══════════════════════════════════════════════════════════
    print_info("Upgrading pip...")
    if not run_command(f'"{python_exe}" -m pip install --quiet --upgrade pip', 
                      cwd=project_dir, quiet=True):
        print_error("Failed to upgrade pip!")
        sys.exit(1)
    
    print_success("pip upgraded")
    print()
    
    # ═══════════════════════════════════════════════════════════
    # INSTALL FRAPPE-BENCH
    # ═══════════════════════════════════════════════════════════
    print_info("Installing frappe-bench...")
    if not run_command(f'"{python_exe}" -m pip install --quiet frappe-bench', 
                      cwd=project_dir, quiet=True):
        print_error("Failed to install frappe-bench!")
        sys.exit(1)
    
    print_success("frappe-bench installed")
    print()
    
    # ═══════════════════════════════════════════════════════════
    # INSTALL WHEEL
    # ═══════════════════════════════════════════════════════════
    print_info("Installing wheel...")
    if not run_command(f'"{python_exe}" -m pip install --quiet wheel', 
                      cwd=project_dir, quiet=True):
        print_error("Failed to install wheel!")
        sys.exit(1)
    
    print_success("wheel installed")
    print()
    
    # ═══════════════════════════════════════════════════════════
    # INITIALIZE BENCH
    # ═══════════════════════════════════════════════════════════
    print_info("Getting frappe and initializing bench...")
    print_warning("This may take a while...")
    print()
    
    # Change to parent directory to run bench init
    parent_dir = project_dir.parent
    

    bench_cmd = (f'source "{env_dir}/bin/activate" && '
                f'bench init {project_name} --frappe-branch {frappe_version} --ignore-exist')
    
    # first attempt
    if not run_command(bench_cmd, cwd=parent_dir, shell=True, check=True, quiet=False):
        print_error("Failed to initialize bench for the first time!")
        print_info("Trying another path...")
        bench_cmd = (f'source "{env_dir}/bin/activate" && '
                    f'bench init {project_name} --frappe-branch {frappe_version} --ignore-exist')
        if not run_command(bench_cmd, cwd=parent_dir, shell=True, check=True, quiet=False): 
            print_error("Failed to initialize bench for the second time!")
            sys.exit(1)
    
    print()
    print_success("Bench initialized successfully!")
    print()
    
    # ═══════════════════════════════════════════════════════════
    # INSTALL TECHNICAL DOCS
    # ═══════════════════════════════════════════════════════════
    if install_docs:
        print_info("Installing TECHNICAL_DOCS.md template...")
        try:
            # Try to get the template file from the package
            import importlib.resources
            try:
                # Python 3.9+
                with importlib.resources.files("ws_frappe_cli.templates.docs").joinpath("TECHNICAL_DOCS.md").open("r") as f:
                    docs_content = f.read()
            except AttributeError:
                # Python 3.8 fallback
                with importlib.resources.open_text("ws_frappe_cli.templates.docs", "TECHNICAL_DOCS.md") as f:
                    docs_content = f.read()
            
            # Write to the root directory
            docs_file = project_dir / "TECHNICAL_DOCS.md"
            with open(docs_file, "w") as f:
                f.write(docs_content)
            
            print_success("TECHNICAL_DOCS.md installed in root directory")
        except Exception as e:
            print_warning(f"Could not install TECHNICAL_DOCS.md: {e}")
        print()
    
    # ═══════════════════════════════════════════════════════════
    # INITIALIZE GIT REPOSITORY
    # ═══════════════════════════════════════════════════════════
    if init_git:
        print_info("Initializing Git repository...")
        
        # Check if Git is available
        if not run_command("git --version", quiet=True):
            print_error("Git is not installed or not available in PATH!")
            print_warning("Skipping Git initialization.")
        else:
            git_dir = project_dir / ".git"
            if git_dir.exists():
                print_warning("Git repository already exists!")
            else:
                if run_command("git init", cwd=project_dir, quiet=True):
                    print_success("Git repository initialized")
                    
                    # Create a basic .gitignore for Frappe projects
                    gitignore_content = """# Frappe/ERPNext specific
env/
sites/*/private/
sites/*/public/
sites/*/locks/
*.pyc
__pycache__/
.DS_Store
*.log
logs/
node_modules/
.vscode/
.idea/

# Bench specific
sites/apps.txt
sites/common_site_config.json
sites/currentsite.txt

# Python
*.egg-info/
build/
dist/
.coverage
.pytest_cache/
"""
                    gitignore_file = project_dir / ".gitignore"
                    with open(gitignore_file, "w") as f:
                        f.write(gitignore_content)
                    print_success(".gitignore created")
                    
                    # Make initial commit if docs were installed
                    if install_docs and (project_dir / "TECHNICAL_DOCS.md").exists():
                        run_command("git add TECHNICAL_DOCS.md .gitignore", cwd=project_dir, quiet=True)
                        run_command('git commit -m "Initial commit: Add technical docs and gitignore"', cwd=project_dir, quiet=True)
                        print_success("Initial commit created")
                else:
                    print_error("Failed to initialize Git repository")
        print()
    
    # ═══════════════════════════════════════════════════════════
    # CREATE SYSTEM SHORTCUTS
    # ═══════════════════════════════════════════════════════════
    if create_shortcuts:
        print_info("Creating system shortcuts for bench commands...")
        shortcuts_created = create_bench_shortcuts(project_dir)
        if shortcuts_created:
            print_success("Bench shortcuts created successfully")
            print_info("Available shortcuts: bs, bm, bcc, br, bef")
        else:
            print_warning("Some shortcuts could not be created")
        print()
    
    # ═══════════════════════════════════════════════════════════
    # FINAL MESSAGE
    # ═══════════════════════════════════════════════════════════
    print()
    print(f"{Colors.BLUE}{'=' * 63}{Colors.NC}")
    print(f"{Colors.GREEN}  Setup Completed Successfully!{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 63}{Colors.NC}")
    print()
    print_success("Your Frappe development environment is ready!")
    
    if install_docs:
        print_success("TECHNICAL_DOCS.md template is available in the root directory")
    
    if init_git:
        print_success("Git repository has been initialized")
    
    if create_shortcuts:
        print_success("Bench shortcuts have been created")
    
    print()
    print_info("Next steps:")
    print(f"  1. Navigate to the project directory:")
    print(f"     {Colors.YELLOW}cd {project_name}{Colors.NC}")
    print(f"  2. Activate the virtual environment:")
    print(f"     {Colors.YELLOW}source env/bin/activate{Colors.NC}")
    print(f"  3. Create a new site:")
    print(f"     {Colors.YELLOW}ws-frappe-cli create-site{Colors.NC}")
    print(f"  4. Install apps:")
    print(f"     {Colors.YELLOW}ws-frappe-cli fetch-app{Colors.NC}")
    print(f"  5. Start the development server:")
    print(f"     {Colors.YELLOW}bench start{Colors.NC}")
    
    if create_shortcuts:
        print()
        print_info("Available shortcuts (from any terminal):")
        print(f"  • {Colors.YELLOW}bs{Colors.NC}  - bench start")
        print(f"  • {Colors.YELLOW}bm{Colors.NC}  - bench migrate") 
        print(f"  • {Colors.YELLOW}bcc{Colors.NC} - bench clear-cache")
        print(f"  • {Colors.YELLOW}br{Colors.NC}  - bench restart")
        print(f"  • {Colors.YELLOW}bef{Colors.NC} - bench export-fixtures")
    
    if install_docs:
        print()
        print_info("Documentation:")
        print(f"  • Review and customize TECHNICAL_DOCS.md for your project")
        print(f"  • Update app versions and customizations as needed")
    
    if init_git:
        print()
        print_info("Git workflow:")
        print(f"  • Add your remote repository: {Colors.YELLOW}git remote add origin <your-repo-url>{Colors.NC}")
        print(f"  • Make your first commit with project files")
    
    print()


if __name__ == "__main__":
    setup()