"""
Core project setup functionality.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable
import subprocess
import os
import importlib

from dotenv import load_dotenv

from infra.config import Config, ConfigError
from infra.providers.git import (
    create_repository,
    check_project_directory,
    create_project_directory,
    populate_project_directory,
    initialize_git_repository,
    LocalGitError
)
from infra.providers.git.local import find_github_secrets_in_workflow, is_git_initialized
from infra.providers.git.github import (
    create_repository as create_github_repo,
    set_repository_secret,
    setup_cicd,
    get_repository_secrets
)
from infra.project_setup.environment import (
    setup_python_environment,
    setup_database,
    setup_frontend_environment,
)
from infra.project_setup.types import ProjectSetupContext
from infra.providers.local.env import ProjectEnv

logger = logging.getLogger(__name__)


class SetupError(Exception):
    """Exception raised for project setup errors."""
    pass


def _setup_project_specific_environment(ctx: ProjectSetupContext) -> str:
    """
    Set up project-specific environment by executing template_setup.py if found.

    :param ctx: The project setup context object.
    :type ctx: ProjectSetupContext
    :return: The final database name used or determined by the template setup script.
    :rtype: str
    """
    logger.debug("Setting up project-specific environment via template_setup.py if available")
    final_db_name = ctx.db_name or ctx.name  # Default db name if not provided or overridden
    template_setup_path = ctx.project_dir / "template_setup.py"

    if template_setup_path.exists():
        logger.info(f"Found template setup script: {template_setup_path}")
        ctx.log_func(f"🔄 Running template-specific environment setup...")

        # Add project directory to path to allow importing template_setup
        sys.path.insert(0, str(ctx.project_dir.parent)) # Add parent to import 'project_dir.template_setup'
        module_name = f"{ctx.project_dir.name}.template_setup"

        try:
            template_module = importlib.import_module(module_name)
            if hasattr(template_module, "setup"):
                # Call the setup function from the template's script
                final_db_name = template_module.setup(ctx)
                logger.info(f"Template setup script executed successfully. Final DB name: {final_db_name}")
                ctx.log_func(f"ℹ️ Template-specific environment setup complete.")
            else:
                logger.warning(f"template_setup.py found but 'setup' function is missing.")
                ctx.log_func(f"⚠️ Template setup script found but 'setup' function is missing.")

        except ImportError as e:
            logger.error(f"Failed to import template setup script '{module_name}': {e}")
            ctx.log_func(f"⚠️ Error importing template setup script: {e}")
        except Exception as e:
            logger.error(f"Error executing template setup script: {e}", exc_info=True)
            ctx.log_func(f"⚠️ Error executing template setup script: {e}")
            # Decide if this should be a fatal error
            # raise SetupError(f"Failed to execute template setup script: {e}") from e
        finally:
            # Clean up sys.path
            if str(ctx.project_dir.parent) in sys.path:
                sys.path.remove(str(ctx.project_dir.parent))
            # Remove potentially cached module
            if module_name in sys.modules:
                del sys.modules[module_name]
    else:
        logger.info("No template_setup.py found. Skipping template-specific environment setup.")
        ctx.log_func("ℹ️ No template-specific setup script (template_setup.py) found.")
        # Optionally, run default logic here if needed for templates without the script
        # For now, we assume the script handles everything or nothing is needed.

    return final_db_name


def _initialize_setup_context(
    name: str,
    technologies: List[str],
    db_type: str,
    db_name: Optional[str],
    use_yandex_cloud: bool,
    use_local_docker: bool,
    project_dir: Path,
    log_func: Callable
) -> ProjectSetupContext:
    """
    Initialize the project setup context and fetch existing GitHub secrets.

    :param name: Project name
    :type name: str
    :param technologies: List of technologies included in the project
    :type technologies: List[str]
    :param db_type: Database type
    :type db_type: str
    :param db_name: Database name
    :type db_name: Optional[str]
    :param use_yandex_cloud: Whether to use Yandex Cloud
    :type use_yandex_cloud: bool
    :param use_local_docker: Whether to use local Docker
    :type use_local_docker: bool
    :param project_dir: Path to the project directory
    :type project_dir: Path
    :param log_func: Function to use for logging
    :type log_func: Callable
    :return: Initialized project setup context
    :rtype: ProjectSetupContext
    """
    logger.debug("Step 3.5 & 4: Setting up project-specific environment")
    # Create context object
    setup_ctx = ProjectSetupContext(
        name=name,
        technologies=technologies,
        db_type=db_type,
        db_name=db_name,
        use_yandex_cloud=use_yandex_cloud,
        use_local_docker=use_local_docker,
        project_dir=project_dir,
        log_func=log_func
    )

    # --- DEBUG LOG: Context ID --- #
    logger.debug(f"Created context object with id: {id(setup_ctx)}")
    # --- END DEBUG LOG --- #

    # --- Fetch Existing GitHub Secrets (Early) --- #
    log_func("🔄 Fetching existing secrets from GitHub...")
    try:
        # Store existing secret names in the context
        setup_ctx.existing_github_secrets = get_repository_secrets(setup_ctx.name)
        # --- DEBUG LOG: Inside Try --- #
        logger.debug(f"Assigned existing secrets in setup_project (try block): {setup_ctx.existing_github_secrets} (type: {type(setup_ctx.existing_github_secrets)})")
        # --- END DEBUG LOG --- #
        logger.info(f"Successfully fetched existing secrets for {setup_ctx.name}: {setup_ctx.existing_github_secrets}")
        log_func(f"   Found {len(setup_ctx.existing_github_secrets)} existing secrets.")
    except Exception as e:
        logger.warning(f"Could not fetch existing GitHub secrets for {setup_ctx.name}: {e}", exc_info=False)
        log_func(f"⚠️ Warning: Could not fetch existing secrets from GitHub for '{setup_ctx.name}'. Assuming none exist.")
        setup_ctx.existing_github_secrets = [] # Assume none if fetch fails
        # --- DEBUG LOG: Inside Except --- #
        logger.debug(f"Assigned existing secrets in setup_project (except block): {setup_ctx.existing_github_secrets} (type: {type(setup_ctx.existing_github_secrets)})")
        # --- END DEBUG LOG --- #

    env_dir = Path(setup_ctx.project_dir)
    env_file_path = env_dir / '.env'
    project_env = ProjectEnv(env_file_path)
    setup_ctx.project_env = project_env.read()
    logger.debug(f"Using environment file for Docker setup: {env_file_path}")

    return setup_ctx


def setup_project(
    name: str,
    technologies: List[str],
    private: bool = True,
    db_type: str = "postgres",
    db_name: Optional[str] = None,
    template_name: Optional[str] = None,
    use_yandex_cloud: bool = False,
    use_local_docker: bool = True,
    log_callback = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Set up a complete project infrastructure based on a template.

    This function:
    1. Creates a GitHub repository
    2. Checks local project directory
    3. Creates or initializes local project with template files
    4. Creates database in the cloud (if use_yandex_cloud is True) or locally in Docker (if use_local_docker is True)
    5. Sets up GitHub secrets based on workflow needs and DB credentials
    6. Sets up CI/CD variables
    7. Pushes code to GitHub
    8. Sets up container infrastructure (if use_yandex_cloud is True)
    9. Saves .env file from setup_ctx.project_env
    10. Finalizes project setup

    :param name: Project name
    :type name: str
    :param technologies: List of technologies included in the project
    :type technologies: List[str]
    :param private: Whether the repository should be private, defaults to True
    :type private: bool, optional
    :param db_type: Database type, defaults to "postgres"
    :type db_type: str, optional
    :param db_name: Database name (defaults to project name), defaults to None
    :type db_name: Optional[str], optional
    :param template_name: Name of the template to use (if specified), defaults to None
    :type template_name: Optional[str], optional
    :param use_yandex_cloud: Whether to use Yandex Cloud for database and container infrastructure, defaults to False
    :type use_yandex_cloud: bool, optional
    :param use_local_docker: Whether to create a local Docker database, defaults to True
    :type use_local_docker: bool, optional
    :param log_callback: Optional callback function for logging. If None, print to stdout., defaults to None
    :type log_callback: Callable, optional
    :param debug: Whether to enable debug logging with stack traces, defaults to False
    :type debug: bool, optional
    :return: Dict with setup results including repository URL, project directory, etc.
    :rtype: Dict[str, Any]
    :raises SetupError: If project setup fails
    """
    if not technologies and not template_name:
        logger.debug("Neither technologies nor template_name were specified")
        raise SetupError("Either technologies or template_name must be specified")

    # Use the provided log function or default to print
    log = log_callback or print

    logger.debug(f"Starting project setup for '{name}'")
    logger.debug(f"Technologies: {technologies}")
    logger.debug(f"Private repository: {private}")
    logger.debug(f"Database type: {db_type}")
    logger.debug(f"Database name: {db_name or '(default)'}")
    logger.debug(f"Template name: {template_name or '(none)'}")
    logger.debug(f"Use Yandex Cloud: {use_yandex_cloud}")
    logger.debug(f"Use local Docker: {use_local_docker}")

    if template_name:
        log(f"Setting up project: {name} with template: {template_name} and technologies: {', '.join(technologies)}")
    else:
        log(f"Setting up project: {name} with technologies: {', '.join(technologies)}")

    try:
        # Step 1: Create GitHub repository
        logger.debug("Step 1: Creating GitHub repository")
        repo, _ = _create_github_repository(name, private, log)

        # Step 2: Check local project directory
        logger.debug("Step 2: Checking local project directory")
        project_dir, dir_exists, is_empty = _check_project_directory(name, log)

        # Step 3: Create or initialize local project without pushing
        logger.debug("Step 3: Setting up local project files")
        _create_local_project_files(
            project_dir,
            dir_exists,
            is_empty,
            technologies,
            log,
            template_name
        )

        # Step 3.5 & 4: Set up project-specific environment (Python venv, database)
        setup_ctx = _initialize_setup_context(
            name=name,
            technologies=technologies,
            db_type=db_type,
            db_name=db_name,
            use_yandex_cloud=use_yandex_cloud,
            use_local_docker=use_local_docker,
            project_dir=project_dir,
            log_func=log
        )

        # Pass context object to the function
        # --- DEBUG LOG: Before _setup_project_specific_environment --- #
        logger.debug(f"Calling _setup_project_specific_environment with context id: {id(setup_ctx)}")
        # --- END DEBUG LOG --- #
        final_db_name = _setup_project_specific_environment(setup_ctx)

        # Step 5: Set up GitHub secrets based on workflow files
        logger.debug("Step 5: Setting up GitHub secrets")
        _setup_github_secrets(setup_ctx)

        # Step 6: Set up CI/CD variables
        logger.debug("Step 6: Setting up CI/CD variables")
        _setup_cicd_variables(setup_ctx)

        # Step 7: Push code to GitHub repository
        logger.debug("Step 7: Pushing to GitHub repository")
        _push_to_remote(project_dir, repo.clone_url, log)

        # Step 8: Set up container infrastructure
        logger.debug("Step 8: Setting up container infrastructure")
        _setup_container_infrastructure(name, log, use_yandex_cloud)

        # Step 9: Save .env file from setup_ctx.project_env
        logger.debug("Step 9: Saving .env file from setup_ctx.project_env")
        _save_env_file(setup_ctx)

        # Step 10: Complete project setup
        logger.debug("Step 10: Finalizing project setup")
        return _finalize_project_setup(
            ctx=setup_ctx, # Pass context
            repo_url=repo.html_url, # Pass repo URL
            final_db_name=final_db_name # Pass final DB name
        )

    except ConfigError as e:
        log_msg = f"Configuration error: {str(e)}"
        logger.error(log_msg, exc_info=debug) # Use exc_info=debug
        raise SetupError(log_msg) from e
    except LocalGitError as e:
        log_msg = f"Git or template error: {str(e)}"
        logger.error(log_msg, exc_info=debug) # Use exc_info=debug
        raise SetupError(log_msg) from e
    except Exception as e:
        log_msg = f"Unexpected error setting up project: {str(e)}"
        logger.error(log_msg, exc_info=debug) # Use exc_info=debug
        raise SetupError(log_msg) from e

    finally:
        # --- DEBUG LOG --- #
        logger.debug(f"State after secret fetch in setup_project: ctx.existing_github_secrets = {setup_ctx.existing_github_secrets} (type: {type(setup_ctx.existing_github_secrets)})")
        # --- END DEBUG LOG --- #


def _create_github_repository(name: str, private: bool, log_func: Callable) -> Tuple[Any, bool]:
    """
    Step 1: Create a GitHub repository for the project.

    :param name: Project name
    :type name: str
    :param private: Whether the repository should be private
    :type private: bool
    :param log_func: Function to use for logging
    :type log_func: Callable
    :return: Tuple containing the repository object and a boolean indicating if it already existed
    :rtype: Tuple[Any, bool]
    :raises LocalGitError: If repository creation fails
    """
    logger.debug(f"Starting repository creation process for {name} (private={private})")
    log_func("🔄 Creating GitHub repository...")
    repo, already_existed = create_repository(name, private)

    if already_existed:
        logger.debug(f"Repository {name} already exists at {repo.html_url}")
        log_func(f"ℹ️ Repository already exists: {repo.html_url}")
        log_func(f"   Skipping repository creation step.")
    else:
        logger.debug(f"Successfully created new repository {name} at {repo.html_url}")
        log_func(f"✅ Repository created: {repo.html_url}")

    return repo, already_existed


def _check_project_directory(name: str, log_func: Callable) -> Tuple[Path, bool, bool]:
    """
    Step 2: Check if the local project directory exists and is empty.

    :param name: Project name
    :type name: str
    :param log_func: Function to use for logging
    :type log_func: Callable
    :return: Tuple containing the project directory path, whether it exists, and whether it's empty
    :rtype: Tuple[Path, bool, bool]
    """
    logger.debug(f"Checking project directory for {name}")
    log_func("🔄 Checking local project directory...")
    projects_root = Config.get_projects_root_dir()
    logger.debug(f"Projects root directory: {projects_root}")
    project_dir, dir_exists, is_empty = check_project_directory(name, projects_root)

    if dir_exists:
        logger.debug(f"Project directory exists: {project_dir}, empty: {is_empty}")
        log_func(f"ℹ️ Project directory already exists: {project_dir}")
        if is_empty:
            log_func(f"   Directory is empty.")
        else:
            log_func(f"   Directory is not empty.")
    else:
        logger.debug(f"Project directory does not exist: {project_dir}")
        log_func(f"✅ Project directory checked")

    return project_dir, dir_exists, is_empty


def _initialize_git_repository(project_dir: Path, log_func: Callable) -> None:
    """
    Initialize a Git repository in the specified directory.

    :param project_dir: Path to the project directory
    :type project_dir: Path
    :param log_func: Function to use for logging
    :type log_func: Callable
    """
    logger.debug(f"Initializing git repository locally")
    subprocess.run(["git", "init", "-b", "main"], check=True, cwd=project_dir)
    subprocess.run(["git", "add", "-A"], check=True, cwd=project_dir)
    subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, cwd=project_dir)
    log_func(f"✅ Initialized Git repository locally")


def _create_local_project_files(
    project_dir: Path,
    dir_exists: bool,
    is_empty: bool,
    technologies: List[str],
    log_func: Callable,
    template_name: Optional[str] = None
) -> None:
    """
    Step 3: Set up the local project directory with template files without pushing to remote.

    :param project_dir: Path to the project directory
    :type project_dir: Path
    :param dir_exists: Whether the directory already exists
    :type dir_exists: bool
    :param is_empty: Whether the directory is empty
    :type is_empty: bool
    :param technologies: List of technologies to include
    :type technologies: List[str]
    :param log_func: Function to use for logging
    :type log_func: Callable
    :param template_name: Name of the template to use (if specified), defaults to None
    :type template_name: Optional[str], optional
    :raises LocalGitError: If there's an error with Git operations or template usage
    """
    logger.debug(f"Setting up local project files in {project_dir}")
    logger.debug(f"Directory exists: {dir_exists}, is empty: {is_empty}")
    logger.debug(f"Technologies: {technologies}, template: {template_name}")

    log_func("🔄 Creating local project files...")

    # Check if Git is already initialized
    git_is_initialized = dir_exists and is_git_initialized(project_dir)
    logger.debug(f"Git already initialized: {git_is_initialized}")

    # Create directory if needed
    if not dir_exists:
        logger.debug(f"Creating new project directory: {project_dir}")
        create_project_directory(project_dir)
        log_func(f"✅ Created project directory: {project_dir}")
    else:
        directory_state = "empty" if is_empty else "non-empty"
        logger.debug(f"Using existing {directory_state} directory: {project_dir}")
        log_func(f"ℹ️ Using existing {directory_state} directory: {project_dir}")

    # Populate with template files if new directory or empty existing directory
    should_populate = not dir_exists or is_empty
    if should_populate:
        logger.debug(f"Populating directory with template files")
        populate_project_directory(project_dir, technologies, template_name)
        log_func(f"✅ Populated project directory with template files")

    # Initialize Git if needed
    if git_is_initialized:
        logger.debug(f"Git repository already initialized")
        log_func(f"ℹ️ Git repository already initialized in project directory")
    else:
        _initialize_git_repository(project_dir, log_func)


def _push_to_remote(
    project_dir: Path,
    repo_url: str,
    log_func: Callable
) -> None:
    """
    Step 5: Push local project to remote repository.

    :param project_dir: Path to the project directory
    :type project_dir: Path
    :param repo_url: URL of the git repository
    :type repo_url: str
    :param log_func: Function to use for logging
    :type log_func: Callable
    :raises LocalGitError: If there's an error with Git operations
    """
    logger.debug(f"Pushing to remote repository: {repo_url}")
    log_func("🔄 Pushing to remote repository...")

    # Get GitHub credentials
    from infra.config import Config
    credentials = Config.get_github_credentials()
    token = credentials.get("token")
    username = credentials.get("username")

    if not token:
        logger.error("GitHub token not found in configuration")
        raise LocalGitError("GitHub token is required for Git operations")

    # Prepare environment with GitHub credentials
    git_env = os.environ.copy()

    # Создаем URL с встроенными учетными данными
    # Формат: https://username:token@github.com/username/repo.git
    auth_url = repo_url.replace("https://", f"https://{username}:{token}@")
    logger.debug(f"Using authenticated URL for Git operations")

    # Check if remote exists
    result = subprocess.run(
        ["git", "remote"],
        capture_output=True,
        text=True,
        check=True,
        cwd=project_dir
    )

    if "origin" in result.stdout.split():
        # Update remote URL
        subprocess.run(
            ["git", "remote", "set-url", "origin", auth_url],
            check=True,
            cwd=project_dir
        )
        logger.info(f"Updated remote URL")
    else:
        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", auth_url],
            check=True,
            cwd=project_dir
        )
        logger.info(f"Added remote 'origin'")

    # Push to remote
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        check=True,
        cwd=project_dir
    )

    # После успешного пуша, сбрасываем URL обратно на версию без учетных данных
    # чтобы не хранить токен в конфигурации Git
    subprocess.run(
        ["git", "remote", "set-url", "origin", repo_url],
        check=True,
        cwd=project_dir
    )

    logger.info(f"Pushed to remote repository")
    log_func(f"✅ Pushed to remote repository")


def _setup_github_secrets(ctx: ProjectSetupContext) -> None:
    """
    Step 3: Set up GitHub Actions secrets for the project using context.

    :param ctx: The project setup context.
    :type ctx: ProjectSetupContext
    """
    log_func = ctx.log_func
    repo_name = ctx.name
    project_dir = ctx.project_dir

    log_func(f"🔄 Configuring GitHub repository secrets for '{repo_name}'...")
    logger.info(f"Configuring GitHub secrets for repository {repo_name}")

    # --- Determine Required Secrets ---
    # Use helper function to find secrets defined in workflow files
    required_secrets = find_github_secrets_in_workflow(project_dir)
    if not required_secrets:
        log_func("ℹ️ No GitHub secrets found referenced in workflow files. Skipping secret setup.")
        logger.info(f"No required secrets found in workflows for {repo_name}. Skipping setup.")
        return
    log_func(f"   Secrets required by workflows: {', '.join(required_secrets)}")

    # --- Identify Secrets to Set/Update ---
    # Secrets generated during this setup run are in ctx.github_secrets
    secrets_to_set_from_context = ctx.github_secrets

    # Get existing secrets from the context (fetched earlier)
    existing_secrets = ctx.existing_github_secrets
    if existing_secrets is None:
        # This path should ideally not be reached anymore if secrets are fetched in setup_project
        log_func(f"⚠️ Internal Warning: Existing secrets were not pre-fetched. Check setup_project logic.")
        logger.error(f"Internal Error: existing_github_secrets is None in _setup_github_secrets for {repo_name}. Should have been fetched earlier.")
        existing_secrets = [] # Assume none to prevent crashing, but log error

    # --- DEBUG LOG: Context ID --- #
    logger.debug(f"Created context object with id: {id(ctx)}")
    # --- END DEBUG LOG --- #

    # Log which secrets were generated during this run
    if secrets_to_set_from_context:
        log_func(f"   Secrets generated or specified during this setup: {', '.join(secrets_to_set_from_context.keys())}")

    # Log which required secrets already exist in GitHub
    if existing_secrets:
        existing_required = [s for s in required_secrets if s in existing_secrets]
        if existing_required:
            log_func(f"   The following required secrets already exist in GitHub and will NOT be overwritten by generated values:")
            for secret in existing_required:
                log_func(f"   - {secret}")

    # --- Prepare Final Secrets Dictionary (Prioritize generated, skip existing) ---
    final_secrets_to_set = {}

    # 1. Add secrets generated during this run (from context)
    for name, value in secrets_to_set_from_context.items():
        if name in required_secrets:
            if name not in existing_secrets:
                final_secrets_to_set[name] = value
                logger.debug(f"Adding generated secret '{name}' to be set.")
            else:
                logger.debug(f"Skipping generated secret '{name}' as it already exists in GitHub.")
        else:
            logger.warning(f"Generated secret '{name}' is not listed as required by workflows. It will not be set.")

    # 2. Check for required secrets missing from both generated and existing
    missing_secrets = []
    for secret_name in required_secrets:
        if secret_name not in final_secrets_to_set and secret_name not in existing_secrets:
            # Try to find the missing secret using the Config class as a fallback
            try:
                secret_value = Config.get(secret_name)
                if secret_value:
                    final_secrets_to_set[secret_name] = secret_value
                    log_func(f"   Found missing required secret '{secret_name}' via Config.")
                    logger.info(f"Found missing secret '{secret_name}' via Config for {repo_name}.")
                else:
                    # Config.get might return None or empty string if set but empty
                    log_func(f"⚠️ Warning: Required secret '{secret_name}' found via Config but is empty. It will not be set.")
                    logger.warning(f"Required secret '{secret_name}' from Config is empty for {repo_name}.")
                    missing_secrets.append(secret_name) # Still considered missing if value is empty
            except ConfigError:
                # Config.get raises ConfigError if the variable is not found at all
                log_func(f"⚠️ Warning: Required secret '{secret_name}' is not generated, not in GitHub, and not found via Config.")
                logger.warning(f"Required secret '{secret_name}' not found via Config for {repo_name}.")
                missing_secrets.append(secret_name)

    # --- Set Secrets in GitHub --- #
    if final_secrets_to_set:
        log_func(f"   Attempting to set/update {len(final_secrets_to_set)} secrets in GitHub: {', '.join(final_secrets_to_set.keys())}")
        try:
            # Assuming setup_cicd is the function to actually set the secrets
            # It should ideally take the repo_name and the dictionary of secrets
            setup_cicd(repo_name=repo_name, secrets=final_secrets_to_set, ctx=ctx)
            log_func(f"✅ GitHub secrets configuration attempted for {len(final_secrets_to_set)} secrets.")
            logger.info(f"Called setup_cicd for {len(final_secrets_to_set)} secrets in {repo_name}.")
        except Exception as e:
            log_func(f"❌ Error setting GitHub secrets: {str(e)}")
            logger.error(f"Failed to set GitHub secrets for {repo_name}: {e}", exc_info=True)
            # Log which secrets failed if possible
            log_func(f"   Failed secrets: {', '.join(final_secrets_to_set.keys())}")
            # Decide if this should be a critical error or just a warning
    else:
        log_func("ℹ️ No new or missing secrets need to be set in GitHub.")
        logger.info(f"No secrets needed setting via setup_cicd for {repo_name}.")

    # --- Final Warnings for Missing Secrets --- #
    if missing_secrets:
        log_func(f"⚠️ Warning: The following required secrets are still missing and must be set manually in GitHub:")
        for secret in missing_secrets:
            log_func(f"   - {secret}")


def _setup_cicd_variables(ctx: ProjectSetupContext) -> None:
    """
    Step 4: Set up CI/CD variables for the project.

    :param ctx: The project setup context, including project name, directory, and db_info.
    :type ctx: ProjectSetupContext
    """
    log_func = ctx.log_func # Get log_func from context
    log_func("🔄 Setting up CI/CD variables...")
    # Placeholder: Add logic here to set up GitHub Actions variables if needed.
    # This might involve using ctx.name, ctx.project_dir, or other context info.
    # Example: repo.create_variable("MY_VARIABLE", "my_value")
    log_func("✅ CI/CD variables setup step completed (Placeholder)")


def _setup_container_infrastructure(name: str, log_func: Callable, use_yandex_cloud: bool = False) -> None:
    """
    Step 6: Set up container infrastructure for the project.

    :param name: Project name
    :type name: str
    :param log_func: Function to use for logging
    :type log_func: Callable
    :param use_yandex_cloud: Whether to use Yandex Cloud for container setup, defaults to False
    :type use_yandex_cloud: bool, optional
    """
    if not use_yandex_cloud:
        log_func("ℹ️ Skipping container infrastructure setup as Yandex Cloud operations are disabled")
        return

    # log_func("🔄 Setting up container infrastructure...")
    # from infra.providers.cloud.yandex.compute import setup_containers
    # setup_containers(name)
    # log_func("✅ Container infrastructure configured")


def _finalize_project_setup(
    ctx: ProjectSetupContext, # Accept context object
    repo_url: str,
    final_db_name: str
) -> Dict[str, Any]:
    """
    Step 9: Finalize project setup and return result using context.

    :param ctx: The project setup context.
    :type ctx: ProjectSetupContext
    :param repo_url: Repository URL
    :type repo_url: str
    :param final_db_name: Final database name used.
    :type final_db_name: str
    :return: Dictionary with setup results
    :rtype: Dict[str, Any]
    """
    log_func = ctx.log_func # Get log_func from context
    log_func("🔄 Finalizing project setup...")

    log_func(f"\nℹ️ Local project directory: {ctx.project_dir}")
    log_func(f"ℹ️ GitHub repository: {repo_url}")
    log_func(f"ℹ️ Project has been set up with: {', '.join(ctx.technologies)}")

    log_func(f"\n🚀 Project {ctx.name} is ready for development! 🚀")

    return {
        "project_name": ctx.name,
        "technologies": ctx.technologies,
        "repository_url": repo_url,
        "project_directory": str(ctx.project_dir),
        "database_name": final_db_name
    }

def _save_env_file(ctx: ProjectSetupContext) -> None:
    """
    Save the environment variables from the setup context to the project's .env file.

    :param ctx: The project setup context containing the project environment variables.
    :type ctx: ProjectSetupContext
    """
    log_func = ctx.log_func
    env_file_path = ctx.project_dir / '.env'

    if ctx.project_env:
        log_func("🔄 Saving environment variables to .env file...")
        with open(env_file_path, 'w') as env_file:
            for key, value in ctx.project_env.items():
                if value is not None:
                    env_file.write(f"{key}={value}\n")
        log_func(f"✅ Environment variables saved to {env_file_path}")
        logger.info(f"Saved environment variables to {env_file_path}")
    else:
        log_func("ℹ️ No environment variables to save.")
        logger.info("No environment variables found in setup context to save.")
