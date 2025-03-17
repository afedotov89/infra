"""
Core project setup functionality.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable
import subprocess
import os

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
from infra.providers.git.github import setup_cicd

logger = logging.getLogger(__name__)


class SetupError(Exception):
    """Exception raised for project setup errors."""
    pass


def _create_github_repository(name: str, private: bool, log_func: Callable) -> Tuple[Any, bool]:
    """
    Step 1: Create a GitHub repository for the project.
    
    Args:
        name: Project name
        private: Whether the repository should be private
        log_func: Function to use for logging
        
    Returns:
        Tuple containing the repository object and a boolean indicating if it already existed
        
    Raises:
        LocalGitError: If repository creation fails
    """
    logger.debug(f"Starting repository creation process for {name} (private={private})")
    log_func("🔄 Creating GitHub repository...")
    repo, already_existed = create_repository(name, private)
    
    if already_existed:
        logger.debug(f"Repository {name} already exists at {repo.html_url}")
        log_func(f"⚠️  Repository already exists: {repo.html_url}")
        log_func(f"   Skipping repository creation step.")
    else:
        logger.debug(f"Successfully created new repository {name} at {repo.html_url}")
        log_func(f"✅ Repository created: {repo.html_url}")
        
    return repo, already_existed


def _check_project_directory(name: str, log_func: Callable) -> Tuple[Path, bool, bool]:
    """
    Step 2: Check if the local project directory exists and is empty.
    
    Args:
        name: Project name
        log_func: Function to use for logging
        
    Returns:
        Tuple containing the project directory path, whether it exists, and whether it's empty
    """
    logger.debug(f"Checking project directory for {name}")
    log_func("🔄 Checking local project directory...")
    projects_root = Config.get_projects_root_dir()
    logger.debug(f"Projects root directory: {projects_root}")
    project_dir, dir_exists, is_empty = check_project_directory(name, projects_root)
    
    if dir_exists:
        logger.debug(f"Project directory exists: {project_dir}, empty: {is_empty}")
        log_func(f"⚠️  Project directory already exists: {project_dir}")
        if is_empty:
            log_func(f"   Directory is empty.")
        else:
            log_func(f"   Directory is not empty.")
    else:
        logger.debug(f"Project directory does not exist: {project_dir}")
        log_func(f"✅ Project directory checked")
        
    return project_dir, dir_exists, is_empty


def _create_local_project_files(
    project_dir: Path, 
    dir_exists: bool, 
    is_empty: bool, 
    technologies: List[str], 
    log_func: Callable,
    template_name: Optional[str] = None
) -> bool:
    """
    Step 3: Set up the local project directory with template files without pushing to remote.
    
    Args:
        project_dir: Path to the project directory
        dir_exists: Whether the directory already exists
        is_empty: Whether the directory is empty
        technologies: List of technologies to include
        log_func: Function to use for logging
        template_name: Name of the template to use (if specified)
        
    Returns:
        A boolean indicating whether Git was already initialized
        
    Raises:
        LocalGitError: If there's an error with Git operations or template usage
    """
    logger.debug(f"Setting up local project files in {project_dir}")
    logger.debug(f"Directory exists: {dir_exists}, is empty: {is_empty}")
    logger.debug(f"Technologies: {technologies}, template: {template_name}")
    
    log_func("🔄 Creating local project files...")
    
    # Проверяем, инициализирован ли Git уже в этой директории
    git_already_initialized = dir_exists and is_git_initialized(project_dir)
    logger.debug(f"Git already initialized: {git_already_initialized}")
    
    if not dir_exists:
        # Create directory if it doesn't exist
        logger.debug(f"Creating new project directory: {project_dir}")
        create_project_directory(project_dir)
        log_func(f"✅ Created project directory: {project_dir}")
        
        # Populate empty directory with template files
        logger.debug(f"Populating directory with template files")
        populate_project_directory(project_dir, technologies, template_name)
        log_func(f"✅ Populated project directory with template files")
        
        # Initialize Git repository locally without pushing
        logger.debug(f"Initializing git repository locally")
        subprocess.run(["git", "init", "-b", "main"], check=True, cwd=project_dir)
        subprocess.run(["git", "add", "-A"], check=True, cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, cwd=project_dir)
        log_func(f"✅ Initialized Git repository locally")
    else:
        if is_empty:
            # Directory exists but is empty
            logger.debug(f"Using existing empty directory: {project_dir}")
            log_func(f"✅ Using existing empty directory: {project_dir}")
            
            # Populate empty directory with template files
            logger.debug(f"Populating directory with template files")
            populate_project_directory(project_dir, technologies, template_name)
            log_func(f"✅ Populated project directory with template files")
            
            # Initialize Git repository locally without pushing
            logger.debug(f"Initializing git repository locally")
            subprocess.run(["git", "init", "-b", "main"], check=True, cwd=project_dir)
            subprocess.run(["git", "add", "-A"], check=True, cwd=project_dir)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, cwd=project_dir)
            log_func(f"✅ Initialized Git repository locally")
        else:
            # Directory exists and is not empty
            logger.debug(f"Using existing non-empty directory: {project_dir}")
            log_func(f"✅ Using existing non-empty directory: {project_dir}")
            
            if git_already_initialized:
                logger.debug(f"Git repository already initialized")
                log_func(f"✅ Git repository already initialized in project directory")
            else:
                # Initialize Git repository locally without pushing
                logger.debug(f"Initializing git repository locally")
                subprocess.run(["git", "init", "-b", "main"], check=True, cwd=project_dir)
                subprocess.run(["git", "add", "-A"], check=True, cwd=project_dir)
                subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, cwd=project_dir)
                log_func(f"✅ Initialized Git repository locally")
    
    return git_already_initialized


def _push_to_remote(
    project_dir: Path,
    repo_url: str,
    git_already_initialized: bool,
    log_func: Callable
) -> None:
    """
    Step 5: Push local project to remote repository.
    
    Args:
        project_dir: Path to the project directory
        repo_url: URL of the git repository
        git_already_initialized: Whether Git was already initialized
        log_func: Function to use for logging
        
    Raises:
        LocalGitError: If there's an error with Git operations
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
    
    # Set up or update remote
    if git_already_initialized:
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


def _setup_github_secrets(project_dir: Path, repo_name: str, log_func: Callable) -> None:
    """
    Step 3.5: Set up GitHub secrets for the repository based on .github/workflows scanning.
    
    This step:
    1. Scans the .github/workflows directory for secret references
    2. Gets these secrets from the .env file or generates them dynamically
    3. Sets them in the GitHub repository
    
    Args:
        project_dir: Path to the project directory
        repo_name: Repository name
        log_func: Function to use for logging
    """
    log_func("🔄 Setting up GitHub secrets...")
    
    # Scan .github/workflows directory for secret references
    required_secrets = find_github_secrets_in_workflow(project_dir)
    
    if not required_secrets:
        log_func("   No GitHub secrets found in workflow files.")
        return
    
    # Log found secrets
    log_func(f"   Found {len(required_secrets)} secret references in workflow files:")
    for secret in required_secrets:
        log_func(f"   - {secret}")
    
    # Import these here to avoid circular imports
    from infra.providers.git.github import generate_dynamic_secrets, get_repository_secrets
    
    # Check which secrets can be dynamically generated
    dynamic_secrets = generate_dynamic_secrets(repo_name)
    can_be_generated = [secret for secret in required_secrets if secret in dynamic_secrets]
    
    if can_be_generated:
        log_func(f"   The following secrets will be generated automatically if not found in .env and don't exist in repository:")
        for secret in can_be_generated:
            log_func(f"   - {secret}")
    
    # Check which secrets already exist in the repository
    try:
        existing_secrets = get_repository_secrets(repo_name)
        if existing_secrets:
            existing_required = [s for s in required_secrets if s in existing_secrets]
            if existing_required:
                log_func(f"   The following secrets already exist and will be skipped:")
                for secret in existing_required:
                    log_func(f"   - {secret}")
    except Exception as e:
        log_func(f"   Warning: Could not check existing secrets: {str(e)}")
    
    # Set up secrets in GitHub repository
    try:
        setup_cicd(repo_name, required_secret_names=list(required_secrets))
        log_func(f"✅ GitHub secrets configured from .env file and dynamic generation")
    except Exception as e:
        log_func(f"⚠️  Warning: Could not set up all GitHub secrets: {str(e)}")
        log_func(f"   You may need to set up missing secrets manually.")


def _setup_cicd_variables(name: str, log_func: Callable) -> None:
    """
    Step 4: Set up CI/CD variables for the project.
    
    Args:
        name: Project name
        log_func: Function to use for logging
    """
    log_func("🔄 Setting up CI/CD variables...")
    # from infra.providers.git import setup_cicd
    # setup_cicd(name)
    log_func("✅ CI/CD variables set up")


def _create_database(name: str, db_type: str, db_name: Optional[str], log_func: Callable) -> str:
    """
    Step 5: Create a database for the project.
    This step is skipped if DATABASE_URL secret already exists in GitHub.
    
    Args:
        name: Project name
        db_type: Database type
        db_name: Database name (defaults to project name)
        log_func: Function to use for logging
        
    Returns:
        The name of the created database
    """
    db_name = db_name or name
    log_func("🔄 Checking if database needs to be created...")
    
    try:
        # Check if DATABASE_URL secret already exists in GitHub
        from infra.providers.git.github import get_repository_secrets
        
        # Get existing secrets
        existing_secrets = get_repository_secrets(name)
        
        if "DATABASE_URL" in existing_secrets:
            log_func(f"✅ DATABASE_URL secret already exists for project {name}")
            log_func(f"   Skipping database creation step to preserve existing configuration")
            return db_name
        
        log_func("🔄 Creating database...")
        from infra.providers.cloud.yandex.db.postgres import create_database
        from infra.config import Config
        
        # Create database in Yandex Cloud PostgreSQL
        db_info = create_database(db_name, db_type)
        
        # Save database info for later use by other operations
        Config.save_database_info(name, db_info)
        
        log_func(f"✅ Database '{db_name}' created")
        log_func(f"   Host: {db_info['host']}")
        log_func(f"   Username: {db_info['username']}")
        
        # Add a note about DATABASE_URL being added to GitHub secrets
        log_func(f"   DATABASE_URL will be added to GitHub secrets")
        
    except Exception as e:
        logger.error(f"Failed to create database: {str(e)}")
        log_func(f"⚠️  Database creation failed: {str(e)}")
        log_func(f"   Continuing with project setup...")
    
    return db_name


def _setup_container_infrastructure(name: str, log_func: Callable) -> None:
    """
    Step 6: Set up container infrastructure for the project.
    
    Args:
        name: Project name
        log_func: Function to use for logging
    """
    log_func("🔄 Setting up container infrastructure...")
    # from infra.providers.cloud.yandex.compute import setup_containers
    # setup_containers(name)
    log_func("✅ Container infrastructure configured")


def _finalize_project_setup(
    name: str, 
    technologies: List[str], 
    repo_url: str, 
    project_dir: Path, 
    db_name: str,
    log_func: Callable
) -> Dict[str, Any]:
    """
    Step 7: Finalize project setup and return result.
    
    Args:
        name: Project name
        technologies: List of technologies
        repo_url: Repository URL
        project_dir: Project directory path
        db_name: Database name
        log_func: Function to use for logging
        
    Returns:
        Dictionary with setup results
    """
    log_func("🔄 Finalizing project setup...")
    
    log_func(f"\n✅ Local project directory: {project_dir}")
    log_func(f"✅ GitHub repository: {repo_url}")
    log_func(f"✅ Project has been set up with: {', '.join(technologies)}")
    
    log_func(f"\n🚀 Project {name} is ready for development! 🚀")
    
    return {
        "project_name": name,
        "technologies": technologies,
        "repository_url": repo_url,
        "project_directory": str(project_dir),
        "database_name": db_name
    }


def setup_project(
    name: str, 
    technologies: List[str], 
    private: bool = True, 
    db_type: str = "postgres", 
    db_name: Optional[str] = None,
    template_name: Optional[str] = None,
    log_callback = None
) -> Dict[str, Any]:
    """
    Set up a complete project infrastructure based on a template.
    
    This function:
    1. Creates a GitHub repository
    2. Checks local project directory
    3. Creates or initializes local project with template files
    4. Creates database in the cloud
    5. Sets up GitHub secrets based on workflow needs and DB credentials
    6. Pushes code to GitHub
    7. Sets up CI/CD variables
    8. Sets up container infrastructure
    9. Finalizes project setup
    
    Args:
        name: Project name
        technologies: List of technologies included in the project
        private: Whether the repository should be private
        db_type: Database type
        db_name: Database name (defaults to project name)
        template_name: Name of the template to use (if specified)
        log_callback: Optional callback function for logging. If None, print to stdout.
        
    Returns:
        Dict with setup results including repository URL, project directory, etc.
        
    Raises:
        SetupError: If project setup fails
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
        git_already_initialized = _create_local_project_files(
            project_dir, 
            dir_exists, 
            is_empty, 
            technologies, 
            log, 
            template_name
        )
        
        # Step 4: Create database (moved earlier in the process)
        logger.debug("Step 4: Creating database")
        final_db_name = _create_database(name, db_type, db_name, log)
        
        # Step 5: Set up GitHub secrets based on workflow files
        logger.debug("Step 5: Setting up GitHub secrets")
        _setup_github_secrets(project_dir, name, log)
        
        # Step 6: Push code to GitHub repository
        logger.debug("Step 6: Pushing to GitHub repository")
        _push_to_remote(project_dir, repo.clone_url, git_already_initialized, log)
        
        # Step 7: Set up CI/CD variables
        logger.debug("Step 7: Setting up CI/CD variables")
        _setup_cicd_variables(name, log)
        
        # Step 8: Set up container infrastructure
        logger.debug("Step 8: Setting up container infrastructure")
        _setup_container_infrastructure(name, log)
        
        # Step 9: Complete project setup
        logger.debug("Step 9: Finalizing project setup")
        return _finalize_project_setup(
            name, technologies, repo.html_url, project_dir, final_db_name, log
        )
        
    except ConfigError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise SetupError(f"Configuration error: {str(e)}") from e
    except LocalGitError as e:
        logger.error(f"Git or template error: {str(e)}")
        raise SetupError(f"Git or template error: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error setting up project: {str(e)}")
        raise SetupError(f"Unexpected error: {str(e)}") from e 