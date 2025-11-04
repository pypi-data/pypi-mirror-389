"""Fetch app command for installing Frappe apps."""

import click
import sys
import shutil
from pathlib import Path

from ..utils import (
    Colors, print_info, print_success, print_warning, print_error,
    run_command, validate_bench_directory
)


# Predefined apps configuration
PREDEFINED_APPS = [
    {
        "name": "hrms",
        "url": "https://github.com/frappe/hrms",
        "branch": "version-15",
        "description": "Human Resource Management System"
    },
    {
        "name": "erpnext",
        "url": "",  # Empty means use default Frappe repository
        "branch": "v15.78.1",
        "description": "Enterprise Resource Planning"
    },
    {
        "name": "payments",
        "url": "https://github.com/frappe/payments",
        "branch": "version-15",
        "description": "Payment Gateway Integration"
    },
    {
        "name": "ecommerce_integrations",
        "url": "https://github.com/frappe/ecommerce_integrations",
        "branch": "main",
        "description": "E-commerce Platform Integrations"
    }
]


def list_sites(script_dir):
    """List available sites."""
    sites_dir = Path(script_dir) / "sites"
    if not sites_dir.exists():
        return []
    
    sites = []
    for item in sites_dir.iterdir():
        if (item.is_dir() and 
            item.name not in ["assets", "common_site_config.json"] and
            not item.name.startswith(".")):
            sites.append(item.name)
    
    return sorted(sites)


def install_app_on_site(app_name, script_dir, site_name=None):
    """Install app on a specific site or ask user to choose."""
    sites = list_sites(script_dir)
    
    if not sites:
        print_warning("No sites found. Please create a site first using 'ws create-site'.")
        return False
    
    # If site name is provided, use it
    if site_name:
        if site_name not in sites:
            print_error(f"Site '{site_name}' not found.")
            return False
        selected_site = site_name
    else:
        # Interactive site selection
        if len(sites) == 1:
            selected_site = sites[0]
            print_info(f"Installing on site: {selected_site}")
        else:
            print_info("Available sites:")
            for i, site in enumerate(sites, 1):
                print(f"  {i}. {site}")
            
            choice = click.prompt("Select site number", type=int)
            
            if 1 <= choice <= len(sites):
                selected_site = sites[choice - 1]
            else:
                print_error("Invalid site selection.")
                return False
    
    # Install the app
    print_info(f"Installing {app_name} on {selected_site}...")
    
    if run_command(f'bench --site "{selected_site}" install-app "{app_name}"'):
        print_success(f"{app_name} installed successfully on {selected_site}!")
        return True
    else:
        print_error(f"Failed to install {app_name} on {selected_site}")
        return False


@click.command()
@click.option('--app-name',
              help='Name of the app to install')
@click.option('--github-url',
              help='GitHub URL of the app')
@click.option('--branch',
              default='develop',
              help='Branch to install (default: develop)')
@click.option('--site',
              help='Site to install the app on')
@click.option('--list-predefined',
              is_flag=True,
              help='List predefined apps available for installation')
@click.option('--no-install',
              is_flag=True,
              help='Only fetch the app, do not install on any site')
@click.option('--force',
              is_flag=True,
              help='Reinstall if app already exists')
def fetch_app(app_name, github_url, branch, site, list_predefined, no_install, force):
    """Fetch and optionally install Frappe apps.
    
    This command can install predefined apps or custom apps from GitHub.
    Use --list-predefined to see available predefined apps.
    """
    # Validate that we're in a bench directory
    if not validate_bench_directory():
        print_error("This command must be run from a bench directory!")
        print_info("Please run 'ws setup' first or navigate to a bench directory.")
        sys.exit(1)
    
    script_dir = Path.cwd()
    
    # List predefined apps if requested
    if list_predefined:
        print()
        print("━" * 60)
        print("  PREDEFINED APPS")
        print("━" * 60)
        print()
        
        for i, app in enumerate(PREDEFINED_APPS, 1):
            print(f"{i}. {Colors.GREEN}{app['name']}{Colors.NC}")
            print(f"   Description: {app['description']}")
            print(f"   Branch: {app['branch']}")
            if app['url']:
                print(f"   URL: {app['url']}")
            else:
                print(f"   URL: Default Frappe repository")
            print()
        
        print_info("To install a predefined app, use:")
        print(f"  {Colors.YELLOW}ws fetch-app --app-name <app_name>{Colors.NC}")
        print()
        return
    
    # Interactive mode if no app name provided
    if not app_name:
        print()
        print("━" * 60)
        print("  FRAPPE APP INSTALLER")
        print("━" * 60)
        print()
        
        # Show predefined apps
        print("Predefined apps:")
        for i, app in enumerate(PREDEFINED_APPS, 1):
            print(f"  {i}. {app['name']} - {app['description']}")
        
        print(f"  {len(PREDEFINED_APPS) + 1}. Custom app (from GitHub URL)")
        print()
        
        choice = click.prompt("Select an option", type=int)
        
        if 1 <= choice <= len(PREDEFINED_APPS):
            # Install predefined app
            selected_app = PREDEFINED_APPS[choice - 1]
            app_name = selected_app['name']
            github_url = selected_app['url']
            branch = selected_app['branch']
        elif choice == len(PREDEFINED_APPS) + 1:
            # Custom app
            app_name = click.prompt("Enter app name")
            github_url = click.prompt("Enter GitHub URL")
            branch = click.prompt("Enter branch", default="develop")
        else:
            print_error("Invalid selection.")
            return
    
    # If app_name is provided but it's a predefined app, get its details
    elif not github_url:
        predefined_app = next((app for app in PREDEFINED_APPS if app['name'] == app_name), None)
        if predefined_app:
            github_url = predefined_app['url']
            if not branch or branch == 'develop':
                branch = predefined_app['branch']
            print_info(f"Using predefined app configuration for {app_name}")
        elif not github_url:
            print_error("GitHub URL is required for custom apps.")
            print_info("Use --list-predefined to see available predefined apps.")
            return
    
    print()
    print("━" * 60)
    print("  FETCHING APP")
    print("━" * 60)
    print()
    
    print_info(f"App Name: {app_name}")
    if github_url:
        print_info(f"GitHub URL: {github_url}")
    else:
        print_info("GitHub URL: Default Frappe repository")
    print_info(f"Branch: {branch}")
    print()
    
    app_path = script_dir / "apps" / app_name
    
    # Check if app already exists
    if app_path.exists():
        if force:
            print_warning(f"App {app_name} already exists. Removing...")
            shutil.rmtree(app_path)
        else:
            print_warning(f"App {app_name} already exists in apps directory.")
            if not click.confirm("Do you want to reinstall?", default=False):
                print_info("Skipping installation...")
                return
            shutil.rmtree(app_path)
    
    # Build bench get-app command
    if github_url:
        cmd = f'bench get-app "{app_name}" "{github_url}" --branch "{branch}"'
    else:
        cmd = f'bench get-app "{app_name}" --branch "{branch}"'
    
    # Fetch the app
    print_info("Fetching app...")
    if not run_command(cmd, cwd=script_dir):
        print_error(f"Failed to fetch app {app_name}")
        return
    
    print_success(f"App {app_name} fetched successfully!")
    
    # Install on site if requested
    if not no_install:
        print()
        if site:
            # Install on specified site
            install_app_on_site(app_name, script_dir, site)
        else:
            # Ask user if they want to install
            if click.confirm("Do you want to install this app on a site now?", default=True):
                install_app_on_site(app_name, script_dir)
    
    print()
    print_success("Done!")


if __name__ == "__main__":
    fetch_app()