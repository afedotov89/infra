"""
Template-specific environment setup script for the 'landing' template.
"""

import copy
import logging
from pathlib import Path
import secrets
import string
from infra.project_setup.environment import setup_bucket, setup_frontend_environment
from infra.project_setup.types import ProjectSetupContext

logger = logging.getLogger(__name__)


def setup(ctx: 'ProjectSetupContext') -> None:
    """
    Sets up the environment for the minimal static React landing template.
    Creates a Yandex Cloud bucket for static files and sets minimal secrets.
    """
    logger.info(f"Running landing template environment setup for project: {ctx.name}")

    # Setup static bucket for landing
    project_name = ctx.name
    bucket_name = project_name
    ctx.github_secrets['YC_BUCKET_NAME'] = bucket_name
    ctx.github_secrets['DOMAIN_NAME'] = f"{project_name}.website.yandexcloud.net"

    # Create Yandex Cloud bucket for static files
    result = setup_bucket(ctx, bucket_name, public_read=True)
    logger.info(f"Bucket creation attempt for {bucket_name}: {'successful' if result else 'failed or bucket already exists'}.")

    # Setup minimal frontend environment (if needed)
    frontend_dir = Path(ctx.project_dir) / 'frontend'
    frontend_ctx = copy.deepcopy(ctx)
    frontend_ctx.project_dir = frontend_dir

    setup_frontend_environment(frontend_ctx)
    if frontend_ctx.public_url:
        ctx.public_url = frontend_ctx.public_url


    logger.info("Landing template environment setup finished.")
