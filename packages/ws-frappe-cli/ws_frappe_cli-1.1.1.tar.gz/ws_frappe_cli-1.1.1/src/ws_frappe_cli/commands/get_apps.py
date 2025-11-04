"""Get Apps command for installing apps from apps.json configuration."""

import click
import json
import subprocess
import sys
import os
import urllib.request
import urllib.parse
import tempfile
import shutil
from pathlib import Path

from ..utils import (
    Colors, print_info, print_success, print_warning, print_error,
    validate_bench_directory, prompt_yes_no
)


def load_apps_config(apps_json_path):
    """Load apps configuration from apps.json file."""
    try:
        with open(apps_json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print_error(f"{apps_json_path} not found")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Error parsing {apps_json_path}: {e}")
        return None


def fetch_apps_from_github(github_url, project_name):
    """Fetch apps configuration from GitHub repository.
    
    Supports both public and private repositories by trying multiple methods:
    1. Direct HTTPS access (for public repos)
    2. Git clone with credentials (for private repos)
    """
    # Try direct HTTPS access first (works for public repos)
    apps_config = try_direct_https_fetch(github_url, project_name)
    if apps_config is not None:
        return apps_config
    
    # If direct access fails, try using git clone (works for private repos with credentials)
    print_info("Direct access failed, attempting to use git credentials...")
    return try_git_clone_fetch(github_url, project_name)


def fetch_json_file_https(github_url, file_url, file_name):
    """Helper function to fetch a JSON file via HTTPS."""
    try:
        print_info(f"Fetching {file_name} from: {file_url}")
        
        request = urllib.request.Request(file_url)
        
        # Check for GitHub token in environment
        github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if github_token:
            request.add_header('Authorization', f'token {github_token}')
        
        # Fetch the file content
        with urllib.request.urlopen(request) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print_warning(f"{file_name} not found (this is optional)")
        elif e.code == 403:
            print_warning(f"Access forbidden for {file_name}")
        else:
            print_warning(f"HTTP error {e.code} for {file_name}: {e.reason}")
        return None
    except Exception as e:
        print_warning(f"Error fetching {file_name}: {e}")
        return None


def try_direct_https_fetch(github_url, project_name):
    """Try to fetch apps.json directly via HTTPS (works for public repos)."""
    try:
        # Clean up the GitHub URL and construct raw content URL
        if github_url.endswith('.git'):
            github_url = github_url[:-4]
        if github_url.endswith('/'):
            github_url = github_url[:-1]
        
        # Convert GitHub URL to raw content URL
        if 'github.com' in github_url:
            # Convert https://github.com/user/repo to https://raw.githubusercontent.com/user/repo/main
            github_url = github_url.replace('github.com', 'raw.githubusercontent.com')
            if not github_url.endswith('/main') and not github_url.endswith('/master'):
                github_url += '/main'
        
        # Fetch base_apps.json first (optional)
        base_apps_json_url = f"{github_url}/projects/{project_name}/base_apps.json"
        base_apps_list = fetch_json_file_https(github_url, base_apps_json_url, "base_apps.json")
        
        # Fetch apps.json (required)
        apps_json_url = f"{github_url}/projects/{project_name}/apps.json"
        apps_list = fetch_json_file_https(github_url, apps_json_url, "apps.json")
        
        if apps_list is None:
            print_error("Failed to fetch apps.json")
            return None
        
        # Combine lists: base_apps first, then apps
        combined_list = []
        if base_apps_list:
            combined_list.extend(base_apps_list)
            print_success(f"Loaded {len(base_apps_list)} app(s) from base_apps.json")
        combined_list.extend(apps_list)
        print_success(f"Loaded {len(apps_list)} app(s) from apps.json")
        
        # Check for GitHub token in environment
        github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if github_token:
            print_info("Using GitHub token for authentication")
            
        # Convert array format to object format for compatibility
        # Note: If same app appears in both files, apps.json will override base_apps.json
        apps_config = {}
        for app in combined_list:
            app_name = app.get('name')
            if app_name:
                apps_config[app_name] = {
                    'url': app.get('url'),
                    'is_repo': True,
                    'resolution': {
                        'branch': app.get('branch', 'main')
                    }
                }
        
        return apps_config
        
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print_warning("File not found via direct access (might be a private repository)")
        elif e.code == 403:
            print_warning("Access forbidden (private repository or rate limit)")
        else:
            print_warning(f"HTTP error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print_warning(f"Network error: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Error parsing apps.json: {e}")
        return None
    except Exception as e:
        print_warning(f"Unexpected error: {e}")
        return None


def try_git_clone_fetch(github_url, project_name):
    """Try to fetch apps.json using git clone (works for private repos with credentials)."""
    temp_dir = None
    try:
        # Clean up the GitHub URL
        if github_url.endswith('.git'):
            clone_url = github_url
        else:
            clone_url = f"{github_url}.git"
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix='ws-frappe-cli-')
        print_info("Cloning repository to temporary directory...")
        
        # Try to do a sparse checkout for better performance
        # Only fetch the specific file we need
        git_cmd = [
            'git', 'clone',
            '--depth', '1',
            '--filter=blob:none',
            '--sparse',
            clone_url,
            temp_dir
        ]
        
        result = subprocess.run(
            git_cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            print_error("Failed to clone repository")
            if 'Authentication failed' in result.stderr or 'fatal: could not read' in result.stderr:
                print_error("Authentication failed. Please ensure:")
                print("  • You have access to the repository")
                print("  • Your git credentials are configured (git config credential.helper)")
                print("  • Or set GITHUB_TOKEN environment variable")
            else:
                print_error(f"Git error: {result.stderr}")
            return None
        
        # Configure sparse checkout
        sparse_checkout_cmd = [
            'git', '-C', temp_dir,
            'sparse-checkout', 'set',
            f'projects/{project_name}'
        ]
        
        result = subprocess.run(sparse_checkout_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print_error(f"Failed to configure sparse checkout: {result.stderr}")
            return None
        
        # Now checkout the files
        checkout_cmd = ['git', '-C', temp_dir, 'checkout']
        result = subprocess.run(checkout_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print_error(f"Failed to checkout files: {result.stderr}")
            return None
        
        # Read the base_apps.json file (optional)
        base_apps_json_path = Path(temp_dir) / 'projects' / project_name / 'base_apps.json'
        base_apps_list = None
        
        if base_apps_json_path.exists():
            try:
                with open(base_apps_json_path, 'r') as f:
                    base_apps_list = json.load(f)
                print_success(f"Loaded {len(base_apps_list)} app(s) from base_apps.json")
            except json.JSONDecodeError as e:
                print_warning(f"Error parsing base_apps.json: {e}")
        else:
            print_info("base_apps.json not found (this is optional)")
        
        # Read the apps.json file (required)
        apps_json_path = Path(temp_dir) / 'projects' / project_name / 'apps.json'
        
        if not apps_json_path.exists():
            print_error(f"Apps configuration not found: projects/{project_name}/apps.json")
            print_info(f"Make sure the project '{project_name}' exists in the repository")
            return None
        
        with open(apps_json_path, 'r') as f:
            apps_list = json.load(f)
        
        print_success(f"Loaded {len(apps_list)} app(s) from apps.json")
        print_success("Successfully fetched apps configuration from repository")
        
        # Combine lists: base_apps first, then apps
        combined_list = []
        if base_apps_list:
            combined_list.extend(base_apps_list)
        combined_list.extend(apps_list)
        
        # Convert array format to object format for compatibility
        # Note: If same app appears in both files, apps.json will override base_apps.json
        apps_config = {}
        for app in combined_list:
            app_name = app.get('name')
            if app_name:
                apps_config[app_name] = {
                    'url': app.get('url'),
                    'is_repo': True,
                    'resolution': {
                        'branch': app.get('branch', 'main')
                    }
                }
        
        return apps_config
        
    except subprocess.TimeoutExpired:
        print_error("Git clone operation timed out")
        return None
    except FileNotFoundError:
        print_error("'git' command not found. Please install git.")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Error parsing apps.json: {e}")
        return None
    except Exception as e:
        print_error(f"Unexpected error during git clone: {e}")
        return None
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print_warning(f"Failed to clean up temporary directory: {e}")


def build_get_app_command(app_name, app_config):
    """Build the bench get-app command for a specific app."""
    cmd = ["bench", "get-app"]
    
    # All apps from GitHub are repository-based
    url = app_config.get("url")
    resolution = app_config.get("resolution", {})
    branch = resolution.get("branch")
    
    # Add branch if specified
    if branch:
        cmd.extend(["--branch", branch])
    
    # Add the repository URL
    if url:
        cmd.append(url)
    else:
        # Fallback to app name if no URL provided
        cmd.append(app_name)
    
    return cmd


def run_get_app_command(cmd, app_name):
    """Execute the get-app command for an app."""
    print_info(f"Installing {app_name}...")
    print(f"  Command: {Colors.YELLOW}{' '.join(cmd)}{Colors.NC}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print_success(f"Successfully installed {app_name}")
        if result.stdout and result.stdout.strip():
            # Only show output if it's not empty
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    print(f"    {line}")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install {app_name}")
        if e.stderr:
            print(f"    {Colors.RED}{e.stderr.strip()}{Colors.NC}")
        return False
    except FileNotFoundError:
        print_error("'bench' command not found. Make sure Frappe Bench is installed and in PATH.")
        return False


def find_apps_json(search_path=None):
    """Find apps.json file in current directory or specified path."""
    if search_path:
        apps_json_path = Path(search_path) / "sites" / "apps.json"
    else:
        apps_json_path = Path.cwd() / "sites" / "apps.json"
    
    # Also check for apps.json in the root directory
    if not apps_json_path.exists():
        root_apps_json = apps_json_path.parent.parent / "apps.json"
        if root_apps_json.exists():
            return root_apps_json
    
    return apps_json_path


@click.command()
@click.argument('github_url')
@click.argument('project_name')
@click.option('--dry-run',
              is_flag=True,
              help='Show what would be installed without actually installing')
@click.option('--force',
              is_flag=True,
              help='Skip confirmation prompt')
@click.option('--app',
              'specific_app',
              help='Install only a specific app from the apps.json')
@click.option('--exclude',
              multiple=True,
              help='Exclude specific apps from installation (can be used multiple times)')
def get_apps(github_url, project_name, dry_run, force, specific_app, exclude):
    """Install apps from GitHub repository apps.json configuration file.
    
    This command fetches the apps.json file from a GitHub repository at
    projects/{PROJECT_NAME}/apps.json and installs all configured apps
    using 'bench get-app'. The frappe app is automatically excluded from installation.
    
    Authentication for Private Repositories:
        The command supports both public and private repositories:
        - Public repos: Works automatically
        - Private repos: Use one of these methods:
          1. Set GITHUB_TOKEN or GH_TOKEN environment variable
          2. Configure git credentials (git config credential.helper)
          3. Use SSH URL (git@github.com:user/repo.git)
    
    Arguments:
        GITHUB_URL: GitHub repository URL (HTTPS or SSH)
                   Examples: https://github.com/user/repo
                            git@github.com:user/repo.git
        PROJECT_NAME: Project name within the repository's projects directory
    
    Examples:
        # Public repository
        ws get-apps https://github.com/user/repo whitestork
        
        # Private repository with token
        export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
        ws get-apps https://github.com/user/private-repo dbouk
        
        # Private repository with SSH
        ws get-apps git@github.com:user/private-repo.git medis
        
        # With options
        ws get-apps https://github.com/user/repo nvox --dry-run
        ws get-apps https://github.com/user/repo whitestork --app erpnext
        ws get-apps https://github.com/user/repo dbouk --exclude hrms --force
    """
    print()
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print(f"{Colors.GREEN}  Frappe Apps Installer{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print()
    
    # Validate bench directory
    current_dir = Path.cwd()
    if not validate_bench_directory(current_dir):
        print_error("This command must be run from a bench directory!")
        print_info("Please navigate to a bench directory or run 'ws setup' first.")
        sys.exit(1)
    
    # Fetch apps configuration from GitHub
    print_info(f"Fetching apps for project '{project_name}' from GitHub repository: {github_url}")
    apps_config = fetch_apps_from_github(github_url, project_name)
    
    if apps_config is None:
        sys.exit(1)
    
    # Filter apps based on options
    apps_to_install = {}
    
    for name, config in apps_config.items():
        # Skip frappe app
        if name.lower() == "frappe":
            continue
            
        # If specific app is requested, only include that one
        if specific_app and name.lower() != specific_app.lower():
            continue
            
        # Skip excluded apps
        if name.lower() in [exc.lower() for exc in exclude]:
            continue
            
        apps_to_install[name] = config
    
    if not apps_to_install:
        if specific_app:
            print_warning(f"App '{specific_app}' not found in project '{project_name}'")
        else:
            print_warning("No apps to install (only frappe found, which is excluded)")
        return
    
    print()
    print_success(f"Found {len(apps_to_install)} app(s) to install:")
    for app_name, app_config in apps_to_install.items():
        resolution = app_config.get("resolution", {})
        branch = resolution.get("branch", "main")
        url = app_config.get("url", f"https://github.com/frappe/{app_name}.git")
        print(f"  • {Colors.YELLOW}{app_name}{Colors.NC} (from {url}@{branch})")
    
    if excluded_count := len(exclude):
        print()
        print_info(f"Excluded {excluded_count} app(s): {', '.join(exclude)}")
    
    if dry_run:
        print()
        print_info("Dry run mode - showing commands that would be executed:")
        print()
        for app_name, app_config in apps_to_install.items():
            cmd = build_get_app_command(app_name, app_config)
            print(f"  {Colors.YELLOW}{' '.join(cmd)}{Colors.NC}")
        print()
        print_info("Use without --dry-run to actually install the apps")
        return
    
    # Confirm before proceeding (unless --force is used)
    if not force:
        print()
        if not prompt_yes_no("Do you want to proceed with installation?", default="n"):
            print_warning("Installation cancelled")
            return
    
    # Install each app
    print()
    successful_installs = []
    failed_installs = []
    
    for app_name, app_config in apps_to_install.items():
        cmd = build_get_app_command(app_name, app_config)
        
        if run_get_app_command(cmd, app_name):
            successful_installs.append(app_name)
        else:
            failed_installs.append(app_name)
        print()
    
    # Summary
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print(f"{Colors.GREEN}  Installation Summary{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print()
    
    if successful_installs:
        print_success(f"Successfully installed ({len(successful_installs)}):")
        for app in successful_installs:
            print(f"  • {app}")
        print()
    
    if failed_installs:
        print_error(f"Failed to install ({len(failed_installs)}):")
        for app in failed_installs:
            print(f"  • {app}")
        print()
        print_warning("Troubleshooting tips:")
        print("  • Check if the repository URLs are correct")
        print("  • Verify your network connection")
        print("  • Ensure you have proper permissions")
        print("  • Check if the branch/commit exists")
        print("  • Try installing failed apps manually")
        print()
    
    if successful_installs and not failed_installs:
        print_success("All apps installed successfully!")
    elif successful_installs and failed_installs:
        print_warning("Installation completed with some failures")
    else:
        print_error("No apps were installed successfully")
    
    print()


if __name__ == "__main__":
    get_apps()