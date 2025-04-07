"""
GitHub API integration module.
"""

import logging
import os
from typing import Dict, List, Optional, TYPE_CHECKING

from github import Github, GithubException, Repository

from infra.config import Config

# Use TYPE_CHECKING to avoid circular import errors
if TYPE_CHECKING:
    from infra.project_setup.types import ProjectSetupContext

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


def setup_cicd(
    repo_name: str,
    ctx: 'ProjectSetupContext', # Pass the context object
    variables: Optional[Dict[str, str]] = None,
    secrets: Optional[Dict[str, str]] = None,
    required_secret_names: Optional[List[str]] = None
) -> None:
    """
    Set up CI/CD variables and secrets for a GitHub repository using context.

    Args:
        repo_name: Repository name
        ctx: The project setup context containing necessary info (like db_info).
        variables: Dictionary of CI/CD variables to set
        secrets: Dictionary of CI/CD secrets to set (explicitly provided).
        required_secret_names: List of secret names that should be set from Config.

    Raises:
        GitHubError: If setting up CI/CD fails
    """
    client = get_github_client()
    # username retrieval remains the same, assuming it's in config
    username = Config.get_github_credentials().get("username")
    if not username:
        logger.error("GitHub username not found in configuration")
        raise GitHubError("GitHub username is required for repository operations")

    try:
        logger.info(f"Setting up CI/CD for repository: {repo_name}")

        # Get the repository
        repo = client.get_user().get_repo(repo_name)

        # Get existing secrets to avoid recreating them
        try:
            existing_secrets = get_repository_secrets(repo_name)
            logger.info(f"Found {len(existing_secrets)} existing secrets in repository")
        except Exception as e:
            logger.warning(f"Could not get existing secrets: {str(e)}. Will attempt to create all required secrets.")
            existing_secrets = []

        # Combine explicitly passed secrets with secrets derived from context (like DB URL)
        all_secrets_to_set = {} if secrets is None else secrets.copy()

        # Add DATABASE_URL from context's github_secrets if available
        db_url = ctx.github_secrets.get('DATABASE_URL')
        if db_url:
            # Add DATABASE_URL to the secrets to be set, potentially overwriting
            # an explicitly passed value if it differs (context takes precedence?)
            # Let's log if it was passed explicitly and differs.
            if "DATABASE_URL" in all_secrets_to_set and all_secrets_to_set["DATABASE_URL"] != db_url:
                logger.warning(f"DATABASE_URL provided explicitly differs from context github_secrets. Using context value for repo {repo_name}.")
            elif "DATABASE_URL" not in all_secrets_to_set:
                logger.info(f"Adding DATABASE_URL from context github_secrets for {repo_name}")

            all_secrets_to_set["DATABASE_URL"] = db_url
        else:
            logger.debug(f"No DATABASE_URL found in context github_secrets for {repo_name}.")

        # Set up variables (GitHub Actions variables)
        if variables:
            for key, value in variables.items():
                # Note: GitHub API doesn't directly support variables via PyGithub
                logger.info(f"Setting variable: {key}")
                # Placeholder

        # Set up secrets from the combined dictionary (explicit + context-derived)
        if all_secrets_to_set:
            for key, value in all_secrets_to_set.items():
                if key in existing_secrets:
                    # Check if the existing secret might need updating?
                    # For now, we skip if it exists, assuming it's correct.
                    # A more complex logic could compare values or force update.
                    logger.info(f"Secret already exists: {key} (skipping)")
                    continue

                logger.info(f"Setting secret: {key}")
                repo.create_secret(key, value)

        # Set up required secrets from Config (e.g., API keys)
        if required_secret_names:
            for secret_name in required_secret_names:
                # Skip if secret already exists (might have been set above if DATABASE_URL was required)
                if secret_name in existing_secrets or secret_name in all_secrets_to_set:
                    logger.info(f"Required secret already exists or was just set: {secret_name} (skipping)")
                    continue

                # Try to get the secret value from config
                try:
                    secret_value = Config.get(secret_name, default=None)
                    if secret_value:
                        logger.info(f"Setting required secret from config: {secret_name}")
                        repo.create_secret(secret_name, secret_value)
                    else:
                        # If it wasn't in config and wasn't derivable from context (like DB URL was)
                        logger.warning(f"Required secret not found in config: {secret_name}")
                except Exception as e:
                     logger.warning(f"Error retrieving required secret {secret_name} from config: {str(e)}")


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