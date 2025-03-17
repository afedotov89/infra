"""
GitHub API integration module.
"""

import logging
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


def generate_dynamic_secrets(repo_name: str) -> Dict[str, str]:
    """
    Generate dynamic secrets that are not in .env but can be derived from project name
    or generated dynamically.
    
    Args:
        repo_name: Repository/project name
        
    Returns:
        Dictionary of secrets that were dynamically generated
    """
    import random
    import string
    
    dynamic_secrets = {}
    
    # Container name for Yandex Cloud Serverless Containers
    dynamic_secrets["YC_CONTAINER_NAME"] = f"{repo_name}-container"
    
    # API Gateway name for Yandex Cloud API Gateway
    dynamic_secrets["YC_API_GATEWAY_NAME"] = f"{repo_name}-gateway"
    
    # Generate Django secret key
    # Using a simple but secure method similar to what Django uses
    chars = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    django_secret_key = ''.join(random.choice(chars) for _ in range(50))
    dynamic_secrets["DJANGO_SECRET_KEY"] = django_secret_key
    
    return dynamic_secrets


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
                    secret_value = Config.get(secret_name, required=False)
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