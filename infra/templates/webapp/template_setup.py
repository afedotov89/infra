"""
Template-specific environment setup script for the 'webapp' template.
"""

import logging
import os  # Add os import for path joining
from pathlib import Path # Import Path
import copy # Import copy
from infra.project_setup.environment import (
    setup_python_environment,
    setup_database,
    setup_frontend_environment
)
from infra.project_setup.types import ProjectSetupContext


logger = logging.getLogger(__name__)


def setup(ctx: 'ProjectSetupContext') -> str:
    """
    Sets up the Python environment and database specifically for the webapp template,
    coordinating backend and frontend setup steps.

    Args:
        ctx: The project setup context containing all necessary information.

    Returns:
        The final database name used (determined during backend setup).
    """
    logger.info(f"Running webapp template environment setup for project: {ctx.name}")

    # 1. Setup Backend
    final_db_name = _setup_backend(ctx)

    # 2. Setup Frontend
    _setup_frontend(ctx)

    # Add any other webapp-specific setup steps here that coordinate between frontend/backend
    # or happen after both are initially set up.

    logger.info("Webapp template environment setup finished.")
    return final_db_name


def _setup_backend(ctx: 'ProjectSetupContext') -> str:
    """Sets up the backend environment (Python venv and database)."""
    logger.debug("Starting backend setup.")

    # Use original project_dir from ctx to determine the backend path
    backend_dir = Path(ctx.project_dir) / 'backend'
    logger.info(f"Backend directory is {backend_dir}.")

    # Create a context specific to the backend setup
    backend_ctx = copy.deepcopy(ctx)
    backend_ctx.project_dir = str(backend_dir) # Update project_dir
    logger.debug(f"Created backend-specific context with project_dir: {backend_ctx.project_dir}")

    # 1. Set up Backend Python virtual environment using the backend context
    logger.info("Setting up Python environment for backend.")
    setup_python_environment(backend_ctx)

    # 2. Create database if needed, using the backend context
    logger.debug("Checking if database creation is needed (using backend context)")
    setup_database(backend_ctx)

    if 'DATABASE_URL' in backend_ctx.github_secrets:
        ctx.github_secrets['DATABASE_URL'] = backend_ctx.github_secrets['DATABASE_URL']
    if 'DATABASE_URL' in backend_ctx.project_env:
        ctx.project_env['DATABASE_URL'] = backend_ctx.project_env['DATABASE_URL']

    logger.debug("Backend setup finished.")


def _setup_frontend(ctx: 'ProjectSetupContext'):
    """Performs setup steps for the frontend environment."""
    logger.debug("Starting frontend setup.")

    # Determine frontend directory relative to the original project root
    frontend_dir = Path(ctx.project_dir) / 'frontend'
    logger.info(f"Frontend directory is {frontend_dir}.")

    # Create a context specific to the frontend setup
    frontend_ctx = copy.deepcopy(ctx)
    frontend_ctx.project_dir = str(frontend_dir) # Update project_dir
    logger.debug(f"Created frontend-specific context with project_dir: {frontend_ctx.project_dir}")

    # Call the centralized function with the frontend context
    logger.info("Setting up frontend environment.")
    setup_frontend_environment(frontend_ctx)

    logger.debug("Frontend setup finished.")
