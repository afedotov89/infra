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
   # After activating the environment, you can run commands directly
   infra --help

   # Or run commands without activating the environment
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
# List available templates
infra list templates

# Complete project setup with selected template
infra setup project --name myproject --template webapp --private --db-type postgres

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

# For debugging purposes
./run_gui_debug.sh
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
├── run_gui_debug.sh    # Script to run GUI in debug mode
├── logs/               # Application logs directory
├── infra/              # Main module
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration handling
│   │   ├── project_setup/  # Project setup functionality
│   │   │   ├── __init__.py
│   │   │   └── core.py     # Core project setup logic
│   │   │   └── environment.py # Environment setup functions (DB, venv, etc.)
│   │   └── providers/      # Service providers
│   │       ├── __init__.py
│   │       ├── git/        # GitHub/GitLab operations
│   │       └── cloud/      # Cloud providers
│   │           ├── __init__.py
│   │           ├── yandex/ # Yandex Cloud specific
│   │           │   ├── __init__.py
│   │           │   ├── db/       # Cloud databases
│   │           │   ├── storage/  # Object storage
│   │           │   └── compute/  # Containers/VMs
│   │           └── aws/    # Other cloud providers
│   ├── agents/         # AI agents for automation (planned)
│   │   └── __init__.py
│   ├── templates/      # Project boilerplate templates
│   │   ├── __init__.py
│   │   ├── generator.py # Template generation logic
│   │   ├── zero/        # Zero configuration template
│   │   ├── webapp/      # Web application template
│   │   │   └── template_setup.py # Example template-specific setup script
│   │   └── chatbot/     # Chatbot application template
│   ├── gui/            # Graphical interfaces
│   │   ├── README.md   # GUI documentation
│   │   ├── __init__.py # GUI module initialization
│   │   ├── app.py      # Main application entry point
│   │   ├── main_window.py # Main window implementation
│   │   ├── resources/  # Icons and resources
│   │   ├── widgets/    # Reusable GUI widgets
│   │   ├── logging/    # Log display components
│   │   ├── settings/   # Settings management
│   │   ├── project/    # Project setup UI
│   │   ├── create/     # Resource creation UI
│   │   ├── templates/  # Template browser
│   │   ├── operations/ # Operation execution
│   │   └── macos/      # macOS-specific components
│   └── utils/          # Helper functions
│       └── __init__.py
└── tests/              # Tests
    └── __init__.py
```

## Extending

The modular architecture makes it easy to add new functionality:

1. **New Cloud Providers**: Add a new module under `infra/providers/cloud/`
2. **New Project Templates**:
   - Add template files to `infra/templates/` directory
   - Available templates currently include:
     - `zero`: Minimal project scaffolding (no specific setup)
     - `webapp`: Web application template
     - `chatbot`: Chatbot application template
   - Register the template in `infra/templates/__init__.py`
   - **Optional**: Create a `template_setup.py` file in the template's root directory.
     - This script should contain a `setup(ctx: ProjectSetupContext) -> str` function.
     - This function will be called by the core setup process after template files are copied.
     - Use this script to perform template-specific environment setup, like initializing a Python venv, creating databases (using functions from `infra.project_setup.environment`), or running initial setup commands.
     - The function should return the final database name used (if applicable).
3. **New AI Agents**: Implement new agents in `infra/agents/`
4. **New CLI Commands**: Extend existing command groups or add new ones in `infra/cli.py`

## License

MIT License