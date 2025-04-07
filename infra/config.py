"""
Configuration module for loading and accessing environment variables and settings.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
import json

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Get the absolute path to the base directory of the project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Загрузка .env выполняется в методе _load_config при первом обращении к конфигурации

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class Config:
    """
    Configuration manager for the Infra toolkit.
    Handles environment variables and provides access to credentials.
    """

    _config_data = None

    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        """
        Load configuration from .env file or environment variables.

        Returns:
            Dict with configuration parameters
        """
        if cls._config_data is None:

            # Получаем путь к .env файлу из переменной окружения или используем значение по умолчанию
            env_file = os.environ.get("INFRA_ENV_FILE", ".env")

            # Если путь не абсолютный, считаем его относительно корня проекта
            if not os.path.isabs(env_file):
                env_file = os.path.join(BASE_DIR, env_file)

            logger.debug(f"Loading configuration from {env_file}")

            # Load from .env file
            if os.path.exists(env_file):
                logger.debug(f"Loading from .env file: {env_file}")
                # Use existing load_dotenv for global environment variables
                load_dotenv(env_file)
            else:
                logger.warning(f".env file not found at {env_file}, using environment variables only")

            # Get all environment variables
            cls._config_data = dict(os.environ)

        return cls._config_data

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        config = cls._load_config()
        return config.get(key, default)

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dict with all configuration parameters
        """
        return cls._load_config()

    @classmethod
    def get_github_credentials(cls) -> Dict[str, str]:
        """
        Get GitHub credentials.

        Returns:
            Dict with GitHub credentials

        Raises:
            ConfigError: If GitHub credentials are not configured
        """
        config = cls._load_config()

        # Check for GitHub token
        token = config.get("GITHUB_API_TOKEN")
        username = config.get("GITHUB_USERNAME")

        if not token:
            logger.error("GitHub API token not found in configuration")
            raise ConfigError("GitHub API token is required. Set GITHUB_API_TOKEN in .env file.")

        if not username:
            logger.warning("GitHub username not found in configuration")

        return {
            "token": token,
            "username": username
        }

    @classmethod
    def get_yandex_cloud_credentials(cls) -> Dict[str, str]:
        """
        Get Yandex Cloud credentials.

        Returns:
            Dict with Yandex Cloud credentials

        Raises:
            ConfigError: If Yandex Cloud credentials are not configured
        """
        config = cls._load_config()

        # Check for Yandex Cloud credentials
        oauth_token = config.get("YC_OAUTH_TOKEN")
        cloud_id = config.get("YC_CLOUD_ID")
        folder_id = config.get("YC_FOLDER_ID")

        if not oauth_token:
            logger.error("Yandex Cloud OAuth token not found in configuration")
            raise ConfigError("Yandex Cloud OAuth token is required. Set YC_OAUTH_TOKEN in .env file.")

        if not cloud_id:
            logger.warning("Yandex Cloud ID not found in configuration")

        if not folder_id:
            logger.warning("Yandex Cloud folder ID not found in configuration")

        return {
            "oauth_token": oauth_token,
            "cloud_id": cloud_id,
            "folder_id": folder_id
        }

    @classmethod
    def get_db_credentials(cls) -> Dict[str, str]:
        """
        Get database credentials.

        Returns:
            Dict with database credentials

        Raises:
            ConfigError: If database credentials are not configured
        """
        config = cls._load_config()

        # Check for database credentials
        admin_username = config.get("DB_ADMIN_USERNAME")
        admin_password = config.get("DB_ADMIN_PASSWORD")

        if not admin_username or not admin_password:
            logger.error("Database admin credentials not found in configuration")
            raise ConfigError("Database admin credentials are required. Set DB_ADMIN_USERNAME and DB_ADMIN_PASSWORD in .env file.")

        return {
            "username": admin_username,
            "password": admin_password
        }

    @classmethod
    def get_ssh_settings(cls) -> Dict[str, str]:
        """Get SSH settings."""
        return {
            "private_key_path": cls.get("SSH_PRIVATE_KEY_PATH", "~/.ssh/id_rsa"),
            "public_key_path": cls.get("SSH_PUBLIC_KEY_PATH", "~/.ssh/id_rsa.pub"),
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
    def get_projects_root_dir(cls) -> Path:
        """
        Get the projects root directory.

        Returns:
            Path to the projects root directory
        """
        config = cls._load_config()

        # Get projects root directory with fallback to home/projects
        projects_dir = config.get("PROJECTS_ROOT_DIR", os.path.expanduser("~/projects"))

        # Expand user home directory if present
        if "~" in projects_dir:
            projects_dir = os.path.expanduser(projects_dir)

        # Create directory if it doesn't exist
        os.makedirs(projects_dir, exist_ok=True)

        return Path(projects_dir)