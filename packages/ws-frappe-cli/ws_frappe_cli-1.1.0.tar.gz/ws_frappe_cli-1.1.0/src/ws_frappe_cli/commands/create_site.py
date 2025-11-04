"""Create site command for Frappe/ERPNext sites."""

import click
import sys
from pathlib import Path

from ..utils import (
    Colors, print_info, print_success, print_warning, print_error,
    run_command, validate_bench_directory, prompt_input, prompt_yes_no
)


def get_available_apps(apps_dir):
    """Get list of available apps (excluding frappe)."""
    available_apps = []
    
    if apps_dir.exists():
        for app_path in apps_dir.iterdir():
            if app_path.is_dir():
                app_name = app_path.name
                # Exclude frappe as it's always installed first
                if app_name != "frappe":
                    available_apps.append(app_name)
    
    # Sort alphabetically
    return sorted(available_apps)


def select_apps_interactive(apps_dir):
    """Interactive app selection with ordering."""
    available_apps = get_available_apps(apps_dir)
    
    if not available_apps:
        print_warning("No additional apps found in apps directory.")
        return ["frappe"]
    
    print()
    print_info("Available apps for installation:")
    for i, app in enumerate(available_apps, 1):
        print(f"  {i}. {app}")
    print()
    
    # Simple selection - just ask which apps to install
    selected_apps = []
    for app in available_apps:
        if click.confirm(f"Install {app}?", default=False):
            selected_apps.append(app)
    
    # Build the final apps list
    apps_to_install = ["frappe"] + selected_apps
    
    if selected_apps:
        print_success(f"Selected apps: {' '.join(selected_apps)}")
    else:
        print_info("No additional apps selected. Only frappe will be available.")
    
    return apps_to_install


@click.command()
@click.option('--site-name', 
              prompt='Site name (e.g., mysite.localhost)',
              help='Name of the site to create')
@click.option('--admin-password',
              prompt='Administrator password',
              hide_input=True,
              confirmation_prompt=True,
              help='Administrator password for the site')
@click.option('--db-name',
              help='Database name (default: derived from site name)')
@click.option('--db-port',
              default='3306',
              help='Database port (default: 3306)')
@click.option('--db-root-username',
              default='root',
              help='Database root username (default: root)')
@click.option('--db-root-password',
              prompt='Database root password',
              hide_input=True,
              default='',
              help='Database root password')
@click.option('--set-default',
              is_flag=True,
              help='Set this site as the default site')
@click.option('--install-apps',
              is_flag=True,
              help='Install apps after site creation')
@click.option('--apps',
              multiple=True,
              help='Specific apps to install (can be used multiple times)')
@click.option('--no-interactive',
              is_flag=True,
              help='Skip interactive prompts')
def create_site(site_name, admin_password, db_name, db_port, db_root_username, 
                db_root_password, set_default, install_apps, apps, no_interactive):
    """Create a new Frappe/ERPNext site.
    
    This command creates a new site with the specified configuration,
    optionally installs apps, and can set it as the default site.
    """
    # Validate that we're in a bench directory
    if not validate_bench_directory():
        print_error("This command must be run from a bench directory!")
        print_info("Please run 'ws setup' first or navigate to a bench directory.")
        sys.exit(1)
    
    script_dir = Path.cwd()
    
    # Clear screen and show header
    print()
    print("═" * 63)
    print("          Frappe/ERPNext Site Creation           ")
    print("═" * 63)
    print()
    
    print_success(f"Running from bench directory: {script_dir}")
    print()
    
    # Check if site already exists
    if (script_dir / "sites" / site_name).exists():
        print_error(f"Site '{site_name}' already exists!")
        sys.exit(1)
    
    # Set default database name if not provided
    if not db_name:
        db_name = site_name.replace(".", "_") + "_db"
    
    # Interactive app selection if not specified and not in non-interactive mode
    apps_to_install = ["frappe"]
    if install_apps and not apps and not no_interactive:
        apps_to_install = select_apps_interactive(script_dir / "apps")
    elif install_apps and apps:
        apps_to_install = ["frappe"] + list(apps)
    
    # ═══════════════════════════════════════════════════════════
    # CONFIGURATION SUMMARY
    # ═══════════════════════════════════════════════════════════
    print()
    print("━" * 63)
    print("  CONFIGURATION SUMMARY")
    print("━" * 63)
    print()
    print(f"Site Name:           {site_name}")
    print(f"Database Name:       {db_name}")
    print(f"Database Port:       {db_port}")
    print(f"Root Username:       {db_root_username}")
    print(f"Set as Default:      {'yes' if set_default else 'no'}")
    print(f"Install Apps:        {'yes' if install_apps else 'no'}")
    if install_apps:
        print(f"Apps to Install:     {' '.join(apps_to_install)}")
    print()
    
    # Confirm before proceeding (unless in non-interactive mode)
    if not no_interactive:
        if not click.confirm("Proceed with site creation?", default=True):
            print_warning("Site creation cancelled.")
            return
    
    # ═══════════════════════════════════════════════════════════
    # BUILD BENCH COMMAND
    # ═══════════════════════════════════════════════════════════
    cmd_parts = ["bench", "new-site", site_name]
    cmd_parts.extend(["--admin-password", admin_password])
    cmd_parts.extend(["--db-name", db_name])
    
    if db_port and db_port != "3306":
        cmd_parts.extend(["--db-port", db_port])
    
    if db_root_username:
        cmd_parts.extend(["--db-root-username", db_root_username])
    
    if db_root_password:
        cmd_parts.extend(["--db-root-password", db_root_password])
    
    # ═══════════════════════════════════════════════════════════
    # EXECUTE SITE CREATION
    # ═══════════════════════════════════════════════════════════
    print()
    print("━" * 63)
    print("  CREATING SITE")
    print("━" * 63)
    print()
    
    # For display purposes, mask the password
    display_cmd = " ".join(cmd_parts).replace(admin_password, "********")
    if db_root_password:
        display_cmd = display_cmd.replace(db_root_password, "********")
    
    print_info(f"Executing: {display_cmd}")
    print()
    
    # Execute the command
    try:
        import subprocess
        subprocess.run(cmd_parts, check=True)
        print_success(f"Site '{site_name}' created successfully!")
    except subprocess.CalledProcessError:
        print_error("Failed to create site!")
        sys.exit(1)
    
    # ═══════════════════════════════════════════════════════════
    # SET AS DEFAULT SITE
    # ═══════════════════════════════════════════════════════════
    if set_default:
        print()
        print_info(f"Setting {site_name} as default site...")
        if run_command(f'bench use "{site_name}"'):
            print_success(f"Default site set to {site_name}")
        else:
            print_error("Failed to set default site")
    
    # ═══════════════════════════════════════════════════════════
    # INSTALL APPS
    # ═══════════════════════════════════════════════════════════
    if install_apps and apps_to_install:
        print()
        print("━" * 63)
        print("  INSTALLING APPS")
        print("━" * 63)
        print()
        
        for app in apps_to_install:
            if app != "frappe":  # Skip frappe as it's already installed
                print_info(f"Installing {app}...")
                if run_command(f'bench --site "{site_name}" install-app "{app}"'):
                    print_success(f"{app} installed successfully")
                else:
                    print_error(f"Failed to install {app}")
    
    # ═══════════════════════════════════════════════════════════
    # FINAL MESSAGE
    # ═══════════════════════════════════════════════════════════
    print()
    print("═" * 63)
    print("                    SITE CREATION COMPLETE                     ")
    print("═" * 63)
    print()
    print_success("Your site is ready!")
    print()
    print_info(f"Access your site at: http://{site_name}")
    print_info("Login with:")
    print("  Username: Administrator")
    print("  Password: ********")
    print()
    print_info("To start the server, run:")
    print("  bench start")
    print()


if __name__ == "__main__":
    create_site()