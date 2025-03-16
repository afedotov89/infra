# Infra

A comprehensive infrastructure automation toolkit for rapid deployment of standardized projects.

## Overview

This project provides a set of tools and scripts for automating the infrastructure setup of new projects, primarily focusing on a Django + PostgreSQL + React stack. It streamlines the process of creating repositories, configuring CI/CD, setting up cloud resources, and generating project boilerplates.

## Features

- **GitHub Integration**: Create repositories and configure CI/CD variables
- **Cloud Resource Management**: 
  - Database provisioning and configuration
  - Container deployment and management
  - Storage bucket creation and configuration
- **Project Templating**: Generate ready-to-use project boilerplates
- **Extensible Architecture**: Supports multiple cloud providers (with focus on Yandex Cloud)
- **AI-Assisted Automation**: (Planned) Intelligent agents for advanced automation
- **Multiple Interfaces**: CLI and GUI (macOS) support

## Requirements

- Python 3.10+
- Git
- Poetry (package manager)
- Access to GitHub API
- Access to cloud provider accounts (Yandex Cloud, etc.)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/infra.git
   cd infra
   ```

2. Install the package with Poetry:
   ```bash
   # Install Poetry if you don't have it
   # curl -sSL https://install.python-poetry.org | python3 -
   
   # Install dependencies and create virtual environment
   poetry install
   
   # Activate the virtual environment
   poetry shell
   
   # Or run commands directly
   poetry run infra --help
   ```

3. Install optional dependency groups as needed:
   ```bash
   # For GUI support
   poetry install --with gui
   
   # For AI agents
   poetry install --with ai
   
   # For development
   poetry install --with dev
   ```

4. Set up environment variables by copying `.env.example` to `.env` and filling in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Usage

### Command Line Interface

The CLI is organized into logical command groups:

```bash
# List available technologies
infra list templates

# Complete project setup with multiple technologies (space-separated)
infra setup project --name myproject --stack "django react postgres"

# Repository creation (two equivalent ways)
infra create repo --name myproject --private
infra git repo create --project-name myproject --private

# Other individual resource creation
infra create db --name mydb --type postgres
infra create container --name mycontainer --image python:3.10
infra create bucket --name mybucket

# Launch the GUI interface
infra gui
```

### Graphical User Interface (macOS)

The project includes a native macOS GUI application that provides a user-friendly interface to all CLI functionality:

```bash
# Install GUI dependencies
poetry install --with gui

# Launch the GUI directly
poetry run infra gui
```

Alternatively, you can build a standalone macOS application:

```bash
# Build the application bundle
./build_macos_app.sh

# Launch the application
open dist/Infra.app
```

The GUI provides:
- Project creation wizard with stack selection
- Infrastructure resource management
- Environment configuration
- Light/dark theme support
- Visual progress logging

For detailed documentation on the GUI, see [infra/gui/README.md](infra/gui/README.md).

### Configuration

The project uses a central `.env` file for all credentials and configuration options. See `.env.example` for available settings.

## Project Structure

```
infra/
├── pyproject.toml      # Project configuration + Poetry settings
├── README.md           # Documentation
├── .gitignore          # Standard gitignore
├── .env.example        # Environment variables template
├── .env                # Actual credentials (not in Git)
├── setup.py            # py2app setup for macOS app building
├── build_macos_app.sh  # Script to build macOS app
├── infra/              # Main module
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration handling
│   ├── providers/      # Service providers
│   │   ├── __init__.py
│   │   ├── git/        # GitHub/GitLab operations
│   │   └── cloud/      # Cloud providers
│   │       ├── __init__.py
│   │       ├── yandex/ # Yandex Cloud specific
│   │       │   ├── __init__.py
│   │       │   ├── db/       # Cloud databases
│   │       │   ├── storage/  # Object storage
│   │       │   └── compute/  # Containers/VMs
│   │       └── aws/    # Other cloud providers
│   ├── agents/         # AI agents for automation
│   │   ├── __init__.py
│   │   ├── base.py     # Base agent class
│   │   └── ...
│   ├── templates/      # Project boilerplate templates
│   │   ├── django/
│   │   ├── react/
│   │   └── ...
│   ├── gui/            # Graphical interfaces
│   │   ├── README.md   # GUI documentation
│   │   ├── __init__.py # GUI module initialization
│   │   ├── app.py      # Main application entry point
│   │   ├── main_window.py # Main window implementation
│   │   ├── resources/  # Icons and resources
│   │   ├── logging/    # Log display components
│   │   ├── settings/   # Settings management
│   │   ├── project/    # Project setup UI
│   │   ├── create/     # Resource creation UI
│   │   ├── templates/  # Template browser
│   │   └── operations/ # Operation execution
│   └── utils/          # Helper functions
│       ├── __init__.py
│       └── ...
└── tests/              # Tests
    ├── __init__.py
    └── ...
```

## Extending

The modular architecture makes it easy to add new functionality:

1. **New Cloud Providers**: Add a new module under `infra/providers/cloud/`
2. **New Project Templates**: Add templates to `infra/templates/`
3. **New AI Agents**: Implement new agents in `infra/agents/`
4. **New CLI Commands**: Extend existing command groups or add new ones in `infra/cli.py`

## License

MIT License