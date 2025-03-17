"""
GitHub API integration module.
"""

import logging
import os
from typing import Dict, List, Optional

from github import Github, GithubException, Repository

from infra.config import Config

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """Exception raised for GitHub API errors."""
    pass


def get_github_client() -> Github:
    """
    Initialize and return a GitHub API client.
    
    Returns:
        Github: Initialized GitHub client
        
    Raises:
        GitHubError: If authentication fails
    """
    credentials = Config.get_github_credentials()
    try:
        return Github(credentials["token"])
    except Exception as e:
        logger.error(f"Failed to initialize GitHub client: {str(e)}")
        raise GitHubError(f"GitHub authentication failed: {str(e)}")


def create_repository(
    name: str, 
    private: bool = True, 
    description: Optional[str] = None,
    auto_init: bool = False
) -> tuple[Repository.Repository, bool]:
    """
    Create a GitHub repository.
    
    Args:
        name: Repository name
        private: Whether the repository should be private
        description: Optional repository description
        auto_init: Whether to initialize with a README
        
    Returns:
        Tuple containing the repository object and a boolean indicating if it already existed
        
    Raises:
        GitHubError: If repository creation fails
    """
    client = get_github_client()
    
    try:
        logger.info(f"Creating {'private' if private else 'public'} repository: {name}")
        logger.debug(f"Repository creation details - name: {name}, private: {private}, auto_init: {auto_init}")
        
        # Check if repository already exists
        user = client.get_user()
        logger.debug(f"Checking if repository '{name}' already exists for user: {user.login}")
        
        for repo in user.get_repos():
            if repo.name == name:
                logger.info(f"Repository {name} already exists at {repo.html_url}")
                return repo, True
        
        # Create repository
        repo = user.create_repo(
            name=name,
            private=private,
            description=description or f"{name} project",
            auto_init=auto_init
        )
        
        logger.debug(f"Repository created with id: {repo.id}, full name: {repo.full_name}")
        logger.info(f"Repository created successfully at {repo.html_url}")
        
        return repo, False
        
    except GithubException as e:
        logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
        raise GitHubError(f"Failed to create repository: {e.data.get('message', str(e))}")
    except Exception as e:
        logger.error(f"Unexpected error creating repository: {str(e)}")
        raise GitHubError(f"Unexpected error: {str(e)}")


def get_repository_secrets(repo_name: str) -> List[str]:
    """
    Get the list of existing secret names for a repository.
    
    Args:
        repo_name: Repository name
        
    Returns:
        List of secret names that already exist in the repository
        
    Raises:
        GitHubError: If there's an error getting repository secrets
    """
    client = get_github_client()
    
    try:
        repo = client.get_user().get_repo(repo_name)
        # Get all secrets (returns a generator of secret names)
        secrets = repo.get_secrets()
        # Extract secret names and return as a list
        return [secret.name for secret in secrets]
    except GithubException as e:
        logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
        raise GitHubError(f"Failed to get repository secrets: {e.data.get('message', str(e))}")
    except Exception as e:
        logger.error(f"Unexpected error getting repository secrets: {str(e)}")
        raise GitHubError(f"Unexpected error getting repository secrets: {str(e)}")


def set_repository_secret(repo_name: str, secret_name: str, secret_value: str) -> None:
    """
    Set a secret in a GitHub repository.
    
    Args:
        repo_name: Repository name
        secret_name: Secret name
        secret_value: Secret value
        
    Raises:
        GitHubError: If setting secret fails
    """
    client = get_github_client()
    username = Config.get_github_credentials().get("username")
    
    if not username:
        logger.error("GitHub username not found in configuration")
        raise GitHubError("GitHub username is required for repository operations")
    
    try:
        repo = client.get_user().get_repo(repo_name)
        repo.create_secret(secret_name, secret_value)
        logger.info(f"Set secret {secret_name} in repository {repo_name}")
    except GithubException as e:
        logger.error(f"GitHub API error: {str(e)}")
        raise GitHubError(f"Failed to set repository secret: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise GitHubError(f"Unexpected error: {str(e)}")


def _get_dynamic_database_url(repo_name: str) -> Optional[str]:
    """
    Get the DATABASE_URL from the database info for the repository.
    
    Args:
        repo_name: Repository name
        
    Returns:
        DATABASE_URL or None if not available
    """
    try:
        from infra.config import Config
        
        # Get database info from configuration
        database_info = Config.get_database_info(repo_name)
        
        if database_info and "database_url" in database_info:
            return database_info["database_url"]
    except Exception as e:
        logger.warning(f"Could not get DATABASE_URL from database info: {str(e)}")
    
    return None


def generate_dynamic_secrets(repo_name: str) -> Dict[str, str]:
    """
    Generate dynamic secrets for a GitHub repository.
    
    Args:
        repo_name: Repository name
        
    Returns:
        Dictionary of secret name to value
    """
    secrets = {}
    
    # Add DATABASE_URL from database info
    database_url = _get_dynamic_database_url(repo_name)
    if database_url:
        secrets["DATABASE_URL"] = database_url
    
    # Add other dynamic secrets as needed
    
    return secrets


def setup_cicd(
    repo_name: str, 
    variables: Optional[Dict[str, str]] = None,
    secrets: Optional[Dict[str, str]] = None,
    required_secret_names: Optional[List[str]] = None
) -> None:
    """
    Set up CI/CD variables and secrets for a GitHub repository.
    
    Args:
        repo_name: Repository name
        variables: Dictionary of CI/CD variables to set
        secrets: Dictionary of CI/CD secrets to set
        required_secret_names: List of secret names that should be set from Config
        
    Raises:
        GitHubError: If setting up CI/CD fails
    """
    client = get_github_client()
    user = Config.get_github_credentials()["username"]
    
    try:
        logger.info(f"Setting up CI/CD for repository: {repo_name}")
        
        # Get the repository
        repo = client.get_user().get_repo(repo_name)
        
        # Generate dynamic secrets that may not be in .env
        dynamic_secrets = generate_dynamic_secrets(repo_name)
        
        # Get existing secrets to avoid recreating them
        try:
            existing_secrets = get_repository_secrets(repo_name)
            logger.info(f"Found {len(existing_secrets)} existing secrets in repository")
        except Exception as e:
            logger.warning(f"Could not get existing secrets: {str(e)}. Will attempt to create all required secrets.")
            existing_secrets = []
        
        # Set up variables (GitHub Actions variables)
        if variables:
            for key, value in variables.items():
                # Note: GitHub API doesn't directly support variables via PyGithub
                # This would typically require additional API calls or GitHub CLI
                logger.info(f"Setting variable: {key}")
                # Example placeholder for when GitHub API supports this directly
                
        # Set up secrets provided in the secrets dict
        if secrets:
            for key, value in secrets.items():
                # Skip if secret already exists
                if key in existing_secrets:
                    logger.info(f"Secret already exists: {key} (skipping)")
                    continue
                    
                logger.info(f"Setting secret: {key}")
                repo.create_secret(key, value)
        
        # Set up required secrets from Config, fallback to dynamic generation if not found
        if required_secret_names:
            for secret_name in required_secret_names:
                # Skip if secret already exists
                if secret_name in existing_secrets:
                    logger.info(f"Required secret already exists: {secret_name} (skipping)")
                    continue
                    
                # Try to get the secret value from config
                try:
                    secret_value = Config.get(secret_name, default=None)
                    if secret_value:
                        logger.info(f"Setting required secret from config: {secret_name}")
                        repo.create_secret(secret_name, secret_value)
                    elif secret_name in dynamic_secrets:
                        # If not found in config but can be generated dynamically
                        logger.info(f"Setting dynamically generated secret: {secret_name}")
                        repo.create_secret(secret_name, dynamic_secrets[secret_name])
                    else:
                        logger.warning(f"Required secret not found in config and cannot be generated: {secret_name}")
                except Exception as e:
                    if secret_name in dynamic_secrets:
                        # If error occurred but can be generated dynamically
                        logger.info(f"Setting dynamically generated secret after error: {secret_name}")
                        repo.create_secret(secret_name, dynamic_secrets[secret_name])
                    else:
                        logger.warning(f"Error setting required secret {secret_name}: {str(e)}")
                
        logger.info(f"CI/CD setup completed for {repo_name}")
        
    except GithubException as e:
        logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
        raise GitHubError(f"Failed to set up CI/CD: {e.data.get('message', str(e))}")
    except Exception as e:
        logger.error(f"Unexpected error setting up CI/CD: {str(e)}")
        raise GitHubError(f"Unexpected error setting up CI/CD: {str(e)}")


def list_repositories(include_private: bool = True) -> List[str]:
    """
    List all repositories accessible to the authenticated user.
    
    Args:
        include_private: Whether to include private repositories
        
    Returns:
        List[str]: List of repository names
        
    Raises:
        GitHubError: If listing repositories fails
    """
    client = get_github_client()
    
    try:
        logger.info("Listing repositories")
        
        repos = []
        for repo in client.get_user().get_repos():
            if include_private or not repo.private:
                repos.append(repo.name)
                
        return repos
        
    except GithubException as e:
        logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
        raise GitHubError(f"Failed to list repositories: {e.data.get('message', str(e))}")
    except Exception as e:
        logger.error(f"Unexpected error listing repositories: {str(e)}")
        raise GitHubError(f"Unexpected error listing repositories: {str(e)}") 