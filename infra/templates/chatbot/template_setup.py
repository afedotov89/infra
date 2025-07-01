"""
Template-specific environment setup script for the 'webapp' template.
"""

import logging
import os  # Add os import for path joining
from pathlib import Path # Import Path
import copy # Import copy
import secrets
import string
from infra.project_setup.environment import (
    setup_python_environment,
    setup_database,
    setup_bucket
)
from infra.project_setup.types import ProjectSetupContext
import subprocess

from infra.providers.local.env import ProjectEnv


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

    # Add any other webapp-specific setup steps here that coordinate between frontend/backend
    # or happen after both are initially set up.

    logger.info("Webapp template environment setup finished.")
    return final_db_name


def _setup_backend(ctx: 'ProjectSetupContext') -> str:
    """Sets up the backend environment (Python venv and database)."""
    logger.debug("Starting backend setup.")

    # Set Yandex Cloud infrastructure names based on project name
    project_name = ctx.name
    ctx.github_secrets['YC_API_GATEWAY_NAME'] = f"{project_name}-api-gateway"
    ctx.github_secrets['YC_STATIC_BUCKET_NAME'] = f"{project_name}-static"
    ctx.github_secrets['YC_CONTAINER_NAME'] = f"{project_name}-backend"
    ctx.github_secrets['ALLOWED_HOSTS'] = f"{project_name}.website.yandexcloud.net"
    ctx.github_secrets['CORS_ALLOWED_ORIGINS'] = f"https://{project_name}.website.yandexcloud.net"
    ctx.github_secrets['SITE_URL'] = f"https://{project_name}.website.yandexcloud.net"


    # Create Yandex Cloud bucket for Django static files using environment module
    bucket_name = f"{project_name}-static"
    result = setup_bucket(ctx, bucket_name, public_read=True)
    logger.info(f"Bucket creation attempt for {bucket_name}: {'successful' if result else 'failed or bucket already exists'}.")


    # Add local development variables to project_env
    local_env = ProjectEnv(Path(ctx.project_dir) / '.env')
    local_env.set_var('CORS_ALLOWED_ORIGINS', "http://localhost:3000")
    local_env.set_var('SITE_URL', "http://localhost:8000")

    # Generate Django Secret Key - using only safe characters
    safe_chars = string.ascii_letters + string.digits + '-_!@#$%^&*()[]{}|;:,.<>?'
    django_key = ''.join(secrets.choice(safe_chars) for i in range(50))
    ctx.github_secrets['DJANGO_SECRET_KEY'] = django_key

    logger.info(f"Set YC infrastructure secrets and generated Django key for project: {project_name}")

    # Use original project_dir from ctx to determine the backend path
    backend_dir = Path(ctx.project_dir)
    logger.info(f"Backend directory is {backend_dir}.")

    # Create a context specific to the backend setup
    backend_ctx = copy.deepcopy(ctx)
    backend_ctx.project_dir = backend_dir # Update project_dir
    backend_ctx.project_env = local_env.read()
    logger.debug(f"Created backend-specific context with project_dir: {backend_ctx.project_dir}")

    # 1. Set up Backend Python virtual environment using the backend context
    logger.info("Setting up Python environment for backend.")
    setup_python_environment(backend_ctx)

    # 2. Create database if needed, using the backend context
    logger.debug("Checking if database creation is needed (using backend context)")
    setup_database(backend_ctx)

    if 'DATABASE_URL' in backend_ctx.github_secrets:
        ctx.github_secrets['DATABASE_URL'] = backend_ctx.github_secrets['DATABASE_URL']

    for k, v in backend_ctx.project_env.items():
        local_env.set_var(k, v)

    logger.debug("Backend setup finished.")

