"""Main CLI entry point for ws-frappe-cli."""

import click
from .commands.setup import setup
from .commands.create_site import create_site
from .commands.fetch_app import fetch_app
from .commands.shortcuts import shortcuts
from .commands.get_apps import get_apps
from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="ws")
@click.pass_context
def main(ctx):
    """WS Frappe CLI - A command-line tool for Frappe/ERPNext development environment management.
    
    This tool helps you set up, configure, and manage Frappe/ERPNext development environments
    with ease. It provides commands for environment setup, site creation, and app management.
    
    Examples:
        ws setup myproject       # Set up development environment
        ws create-site              # Create a new site interactively
        ws fetch-app --list-predefined  # List available apps
        ws fetch-app --app-name erpnext # Install ERPNext
        ws shortcuts --list         # List available shortcuts
        ws shortcuts                # Create bench shortcuts
        ws get-apps https://github.com/user/repo whitestork # Install apps from GitHub
        ws get-apps https://github.com/user/repo medis --dry-run # Preview app installation
    """
    # Ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if __name__ == "__main__"` block below)
    ctx.ensure_object(dict)


# Add commands to the main group
main.add_command(setup)
main.add_command(create_site)
main.add_command(fetch_app)
main.add_command(shortcuts)
main.add_command(get_apps)


# Create an alias for the main function to be used as entry point
cli = main


if __name__ == "__main__":
    main()