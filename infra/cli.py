"""
Command Line Interface for the Infra toolkit.
"""

import sys
import logging
from typing import Optional, List, Dict, Any
from functools import wraps

import click

# Настройка логирования на уровне модуля
logging.basicConfig(
    level=logging.WARNING,  # По умолчанию WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from infra import __version__
from infra.config import Config, ConfigError
from infra.providers.git import create_repository
from infra.project_setup.core import setup_project as setup_project_operation, SetupError


# Available templates for projects
PROJECT_TEMPLATES = {
    "chatbot": {
        "description": "Chat bot application",
        "technologies": ["django", "postgres", "redis"],
        "details": "Django-based chat bot with Postgres database and Redis for message queuing"
    },
    "webapp": {
        "description": "Full-stack web application",
        "technologies": ["react", "django", "postgres"],
        "details": "React frontend with Django backend and Postgres database"
    },
    "zero": {
        "description": "Empty project template",
        "technologies": [],
        "details": "A blank project structure without any predefined technologies or dependencies"
    }
}

# All technologies used across templates
AVAILABLE_TECHNOLOGIES = sorted(list(set(
    tech for template in PROJECT_TEMPLATES.values()
    for tech in template["technologies"]
)))


def validate_template(ctx, param, value: str) -> Dict[str, Any]:
    """Validate template selection."""
    if not value:
        raise click.BadParameter("Template name is required")

    if value not in PROJECT_TEMPLATES:
        available_templates = ", ".join(PROJECT_TEMPLATES.keys())
        raise click.BadParameter(
            f"Invalid template: {value}\n"
            f"Available templates are: {available_templates}"
        )

    return PROJECT_TEMPLATES[value]


def common_options(func):
    """Decorator that adds common options to all commands."""
    @click.option("--debug", is_flag=True, help="Enable debug logging")
    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("debug"):
            # Изменение уровня логирования на DEBUG для корневого логгера
            logging.getLogger().setLevel(logging.DEBUG)
            click.echo("Debug logging enabled")
        return func(*args, **kwargs)
    return wrapper


@click.group()
@click.version_option(version=__version__)
@common_options
def cli(debug: bool):
    """Infra - Infrastructure automation toolkit for rapid project deployment."""
    pass


# Git operations group
@cli.group()
@common_options
def git(debug: bool):
    """Git operations (repositories, CI/CD)."""
    pass


# Git repository operations subgroup
@git.group()
@common_options
def repo(debug: bool):
    """Repository operations."""
    pass


@repo.command("create")
@click.option("--project-name", required=True, help="Repository/project name")
@click.option("--private/--public", default=True, help="Create a private repository")
@common_options
def git_repo_create(project_name: str, private: bool, debug: bool):
    """Create a GitHub repository."""
    click.echo(f"Creating {'private' if private else 'public'} repository: {project_name}")
    repository, already_existed = create_repository(project_name, private)

    if already_existed:
        click.echo(f"Repository already exists: {repository.html_url}")
    else:
        click.echo(f"Repository created: {repository.html_url}")


# Create group for resource creation commands
@cli.group()
@common_options
def create(debug: bool):
    """Create individual infrastructure resources (repo, db, container, bucket)."""
    pass


@create.command("repo")
@click.option("--name", required=True, help="Repository name")
@click.option("--private/--public", default=True, help="Create a private repository")
@common_options
def create_repo(name: str, private: bool, debug: bool):
    """Create a GitHub repository."""
    click.echo(f"Creating {'private' if private else 'public'} repository: {name}")
    repository, already_existed = create_repository(name, private)

    if already_existed:
        click.echo(f"Repository already exists: {repository.html_url}")
    else:
        click.echo(f"Repository created: {repository.html_url}")


@create.command("db")
@click.option("--name", required=True, help="Database name")
@click.option("--type", "db_type", default="postgres", help="Database type")
@common_options
def create_db(name: str, db_type: str, debug: bool):
    """Create a database in the cloud."""
    click.echo(f"Creating database: {name} of type: {db_type}")
    # from infra.providers.cloud.yandex.db import create_database
    # create_database(name, db_type)


@create.command("container")
@click.option("--name", required=True, help="Container name")
@click.option("--image", required=True, help="Docker image to use")
@common_options
def create_container(name: str, image: str, debug: bool):
    """Create a container in the cloud."""
    click.echo(f"Creating container: {name} with image: {image}")
    # from infra.providers.cloud.yandex.compute import create_container
    # create_container(name, image)


@create.command("bucket")
@click.option("--name", required=True, help="Bucket name")
@common_options
def create_bucket(name: str, debug: bool):
    """Create a storage bucket in the cloud."""
    click.echo(f"Creating bucket: {name}")
    # from infra.providers.cloud.yandex.storage import create_bucket
    # create_bucket(name)


# Setup group for complex setup operations
@cli.group()
@common_options
def setup(debug: bool):
    """Set up complete infrastructure components."""
    pass


@setup.command("project")
@click.option("--name", required=True, help="Project name")
@click.option(
    "--template",
    required=True,
    help="Project template to use (e.g. 'webapp', 'chatbot')",
    callback=validate_template
)
@click.option("--private/--public", default=True, help="Create a private repository")
@click.option("--db-type", default="postgres", help="Database type")
@click.option("--db-name", help="Database name (defaults to project name)")
@click.option("--yandex", is_flag=True, help="Enable Yandex Cloud operations")
@common_options
def setup_project(
    name: str,
    template: Dict[str, Any],
    private: bool,
    db_type: str,
    db_name: Optional[str] = None,
    yandex: bool = False,
    debug: bool = False
):
    """
    Set up a complete project infrastructure.

    This command will:
    1. Create GitHub repository
    2. Check local project directory
    3. Create or initialize local project with selected template
    4. Set up CI/CD variables
    5. Create database in the cloud (if --yandex flag is set)
    6. Set up container infrastructure (if --yandex flag is set)
    """
    technologies = template["technologies"]
    template_name = next(name for name, data in PROJECT_TEMPLATES.items() if data == template)

    click.echo(f"Setting up project '{name}' using template: {template_name}")
    click.echo(f"Template description: {template['description']}")
    click.echo(f"Technologies included: {', '.join(technologies)}")

    try:
        setup_project_operation(
            name=name,
            technologies=technologies,
            private=private,
            db_type=db_type,
            db_name=db_name,
            template_name=template_name,
            use_yandex_cloud=yandex,
            log_callback=click.echo
        )
    except SetupError as e:
        click.echo(f"❌ {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {str(e)}", err=True)
        sys.exit(1)


# List group for information listing commands
@cli.group()
@common_options
def list(debug: bool):
    """List available resources and configurations."""
    pass


@list.command("templates")
@common_options
def list_templates(debug: bool):
    """List available project templates."""
    click.echo("Available project templates:")
    for name, info in PROJECT_TEMPLATES.items():
        click.echo(f"\n• {name} - {info['description']}")
        click.echo(f"  Technologies: {', '.join(info['technologies'])}")
        click.echo(f"  Details: {info['details']}")


# Add GUI command
@cli.command("gui")
@common_options
def gui(debug: bool):
    """Launch the graphical user interface."""
    click.echo("Launching GUI...")
    from infra.gui.app import main
    sys.exit(main())


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()