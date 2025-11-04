# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2024-10-26

### ⚠️ BREAKING CHANGES
- **Setup command now requires project name**: `--project-name` is now mandatory
- **Project directory creation**: Setup now creates a new directory with the project name instead of using current directory

### Changed
- Setup command behavior: creates new project directory instead of working in current directory
- Improved project isolation and organization
- Updated CLI help documentation and examples to reflect mandatory project name
- Enhanced user workflow with clearer directory structure

### Enhanced
- Better project structure management with dedicated project directories
- Improved setup instructions showing directory navigation
- More intuitive project initialization workflow

## [0.5.0] - 2024-10-26

### Added
- New `get-apps` command for batch app installation from apps.json
- Support for apps.json configuration file parsing
- Dry-run mode for previewing app installations
- Selective app installation with `--app` option
- App exclusion functionality with `--exclude` option
- Automatic frappe app exclusion from installation
- Custom apps.json file path support
- Force mode to skip confirmation prompts
- Comprehensive installation summary and error reporting
- Support for repository-based and package-based apps
- Branch and commit hash support for git repositories

### Enhanced
- Improved CLI help documentation with get-apps examples
- Better error handling and user feedback for app installations
- Cross-platform compatibility for app management workflows

## [Unreleased]

## [0.4.0] - 2024-01-XX

### Added
- New `shortcuts` command for managing bench command shortcuts
- System-wide shortcuts for common bench commands:
  - `bs` - bench start
  - `bm` - bench migrate  
  - `bcc` - bench clear-cache
  - `br` - bench restart
  - `bef` - bench export-fixtures
- Cross-platform support for shortcuts (Windows, Linux, macOS)
- Shortcuts can be created, listed, and removed independently
- Integration with `setup` command via `--create-shortcuts` option
- Automatic PATH validation and guidance for shortcut accessibility
- TECHNICAL_DOCS.md template for tracking app versions and customizations
- Git repository initialization option in setup command

### Enhanced
- Updated CLI help documentation with shortcut examples
- Improved cross-platform compatibility for script generation
- Enhanced setup command with `--install-docs`, `--init-git`, and `--create-shortcuts` options

## [0.3.0] - 2024-01-XX

### Added
- Template system for documentation installation
- Enhanced setup command with multiple options

## [0.2.0] - 2024-01-XX

### Added
- Complete CLI conversion from standalone scripts
- Environment setup command with virtual environment management
- Interactive site creation with validation
- App fetching with predefined app list
- Comprehensive error handling and colored output
- Cross-platform compatibility

### Changed
- Converted from standalone scripts to proper CLI package
- Restructured codebase with modern Python packaging standards

## [0.1.0] - 2024-01-XX

### Added
- Initial release
- Basic CLI functionality for Frappe/ERPNext development
- Environment setup automation
- Site creation with interactive configuration
- App installation from predefined list or custom GitHub repositories
- Cross-platform support (Linux, macOS, Windows)

### Features
- `setup` command for environment initialization
- `create-site` command for site creation
- `fetch-app` command for app management
- Rich CLI interface with colors and interactive prompts
- Support for Python 3.8+

[Unreleased]: https://github.com/HasanHajHasan/ws-frappe-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/HasanHajHasan/ws-frappe-cli/releases/tag/v0.1.0