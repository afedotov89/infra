"""
Command Line Interface for the Infra toolkit.
"""

import sys
from typing import Optional, List

import click

from infra import __version__
from infra.config import Config, ConfigError
from infra.providers.git import create_repository
from infra.project_setup.core import setup_project as setup_project_operation, SetupError


# Available technologies that can be chosen for projects
AVAILABLE_TECHNOLOGIES = [
    "python",   # Python language
    "django",   # Python web framework
    "postgres", # Database
    "react",    # Frontend framework
    "redis"     # Cache/message broker
]


def validate_stack(ctx, param, value: str) -> List[str]:
    """Validate and split stack technologies."""
    if not value:
        return []
    
    technologies = value.split()
    invalid_techs = [tech for tech in technologies if tech not in AVAILABLE_TECHNOLOGIES]
    
    if invalid_techs:
        available_techs = ", ".join(AVAILABLE_TECHNOLOGIES)
        invalid_list = ", ".join(invalid_techs)
        raise click.BadParameter(
            f"Invalid technologies: {invalid_list}\n"
            f"Available technologies are: {available_techs}"
        )
    
    return technologies


@click.group()
@click.version_option(version=__version__)
def cli():
    """Infra - Infrastructure automation toolkit for rapid project deployment."""
    # This is the main command group
    pass


# Git operations group
@cli.group()
def git():
    """Git operations (repositories, CI/CD)."""
    pass


# Git repository operations subgroup
@git.group()
def repo():
    """Repository operations."""
    pass


@repo.command("create")
@click.option("--project-name", required=True, help="Repository/project name")
@click.option("--private/--public", default=True, help="Create a private repository")
def git_repo_create(project_name: str, private: bool):
    """Create a GitHub repository."""
    click.echo(f"Creating {'private' if private else 'public'} repository: {project_name}")
    repository, already_existed = create_repository(project_name, private)
    
    if already_existed:
        click.echo(f"Repository already exists: {repository.html_url}")
    else:
        click.echo(f"Repository created: {repository.html_url}")


# Create group for resource creation commands
@cli.group()
def create():
    """Create individual infrastructure resources (repo, db, container, bucket)."""
    pass


@create.command("repo")
@click.option("--name", required=True, help="Repository name")
@click.option("--private/--public", default=True, help="Create a private repository")
def create_repo(name: str, private: bool):
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
def create_db(name: str, db_type: str):
    """Create a database in the cloud."""
    click.echo(f"Creating database: {name} of type: {db_type}")
    # from infra.providers.cloud.yandex.db import create_database
    # create_database(name, db_type)


@create.command("container")
@click.option("--name", required=True, help="Container name")
@click.option("--image", required=True, help="Docker image to use")
def create_container(name: str, image: str):
    """Create a container in the cloud."""
    click.echo(f"Creating container: {name} with image: {image}")
    # from infra.providers.cloud.yandex.compute import create_container
    # create_container(name, image)


@create.command("bucket")
@click.option("--name", required=True, help="Bucket name")
def create_bucket(name: str):
    """Create a storage bucket in the cloud."""
    click.echo(f"Creating bucket: {name}")
    # from infra.providers.cloud.yandex.storage import create_bucket
    # create_bucket(name)


# Setup group for complex setup operations
@cli.group()
def setup():
    """Set up complete infrastructure components."""
    pass


@setup.command("project")
@click.option("--name", required=True, help="Project name")
@click.option(
    "--stack", 
    required=True,
    help="Technologies to include in the project (space-separated, e.g. 'django react postgres')",
    callback=validate_stack
)
@click.option("--private/--public", default=True, help="Create a private repository")
@click.option("--db-type", default="postgres", help="Database type")
@click.option("--db-name", help="Database name (defaults to project name)")
def setup_project(
    name: str, 
    stack: list[str], 
    private: bool, 
    db_type: str, 
    db_name: Optional[str] = None
):
    """
    Set up a complete project infrastructure.
    
    This command will:
    1. Create GitHub repository
    2. Check local project directory
    3. Create or initialize local project
    4. Set up CI/CD variables
    5. Create database in the cloud
    6. Set up container infrastructure
    7. Generate project boilerplate with selected technologies
    """
    try:
        setup_project_operation(
            name=name,
            technologies=stack,
            private=private,
            db_type=db_type,
            db_name=db_name,
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
def list():
    """List available resources and configurations."""
    pass


@list.command("templates")
def list_templates():
    """List available project technologies."""
    click.echo("Available technologies:")
    for tech in AVAILABLE_TECHNOLOGIES:
        click.echo(f"  - {tech}")


# Add GUI command
@cli.command("gui")
def gui():
    """Launch the graphical user interface."""
    click.echo("Launching GUI...")
    from infra.gui.app import main
    sys.exit(main())


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main() 