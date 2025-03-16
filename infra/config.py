"""
Configuration module for loading and accessing environment variables and settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class Config:
    """
    Configuration manager for the Infra toolkit.
    Handles environment variables and provides access to credentials.
    """
    
    @staticmethod
    def get(key: str, default: Optional[Any] = None, required: bool = False) -> Any:
        """
        Get a configuration value from environment variables.
        
        Args:
            key: The configuration key to get
            default: Default value if key is not found
            required: Whether the key is required (raises error if not found)
            
        Returns:
            The configuration value
            
        Raises:
            ConfigError: If the key is required but not found
        """
        value = os.environ.get(key, default)
        if required and value is None:
            raise ConfigError(f"Required configuration key '{key}' not found")
        return value
    
    @classmethod
    def get_github_credentials(cls) -> Dict[str, str]:
        """Get GitHub API credentials."""
        return {
            "token": cls.get("GITHUB_API_TOKEN", required=True),
            "username": cls.get("GITHUB_USERNAME", required=True),
        }
    
    @classmethod
    def get_yandex_cloud_credentials(cls) -> Dict[str, str]:
        """Get Yandex Cloud credentials."""
        return {
            "oauth_token": cls.get("YC_OAUTH_TOKEN", required=True),
            "cloud_id": cls.get("YC_CLOUD_ID", required=True),
            "folder_id": cls.get("YC_FOLDER_ID", required=True),
            "service_account_id": cls.get("YC_SERVICE_ACCOUNT_ID"),
            "service_account_key_file": cls.get("YC_SERVICE_ACCOUNT_KEY_FILE"),
        }
    
    @classmethod
    def get_db_credentials(cls) -> Dict[str, str]:
        """Get database admin credentials."""
        return {
            "username": cls.get("DB_ADMIN_USERNAME", required=True),
            "password": cls.get("DB_ADMIN_PASSWORD", required=True),
        }
    
    @classmethod
    def get_ssh_settings(cls) -> Dict[str, str]:
        """Get SSH settings."""
        return {
            "private_key_path": cls.get("SSH_PRIVATE_KEY_PATH", "~/.ssh/id_rsa"),
            "public_key_path": cls.get("SSH_PUBLIC_KEY_PATH", "~/.ssh/id_rsa.pub"),
        }
    
    @classmethod
    def get_template_urls(cls) -> Dict[str, str]:
        """Get template repository URLs."""
        return {
            "django": cls.get("TEMPLATE_REPO_URL_DJANGO", ""),
            "react": cls.get("TEMPLATE_REPO_URL_REACT", ""),
        }
    
    @classmethod
    def get_openai_settings(cls) -> Dict[str, str]:
        """Get OpenAI API settings."""
        return {
            "api_key": cls.get("OPENAI_API_KEY", ""),
        }
    
    @classmethod
    def get_gui_settings(cls) -> Dict[str, str]:
        """Get GUI settings."""
        return {
            "theme": cls.get("GUI_THEME", "light"),
        }
    
    @classmethod
    def get_projects_root_dir(cls) -> str:
        """Get the root directory where all projects are stored."""
        projects_dir = cls.get("PROJECTS_ROOT_DIR", required=True)
        return projects_dir 