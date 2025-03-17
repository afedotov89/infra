"""
Local Git operations module.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Set
import re

logger = logging.getLogger(__name__)


class LocalGitError(Exception):
    """Exception raised for local Git operations errors."""
    pass


def check_project_directory(project_name: str, root_dir: str) -> tuple[Path, bool, bool]:
    """
    Check if the project directory exists and if it's empty.
    
    Args:
        project_name: Name of the project
        root_dir: Root directory for all projects
        
    Returns:
        tuple: (project_dir, exists, is_empty) where:
            - project_dir: Path object for the project directory
            - exists: True if directory exists
            - is_empty: True if directory is empty
            
    Raises:
        LocalGitError: If there's an error checking the directory
    """
    try:
        # Expand tilde in path for home directory
        expanded_root = os.path.expanduser(root_dir)
        
        # Create absolute Path object for the project directory
        project_dir = Path(expanded_root).resolve() / project_name
        
        # Check if directory exists
        exists = project_dir.exists()
        
        # Check if directory is empty (if it exists)
        is_empty = True
        if exists:
            # Directory is empty if it has no files and no subdirectories
            # We exclude .git directory from this check
            contents = [f for f in project_dir.iterdir() if f.name != '.git']
            is_empty = len(contents) == 0
            
        return project_dir, exists, is_empty
        
    except Exception as e:
        logger.error(f"Error checking project directory: {str(e)}")
        raise LocalGitError(f"Error checking project directory: {str(e)}")


def create_project_directory(project_dir: Path) -> None:
    """
    Create the project directory if it doesn't exist.
    
    Args:
        project_dir: Path object for the project directory
        
    Raises:
        LocalGitError: If there's an error creating the directory
    """
    try:
        # Ensure project_dir is an absolute path with no tilde
        project_dir = project_dir.resolve()
        
        # Create directory if it doesn't exist
        os.makedirs(project_dir, exist_ok=True)
        logger.info(f"Created project directory: {project_dir}")
    except Exception as e:
        logger.error(f"Error creating project directory: {str(e)}")
        raise LocalGitError(f"Error creating project directory: {str(e)}")


def populate_project_directory(
    project_dir: Path, 
    technologies: list[str],
    template_name: Optional[str] = None
) -> None:
    """
    Populate an empty project directory with boilerplate code based on selected technologies.
    
    This function copies template files from infra/templates directory based on the
    specified template_name.
    
    Args:
        project_dir: Path object for the project directory
        technologies: List of technologies to include
        template_name: Name of template to use (required)
        
    Raises:
        LocalGitError: If there's an error populating the directory or if template is not found
    """
    try:
        from infra.templates.generator import generate_boilerplate, list_available_templates, TemplateError
        
        # Get the project name from the directory path
        project_name = project_dir.name
        
        # Get available templates
        available_templates = list_available_templates()
        
        # Шаблон должен быть явно указан
        if not template_name:
            raise LocalGitError("Template name must be specified")
            
        # Проверяем наличие шаблона
        if template_name not in available_templates:
            raise LocalGitError(f"Specified template '{template_name}' not found in available templates")
            
        template_to_use = template_name
        
        # Use the template system to generate boilerplate
        # We're using an existing directory so we need to adjust parameters
        output_dir = project_dir.parent
        
        # Since we're handling git repository separately, don't initialize git here
        try:
            generate_boilerplate(
                project_name=project_name,
                template_name=template_to_use,
                output_dir=output_dir,
                initialize_git=False,
                force_existing_dir=True
            )
            
            logger.info(f"Populated project directory with template: {template_to_use}")
        except TemplateError as e:
            logger.error(f"Error using template system: {str(e)}")
            raise LocalGitError(f"Error using template system: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error populating project directory: {str(e)}")
        raise LocalGitError(f"Error populating project directory: {str(e)}")


def _create_basic_readme(project_dir: Path, technologies: list[str]) -> None:
    """
    Create a basic README file when no template is found.
    
    Args:
        project_dir: Path object for the project directory
        technologies: List of technologies to include
    """
    readme_content = f"""# Project

This project uses the following technologies:
{', '.join(technologies)}

## Getting Started

TODO: Add instructions for setting up the project locally.
"""
    with open(project_dir / "README.md", "w") as f:
        f.write(readme_content)
        
    logger.info("Created basic README.md file")


def is_git_initialized(project_dir: Path) -> bool:
    """
    Check if a Git repository is already initialized in the project directory.
    
    Args:
        project_dir: Path object for the project directory
        
    Returns:
        bool: True if Git is already initialized (.git directory exists)
    """
    git_dir = project_dir / ".git"
    return git_dir.exists()


def initialize_git_repository(
    project_dir: Path, 
    remote_url: str,
    branch: str = "main"
) -> bool:
    """
    Initialize a Git repository in the project directory, set up remote, and make initial commit.
    
    Args:
        project_dir: Path object for the project directory
        remote_url: URL of the remote repository
        branch: Name of the default branch
        
    Returns:
        bool: True if Git was newly initialized, False if Git was already initialized
        
    Raises:
        LocalGitError: If there's an error initializing the repository
    """
    try:
        # Change to project directory
        cwd = os.getcwd()
        os.chdir(project_dir)
        
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
        # Setting GIT_ASKPASS to 'echo' with token to avoid password prompts
        git_env["GIT_ASKPASS"] = "echo"
        git_env["GIT_TERMINAL_PROMPT"] = "0"
        # Set username and password in environment for Git to use
        git_env["GIT_USERNAME"] = username
        git_env["GIT_PASSWORD"] = token
        
        # Check if .git directory already exists
        git_dir = project_dir / ".git"
        already_initialized = git_dir.exists()
        
        if not already_initialized:
            # Initialize repository
            subprocess.run(["git", "init", "-b", branch], check=True, env=git_env)
            logger.info(f"Initialized Git repository in {project_dir}")
            
            # Configure Git credential helper to use environment variables
            subprocess.run(["git", "config", "credential.helper", ""], check=True, env=git_env)
            subprocess.run(["git", "config", "credential.helper", "env"], check=True, env=git_env)
            
            # Set up remote
            subprocess.run(
                ["git", "remote", "add", "origin", remote_url], 
                check=True,
                env=git_env
            )
            logger.info(f"Added remote 'origin' pointing to {remote_url}")
            
            # Add all files
            subprocess.run(["git", "add", "-A"], check=True, env=git_env)
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"], 
                capture_output=True, 
                text=True,
                check=True,
                env=git_env
            )
            
            if result.stdout.strip():
                # Make initial commit
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit"], 
                    check=True,
                    env=git_env
                )
                logger.info("Created initial commit")
                
                # Push to remote
                subprocess.run(
                    ["git", "push", "-u", "origin", branch], 
                    check=True,
                    env=git_env
                )
                logger.info(f"Pushed to remote repository")
            else:
                logger.info("No changes to commit")
        else:
            logger.info(f"Git repository already exists in {project_dir}")
            
            # Configure Git credential helper to use environment variables
            subprocess.run(["git", "config", "credential.helper", ""], check=True, env=git_env)
            subprocess.run(["git", "config", "credential.helper", "env"], check=True, env=git_env)
            
            # Check if remote exists
            result = subprocess.run(
                ["git", "remote"], 
                capture_output=True, 
                text=True, 
                check=True,
                env=git_env
            )
            
            if "origin" in result.stdout.split():
                # Update remote URL
                subprocess.run(
                    ["git", "remote", "set-url", "origin", remote_url], 
                    check=True,
                    env=git_env
                )
                logger.info(f"Updated remote URL")
            else:
                # Add remote if it doesn't exist
                subprocess.run(
                    ["git", "remote", "add", "origin", remote_url], 
                    check=True,
                    env=git_env
                )
                logger.info(f"Added remote 'origin' pointing to {remote_url}")
            
        return not already_initialized
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.cmd}. Output: {e.stdout} {e.stderr}")
        raise LocalGitError(f"Git command failed: {e.cmd}. Error: {e.stderr}")
    except Exception as e:
        logger.error(f"Error initializing Git repository: {str(e)}")
        raise LocalGitError(f"Error initializing Git repository: {str(e)}")
    finally:
        # Change back to original directory
        os.chdir(cwd) 


def find_github_secrets_in_workflow(project_dir: Path) -> Set[str]:
    """
    Scan the .github directory for workflow files and extract GitHub secrets references.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        Set of secret names found in the workflow files
    """
    github_dir = project_dir / ".github"
    secrets = set()
    
    if not github_dir.exists():
        return secrets
        
    # Regex pattern to find secrets.XXX references in workflow files
    secret_pattern = re.compile(r'\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}')
    
    # Look for workflow files in GitHub Actions directory
    workflows_dir = github_dir / "workflows"
    if workflows_dir.exists():
        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file, "r") as f:
                content = f.read()
                # Find all secret references
                for match in secret_pattern.finditer(content):
                    secret_name = match.group(1)
                    secrets.add(secret_name)
    
    return secrets 