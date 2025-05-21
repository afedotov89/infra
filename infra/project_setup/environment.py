import logging
import sys
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING
import subprocess
import os
import random
import socket
import shutil
import platform
import shlex
import copy
import json
import string

# Avoid circular import by importing specific types if needed, or pass necessary info directly
# from .types import ProjectSetupContext # This might cause issues, let's pass simple types for now
from infra.project_setup.types import ProjectSetupContext # Import ProjectSetupContext
from infra.providers.local.env import ProjectEnv
from infra.config import Config
# Assuming these functions exist or adjust imports as needed
from infra.providers.git.github import get_repository_secrets
# Import the specific functions needed from the postgres module
from infra.providers.cloud.yandex.db.postgres import (
    create_database as create_yc_db,
    check_database_exists as check_yc_db_exists,
    YandexCloudDBError
)
from infra.providers.local.env import get_project_env


logger = logging.getLogger(__name__)

# Constants
VENV_NAME = ".venv"
YANDEX_CLOUD_CLI = "yc"
DOCKER_COMPOSE_CMD = "docker compose" # Changed to list for subprocess


def _run_command(command: list[str], cwd: Path, log_func: Callable, check: bool = True) -> subprocess.CompletedProcess:
    """
    Runs a command in a subprocess, logging output.

    :param command: The command to run as a list of strings.
    :type command: list[str]
    :param cwd: The working directory for the command.
    :type cwd: Path
    :param log_func: Function to use for logging output.
    :type log_func: Callable
    :param check: Whether to raise an exception on non-zero exit code, defaults to True.
    :type check: bool, optional
    :return: The completed process object.
    :rtype: subprocess.CompletedProcess
    :raises subprocess.CalledProcessError: If the command fails and check is True.
    :raises FileNotFoundError: If the command executable is not found.
    """
    try:
        # Ensure command is a list of strings
        cmd_str = ' '.join(shlex.quote(part) for part in command)
        logger.debug(f"Running command: '{cmd_str}' in '{cwd}'")
        log_func(f"   Running: {cmd_str}...")

        process = subprocess.run(
            command,
            check=check,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=os.environ # Pass parent environment
        )
        # Log stdout/stderr concisely
        if process.stdout:
            logger.debug(f"Command stdout:\n{process.stdout.strip()}")
        if process.stderr:
            logger.debug(f"Command stderr:\n{process.stderr.strip()}") # Log stderr even on success for debug
        return process
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Command failed: {command}. Error: {stderr_msg}")
        log_func(f"   ❌ Command failed: {' '.join(command)}")
        log_func(f"   Error: {stderr_msg}")
        raise # Re-raise the exception to signal failure
    except FileNotFoundError:
        logger.error(f"Command not found: {command[0]}")
        log_func(f"   ❌ Command not found: {command[0]}. Is it installed and in PATH?")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred running command {command}: {e}")
        log_func(f"   ❌ An unexpected error occurred: {e}")
        raise


def _check_dependency(command: str, name: str, log_func: Callable) -> bool:
    """
    Checks if a command-line dependency is available.

    :param command: The command to check (e.g., 'docker').
    :type command: str
    :param name: The human-readable name of the dependency.
    :type name: str
    :param log_func: Function to use for logging.
    :type log_func: Callable
    :return: True if the dependency is available, False otherwise.
    :rtype: bool
    """
    if not shutil.which(command):
        logger.warning(f"'{command}' command not found, required for {name}.")
        log_func(f"⚠️ '{command}' command not found. Please install it to use {name} features.")
        return False
    logger.debug(f"Dependency check passed for '{command}'.")
    return True


def setup_python_environment(ctx: 'ProjectSetupContext') -> None:
    """
    Sets up a Python virtual environment and installs dependencies from requirements.txt.

    :param ctx: The project setup context. Expects ctx.project_dir to be set to the
                directory where the environment should be created.
    :type ctx: ProjectSetupContext
    """
    project_dir = Path(ctx.project_dir)
    log_func = ctx.log_func
    venv_dir = project_dir / VENV_NAME

    log_func(f"🐍 Setting up Python environment in '{project_dir}'...") # Use relative path for cleaner logs if possible
    logger.info(f"Setting up Python environment in {project_dir}")

    # 1. Check if venv already exists
    if venv_dir.exists():
        logger.info(f"Virtual environment already exists at {venv_dir}. Skipping creation.")
        log_func("ℹ️ Virtual environment already exists.")
        # Optionally, you could add logic here to check if it's functional
        # or if dependencies need updating, but for now, just skip.
        return # Exit early if venv exists

    # 2. Create virtual environment
    try:
        log_func(f"   Creating virtual environment using 'python -m venv {VENV_NAME}'...")
        _run_command(["python", "-m", "venv", VENV_NAME], cwd=project_dir, log_func=log_func)
        logger.info(f"Successfully created virtual environment at {venv_dir}")
        log_func("   ✅ Virtual environment created.")
    except Exception as e:
        logger.error(f"Failed to create virtual environment at {venv_dir}: {e}")
        log_func(f"   ❌ Failed to create virtual environment. See logs for details.")
        # Decide if this is a critical failure - perhaps raise an exception?
        return # Stop if venv creation fails

    # 3. Install dependencies from requirements.txt
    requirements_path = project_dir / "requirements.txt"
    if requirements_path.exists():
        log_func("   Installing dependencies from requirements.txt...")
        pip_executable = str(venv_dir / "bin" / "pip") if platform.system() != "Windows" else str(venv_dir / "Scripts" / "pip.exe")
        try:
            _run_command([pip_executable, "install", "-r", str(requirements_path)], cwd=project_dir, log_func=log_func)
            logger.info("Successfully installed dependencies from requirements.txt")
            log_func("   ✅ Dependencies installed.")
        except Exception as e:
            logger.error(f"Failed to install dependencies from {requirements_path}: {e}")
            log_func(f"   ❌ Failed to install dependencies. Check requirements.txt and logs.")
            # Consider if this failure should halt the process
    else:
        logger.info("No requirements.txt found. Skipping dependency installation.")
        log_func("   ℹ️ No requirements.txt found, skipping dependency installation.")

    log_func("🐍 Python environment setup complete.")
    logger.info(f"Python environment setup finished for {project_dir}")


def _setup_yandex_cloud_database(ctx: 'ProjectSetupContext') -> None:
    """
    Ensures a database exists in Yandex Cloud and its DATABASE_URL is available.
    Skips the operation if 'DATABASE_URL' is already present in ctx.github_secrets.
    Updates ctx.github_secrets['DATABASE_URL'] if the database is created or updated.

    :param ctx: The project setup context containing all necessary information.
    :type ctx: ProjectSetupContext
    """
    # --- DEBUG LOG: Context ID --- #
    logger.debug(f"Entering _setup_yandex_cloud_database with context id: {id(ctx)}")
    # --- END DEBUG LOG --- #

    # Extract values from context
    repo_name = ctx.name # Use project name as repo context for secrets
    db_type = ctx.db_type
    log_func = ctx.log_func
    final_db_name = ctx.db_name or ctx.name # Use consistent naming throughout

    # 1. Check if DATABASE_URL secret is already present in the actual GitHub repo secrets
    log_func(f"🔄 Checking GitHub repository secrets for '{repo_name}' (using pre-fetched data)...")
    logger.info(f"Checking pre-fetched GitHub secrets for repository {repo_name}")

    existing_secrets = ctx.existing_github_secrets
    if existing_secrets is None:
        # Fallback/Warning: If secrets weren't fetched earlier (should not happen in normal flow)
        logger.warning(f"Existing GitHub secrets not pre-fetched for {repo_name}. Cannot check GitHub.")
        log_func(f"⚠️ Warning: Could not check GitHub repository '{repo_name}' secrets (data not available).")
        # Fallback to checking if it was generated earlier *in this run*
        if 'DATABASE_URL' in ctx.github_secrets:
            log_func(f"ℹ️ DATABASE_URL was generated earlier in this run. Skipping Yandex Cloud DB setup (GitHub check skipped).")
            logger.info(f"DATABASE_URL found in ctx.github_secrets for {repo_name} (GitHub check skipped). Skipping YC DB setup.")
            return
        else:
            log_func(f"   Proceeding with Yandex Cloud DB setup (GitHub check skipped).")
            logger.info(f"Proceeding with YC DB setup for {repo_name} (GitHub check skipped).")

    elif 'DATABASE_URL' in existing_secrets:
        log_func(f"ℹ️ DATABASE_URL secret already exists in GitHub repository '{repo_name}'. Skipping Yandex Cloud DB setup.")
        logger.info(f"DATABASE_URL secret found in pre-fetched GitHub secrets for {repo_name}. Skipping YC DB setup.")
        return # Skip the rest of the function

    # Check if it was generated earlier *in this run* (if not found in GitHub)
    elif 'DATABASE_URL' in ctx.github_secrets:
        log_func(f"ℹ️ DATABASE_URL not in GitHub, but was generated earlier in this run. Skipping Yandex Cloud DB setup.")
        logger.info(f"DATABASE_URL found in ctx.github_secrets for {repo_name} (not in GitHub). Skipping YC DB setup.")
        return # Skip the rest of the function

    else:
        log_func(f"   DATABASE_URL secret not found in GitHub repository '{repo_name}' or generated earlier this run.")
        logger.info(f"DATABASE_URL not found in GitHub or ctx.github_secrets for {repo_name}.")

    # If secret isn't in GitHub and wasn't generated earlier in this run, proceed with YC setup
    log_func(f"   Proceeding...")
    log_func(f"🔄 Ensuring database '{final_db_name}' exists in Yandex Cloud and obtaining connection URL...")

    # 2. Ensure database and user exist (create or update password)
    # Errors during creation (config, command failure, etc.) will propagate up.
    try:
        # Create/ensure database in Yandex Cloud PostgreSQL using the imported function
        # This handles idempotency internally (user update, skip DB creation if exists)
        db_info = create_yc_db(final_db_name, db_type) # Use final_db_name

        # 3. Store the connection URL for GitHub secrets (in the local context for later use)
        # Use 'database_url' key which is returned by the underlying function
        db_url = db_info.get('database_url')
        if db_url:
            # Store in the local context dict, even if fetched from GitHub,
            # potentially useful for other steps in this run? Or maybe remove this if redundant.
            # For now, keep storing it here as the central place for the URL *during this run*.
            ctx.github_secrets['DATABASE_URL'] = db_url
            logger.info(f"Stored DATABASE_URL in ctx.github_secrets for repo {repo_name}")
            log_func(f"✅ Database '{final_db_name}' ensured/created in Yandex Cloud.") # Use final_db_name
            log_func(f"   Host: {db_info.get('host', 'N/A')}")
            log_func(f"   Username: {db_info.get('username', 'N/A')}")
            log_func(f"   DATABASE_URL obtained and stored locally (ctx.github_secrets) for potential later use.")
            # Note: Password is not logged for security.
        else:
            logger.error(f"No database_url returned from Yandex Cloud setup for {repo_name}")
            log_func(f"⚠️ Failed to obtain DATABASE_URL from Yandex Cloud for '{final_db_name}'.") # Use final_db_name
            # Consider raising an error here if the URL is essential
            raise YandexCloudDBError(f"Failed to retrieve database_url for {final_db_name}") # Use final_db_name

    except Exception as e:
        # Catch errors from create_yc_db or potential issues
        logger.error(f"Failed to setup Yandex Cloud database '{final_db_name}': {str(e)}", exc_info=True) # Use final_db_name
        log_func(f"❌ Failed to setup Yandex Cloud database '{final_db_name}': {str(e)}") # Use final_db_name
        # Re-raise the exception to halt the process if DB setup is critical
        raise


def _setup_docker_database(ctx: 'ProjectSetupContext') -> None:
    """
    Create a local database using Docker. Skips if DATABASE_URL exists in ctx.project_env.
    Updates ctx.project_env['DATABASE_URL'] if successful and writes to .env file.

    :param ctx: The project setup context containing all necessary information.
    :type ctx: ProjectSetupContext
    """
    # Extract values from context
    project_name = ctx.name
    # db_type = ctx.db_type # Not currently used for Docker setup (assumes postgres)
    db_name = ctx.db_name or ctx.name
    log_func = ctx.log_func

    # 1. Check if DATABASE_URL is already known in the project environment context
    if 'DATABASE_URL' in ctx.project_env:
        existing_url = ctx.project_env['DATABASE_URL']
        log_func(f"ℹ️ DATABASE_URL is already present in the local project context. Skipping Docker DB setup.")
        log_func(f"   Existing URL: {existing_url[:existing_url.find('@')] + '@...' if '@' in existing_url else existing_url}") # Log obfuscated URL
        logger.info(f"DATABASE_URL found in ctx.project_env for {project_name}. Skipping Docker DB setup.")
        return

    log_func(f"   DATABASE_URL not found in project context for '{project_name}'.")
    log_func("🔄 Creating local database in Docker...")

    # Setup ProjectEnv helper for interacting with the .env file
    env_dir = Path(ctx.project_dir)

    # --- Docker Setup Logic (Port finding, container management) ---

    # Check Docker dependency
    if not _check_dependency("docker", "Docker", log_func):
        raise Exception("Docker is required for local database setup but was not found.")

    # Generate random credentials
    username = f"user_{project_name.replace('-', '_')}"
    # Ensure password generation is robust
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choice(chars) for _ in range(16))

    # Find available port
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except socket.error:
                return False

    port = random.randint(32000, 65000)
    attempts = 0
    max_attempts = 50 # Increased attempts for finding a port
    while not is_port_available(port) and attempts < max_attempts:
        port = random.randint(32000, 65000)
        attempts += 1

    if attempts >= max_attempts:
        logger.error(f"Could not find an available port between 32000-65000 after {max_attempts} attempts.")
        raise Exception("Could not find available port for Docker database")

    # Start Docker container
    container_name = f"postgres_{project_name.replace('-', '_')}"
    log_func(f"   Starting Docker container '{container_name}' with PostgreSQL on port {port}...")

    try:
        # Check if container already exists using Docker CLI
        # Use a more reliable way to check if container exists (e.g., docker ps -a)
        docker_cmd = ["docker", "ps", "-a", "--filter", f"name=^{container_name}$", "--format", "{{.Names}}"]
        check_result = subprocess.run(docker_cmd, capture_output=True, text=True, check=False)

        if check_result.returncode == 0 and container_name in check_result.stdout.strip().splitlines():
            log_func(f"   Container '{container_name}' already exists. Removing it...")
            _run_command(["docker", "rm", "-f", container_name], cwd=env_dir, log_func=log_func)
        elif check_result.returncode != 0:
            logger.warning(f"Failed to check for existing Docker container '{container_name}': {check_result.stderr}")
            # Proceed with caution, attempt to create anyway

        # Create and start the container using _run_command
        run_cmd = [
            "docker", "run", "--name", container_name,
            "-e", f"POSTGRES_USER={username}",
            "-e", f"POSTGRES_PASSWORD={password}",
            "-e", f"POSTGRES_DB={db_name}",
            "-p", f"127.0.0.1:{port}:5432", # Bind to localhost explicitly
            "-d", "postgres:latest" # Specify image tag
        ]
        _run_command(run_cmd, cwd=env_dir, log_func=log_func)

        # Create DATABASE_URL
        # Use 127.0.0.1 which is more reliable than 'localhost' in some contexts
        database_url = f"postgresql://{username}:{password}@127.0.0.1:{port}/{db_name}"

        # Store the URL in the context
        ctx.project_env['DATABASE_URL'] = database_url
        logger.info(f"Stored DATABASE_URL in ctx.project_env for project {project_name}")

        log_func(f"✅ Database '{db_name}' created in Docker container '{container_name}'")
        log_func(f"   Container: {container_name}")
        log_func(f"   Port: {port}")
        log_func(f"   Username: {username}")
        log_func(f"   DATABASE_URL added to project environment")

    except subprocess.CalledProcessError as e:
        # Error logging already done by _run_command
        log_func(f"   ❌ Docker command failed. Check logs for details.")
        raise Exception(f"Docker setup failed for container '{container_name}'.")
    except Exception as e:
        logger.error(f"Error during Docker DB setup for '{container_name}': {e}", exc_info=True)
        log_func(f"   ❌ An unexpected error occurred during Docker setup: {e}")
        raise # Re-raise the exception


def setup_database(ctx: 'ProjectSetupContext') -> str:
    """
    Create a database for the project, delegating to cloud or local Docker methods.

    :param ctx: The project setup context containing all necessary information.
    :type ctx: ProjectSetupContext
    :return: The name of the database used/created.
    :rtype: str
    """
    # Extract log_func and calculate final_db_name for top-level use
    log_func = ctx.log_func
    final_db_name = ctx.db_name or ctx.name

    log_func("🔄 Checking if database needs to be created...")

    try:
        # Determine which method to use for database creation
        if ctx.use_yandex_cloud:
            # Pass ctx directly to the helper function
            _setup_yandex_cloud_database(ctx)
        if ctx.use_local_docker:
            # Pass ctx directly to the helper function
            _setup_docker_database(ctx)
        # else:
        #     log_func("ℹ️ Skipping database creation as both Yandex Cloud and local Docker are disabled")

    except Exception as e:
        logger.error(f"Failed to setup database: {str(e)}", exc_info=True)
        log_func(f"⚠️  Database creation failed: {str(e)}")
        log_func(f"   Continuing with project setup...")
        # Decide if failure is critical, maybe raise specific exception?

    return final_db_name


def setup_frontend_environment(ctx: 'ProjectSetupContext') -> None:
    """
    Checks for frontend package manager files and installs dependencies automatically.
    Operates within the directory specified by ctx.project_dir.

    :param ctx: The project setup context. Expects ctx.project_dir to point to the
                frontend subdirectory (e.g., '.../myproject/frontend').
    :type ctx: ProjectSetupContext
    """
    frontend_dir = Path(ctx.project_dir) # Use the directory directly from context
    log_func = ctx.log_func

    logger.debug(f"Checking for frontend setup in directory: {frontend_dir}")
    log_func(f"🔄 Setting up frontend environment in '{frontend_dir}'...")

    package_json_path = frontend_dir / "package.json"
    yarn_lock_path = frontend_dir / "yarn.lock"
    node_modules_path = frontend_dir / "node_modules"

    if not package_json_path.exists():
        logger.info(f"No {package_json_path} found in {frontend_dir}. Skipping frontend dependency setup.")
        log_func(f"   No package.json found in '{frontend_dir}'. Skipping frontend setup.")
        return

    # Check if node_modules already exists and is populated
    if node_modules_path.exists() and any(node_modules_path.iterdir()):
        logger.info(f"'{node_modules_path}' already exists and is not empty. Skipping installation.")
        log_func(f"ℹ️ Frontend dependencies already installed in '{frontend_dir}', skipping.")
        return

    manager = ""
    install_command_args = []

    if yarn_lock_path.exists():
        manager = "yarn"
        # Check if yarn is installed
        if _check_dependency("yarn", "Yarn package manager", log_func):
            logger.info("yarn.lock found, using 'yarn install'.")
            install_command_args = ["yarn", "install"]
        else:
            log_func("   ⚠️ yarn.lock found, but 'yarn' command not found. Skipping frontend setup.")
            logger.warning("yarn.lock found but yarn command not found.")
            return
    else:
        manager = "npm"
        # Check if npm is installed
        if _check_dependency("npm", "NPM package manager", log_func):
            logger.info("No yarn.lock found, using 'npm install'.")
            install_command_args = ["npm", "install"]
        else:
            log_func("   ⚠️ package.json found, but 'npm' command not found. Skipping frontend setup.")
            logger.warning("package.json found but npm command not found.")
            return

    log_func(f"   Using {manager} to install dependencies...")

    try:
        # Execute the install command using the helper
        _run_command(install_command_args, cwd=frontend_dir, log_func=log_func)
        logger.info(f"Frontend dependencies installed successfully in {frontend_dir}")
        log_func(f"✅ Frontend dependencies installed successfully using {manager}.")

    except Exception as e: # Catch errors from _run_command or other unexpected issues
        # Error logging is handled within _run_command, but add a summary here
        logger.error(f"Failed to install frontend dependencies using {manager} in {frontend_dir}. Error: {e}", exc_info=True)
        log_func(f"   ❌ Failed to install frontend dependencies using {manager}. Check logs.")
        # Potentially re-raise or handle differently depending on desired flow

    log_func(f"✅ Frontend setup finished for '{frontend_dir}'.")
    logger.debug(f"Frontend setup finished for {frontend_dir}")


def setup_bucket(ctx: 'ProjectSetupContext', bucket_name: str, public_read: bool = False) -> bool:
    """
    Creates a bucket in Yandex Cloud if it doesn't already exist and optionally configures it for website hosting.
    Args:
        ctx: The project setup context.
        bucket_name: The name of the bucket to create.
        public_read: If True, bucket will be public for read (default: False).

    Returns:
        bool: True if bucket exists or was created successfully (including optional configuration),
              False if creation failed.
    """
    from infra.providers.cloud.yandex.storage.bucket import create_bucket, check_bucket_exists
    log_func = ctx.log_func
    log_func(f"🔄 Checking if bucket '{bucket_name}' already exists...")
    if check_bucket_exists(bucket_name):
        log_func(f"ℹ️ Bucket '{bucket_name}' already exists. Skipping creation/configuration.")
        logger.info(f"Bucket {bucket_name} already exists. Skipping creation/configuration.")
        # Optionally, we could add logic here to *ensure* website config is set even if bucket exists
        # For now, if it exists, we assume it's configured correctly.
        return True

    log_func(f"   Bucket '{bucket_name}' does not exist. Proceeding with creation and configuration...")
    logger.info(f"Bucket {bucket_name} does not exist. Creating and configuring new bucket.")

    # Call create_bucket, passing the website configuration flag
    result = create_bucket(ctx, bucket_name, public_read=public_read)

    if result:
        # Log success based on the public_read flag
        if public_read:
            log_func(f"✅ Bucket '{bucket_name}' created and configured for website hosting successfully.")
            ctx.public_url = f"https://{bucket_name}.website.yandexcloud.net/"
        else:
            log_func(f"✅ Bucket '{bucket_name}' created successfully (website hosting skipped).")
    else:
        # Check if it might exist despite creation failure (e.g., race condition or API error)
        if check_bucket_exists(bucket_name):
            log_func(f"ℹ️ Bucket '{bucket_name}' now exists (detected after creation attempt). Assuming success.")
            # Here we might still want to attempt configuration if public_read is True,
            # but let's keep it simple for now.
            return True
        else:
            log_func(f"❌ Failed to create bucket '{bucket_name}'. Check logs for details.")
            return False
    return result