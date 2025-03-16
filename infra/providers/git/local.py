"""
Local Git operations module.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

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
    technologies: list[str]
) -> None:
    """
    Populate an empty project directory with boilerplate code.
    
    This is currently a stub function that will be expanded later.
    
    Args:
        project_dir: Path object for the project directory
        technologies: List of technologies to include
        
    Raises:
        LocalGitError: If there's an error populating the directory
    """
    try:
        # This is a placeholder. In the future, this will generate appropriate
        # boilerplate based on the selected technologies
        readme_content = f"""# Project

This project uses the following technologies:
{', '.join(technologies)}

## Getting Started

TODO: Add instructions for setting up the project locally.
"""
        with open(project_dir / "README.md", "w") as f:
            f.write(readme_content)
            
        logger.info(f"Populated project directory with boilerplate code")
        
    except Exception as e:
        logger.error(f"Error populating project directory: {str(e)}")
        raise LocalGitError(f"Error populating project directory: {str(e)}")


def initialize_git_repository(
    project_dir: Path, 
    remote_url: str,
    branch: str = "main"
) -> None:
    """
    Initialize a Git repository in the project directory, set up remote, and make initial commit.
    
    Args:
        project_dir: Path object for the project directory
        remote_url: URL of the remote repository
        branch: Name of the default branch
        
    Raises:
        LocalGitError: If there's an error initializing the repository
    """
    try:
        # Change to project directory
        cwd = os.getcwd()
        os.chdir(project_dir)
        
        # Add token to remote URL for authentication
        from infra.config import Config
        credentials = Config.get_github_credentials()
        token = credentials.get("token")
        
        # Replace https://github.com with https://token@github.com
        authenticated_url = remote_url
        if token and "https://" in remote_url:
            authenticated_url = remote_url.replace("https://", f"https://{token}@")
        
        # Check if .git directory already exists
        git_dir = project_dir / ".git"
        if not git_dir.exists():
            # Initialize repository
            subprocess.run(["git", "init", "-b", branch], check=True)
            logger.info(f"Initialized Git repository in {project_dir}")
        else:
            logger.info(f"Git repository already exists in {project_dir}")
            
        # Set up remote
        remote_exists = False
        result = subprocess.run(
            ["git", "remote"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        if "origin" in result.stdout.split():
            # Check if remote URL matches
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            if result.stdout.strip() != remote_url:
                # Update remote URL
                subprocess.run(
                    ["git", "remote", "set-url", "origin", authenticated_url], 
                    check=True
                )
                logger.info(f"Updated remote URL to {remote_url}")
            else:
                remote_exists = True
                # We still need to update the URL with credentials for push
                subprocess.run(
                    ["git", "remote", "set-url", "origin", authenticated_url], 
                    check=True
                )
                logger.info(f"Remote 'origin' already points to {remote_url}")
        else:
            # Add remote
            subprocess.run(
                ["git", "remote", "add", "origin", authenticated_url], 
                check=True
            )
            logger.info(f"Added remote 'origin' pointing to {remote_url}")
            
        # Add all files
        subprocess.run(["git", "add", "-A"], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            # Make initial commit
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"], 
                check=True
            )
            logger.info("Created initial commit")
            
            # Push to remote
            subprocess.run(
                ["git", "push", "-u", "origin", branch], 
                check=True
            )
            logger.info(f"Pushed to remote repository")
        else:
            logger.info("No changes to commit")
            
            if not remote_exists:
                # If remote doesn't exist yet, push
                subprocess.run(
                    ["git", "push", "-u", "origin", branch], 
                    check=True
                )
                logger.info(f"Pushed to remote repository")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e.cmd}. Output: {e.stdout} {e.stderr}")
        raise LocalGitError(f"Git command failed: {e.cmd}. Error: {e.stderr}")
    except Exception as e:
        logger.error(f"Error initializing Git repository: {str(e)}")
        raise LocalGitError(f"Error initializing Git repository: {str(e)}")
    finally:
        # Change back to original directory
        os.chdir(cwd) 