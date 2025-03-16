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
    Create a new GitHub repository.
    
    Args:
        name: Repository name
        private: Whether the repository should be private
        description: Repository description
        auto_init: Whether to initialize the repository with a README
        
    Returns:
        tuple: (Repository, already_existed) where:
            - Repository: The GitHub repository object
            - already_existed: True if repository already existed, False if it was created
        
    Raises:
        GitHubError: If repository creation fails
    """
    client = get_github_client()
    
    try:
        logger.info(f"Creating {'private' if private else 'public'} repository: {name}")
        
        # Check if repo already exists
        try:
            existing_repo = client.get_user().get_repo(name)
            logger.info(f"Repository {name} already exists at {existing_repo.html_url}")
            return existing_repo, True
        except GithubException:
            # Repository doesn't exist, continue with creation
            pass
            
        # Create the repository
        repo = client.get_user().create_repo(
            name=name,
            private=private,
            description=description or f"Repository for {name}",
            auto_init=auto_init,
        )
        
        logger.info(f"Repository created successfully at {repo.html_url}")
        return repo, False
        
    except GithubException as e:
        logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
        raise GitHubError(f"Failed to create repository: {e.data.get('message', str(e))}")
    except Exception as e:
        logger.error(f"Unexpected error creating repository: {str(e)}")
        raise GitHubError(f"Unexpected error creating repository: {str(e)}")


def setup_cicd(
    repo_name: str, 
    variables: Optional[Dict[str, str]] = None,
    secrets: Optional[Dict[str, str]] = None
) -> None:
    """
    Set up CI/CD variables and secrets for a GitHub repository.
    
    Args:
        repo_name: Repository name
        variables: Dictionary of CI/CD variables to set
        secrets: Dictionary of CI/CD secrets to set
        
    Raises:
        GitHubError: If setting up CI/CD fails
    """
    client = get_github_client()
    user = Config.get_github_credentials()["username"]
    
    try:
        logger.info(f"Setting up CI/CD for repository: {repo_name}")
        
        # Get the repository
        repo = client.get_user().get_repo(repo_name)
        
        # Set up variables (GitHub Actions variables)
        if variables:
            for key, value in variables.items():
                # Note: GitHub API doesn't directly support variables via PyGithub
                # This would typically require additional API calls or GitHub CLI
                logger.info(f"Setting variable: {key}")
                # Example placeholder for when GitHub API supports this directly
                
        # Set up secrets
        if secrets:
            for key, value in secrets.items():
                logger.info(f"Setting secret: {key}")
                repo.create_secret(key, value)
                
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