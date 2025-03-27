"""
Local environment file handling module.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class EnvFileError(Exception):
    """Exception raised for .env file related errors."""
    pass


class ProjectEnv:
    """Class for managing project environment variables in .env files."""

    def __init__(self, env_file_path: Path):
        """
        Initialize with path to the .env file.

        Args:
            env_file_path: Path to the .env file
        """
        self.env_file_path = env_file_path

    def read(self) -> Dict[str, str]:
        """
        Read and parse the .env file into a dictionary.

        Returns:
            Dictionary of environment variables

        Raises:
            EnvFileError: If the file cannot be read
        """
        if not self.env_file_path.exists():
            logger.debug(f".env file does not exist: {self.env_file_path}")
            return {}

        try:
            env_vars = {}
            content = self.env_file_path.read_text()

            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

            logger.debug(f"Read {len(env_vars)} variables from {self.env_file_path}")
            return env_vars

        except Exception as e:
            logger.error(f"Error reading .env file {self.env_file_path}: {str(e)}")
            raise EnvFileError(f"Failed to read .env file: {str(e)}")

    def has_var(self, var_name: str) -> bool:
        """
        Check if a specific environment variable exists in the .env file.

        Args:
            var_name: Name of the environment variable to check

        Returns:
            True if the variable exists, False otherwise
        """
        if not self.env_file_path.exists():
            return False

        try:
            env_vars = self.read()
            return var_name in env_vars
        except EnvFileError:
            return False

    def get_var(self, var_name: str) -> Optional[str]:
        """
        Get the value of a specific environment variable from the .env file.

        Args:
            var_name: Name of the environment variable to get

        Returns:
            The value of the variable or None if it doesn't exist
        """
        if not self.env_file_path.exists():
            return None

        try:
            env_vars = self.read()
            return env_vars.get(var_name)
        except EnvFileError:
            return None

    def set_var(self, var_name: str, var_value: str) -> bool:
        """
        Set or update an environment variable in the .env file.

        Args:
            var_name: Name of the environment variable to set
            var_value: Value to set

        Returns:
            True if successful, False otherwise

        Raises:
            EnvFileError: If there's an error writing to the file
        """
        try:
            if self.env_file_path.exists():
                # Read existing .env file
                env_vars = self.read()

                # Update the variable
                env_vars[var_name] = var_value

                # Write back to the file
                self._write(env_vars)
            else:
                # Create new .env file with the variable
                self._write({var_name: var_value})

            logger.debug(f"Set environment variable {var_name} in {self.env_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error setting environment variable {var_name} in {self.env_file_path}: {str(e)}")
            raise EnvFileError(f"Failed to set environment variable: {str(e)}")

    def remove_var(self, var_name: str) -> bool:
        """
        Remove an environment variable from the .env file.

        Args:
            var_name: Name of the environment variable to remove

        Returns:
            True if the variable was removed, False if it didn't exist

        Raises:
            EnvFileError: If there's an error writing to the file
        """
        if not self.env_file_path.exists():
            return False

        try:
            # Read existing .env file
            env_vars = self.read()

            # Check if the variable exists
            if var_name not in env_vars:
                return False

            # Remove the variable
            del env_vars[var_name]

            # Write back to the file
            self._write(env_vars)

            logger.debug(f"Removed environment variable {var_name} from {self.env_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error removing environment variable {var_name} from {self.env_file_path}: {str(e)}")
            raise EnvFileError(f"Failed to remove environment variable: {str(e)}")

    def _write(self, env_vars: Dict[str, str]) -> None:
        """
        Write environment variables to the .env file.

        Args:
            env_vars: Dictionary of environment variables to write

        Raises:
            EnvFileError: If there's an error writing to the file
        """
        try:
            # Create parent directories if they don't exist
            self.env_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate .env file content
            lines = [f"{key}={value}" for key, value in env_vars.items()]
            content = "\n".join(lines) + "\n"

            # Write to file
            self.env_file_path.write_text(content)
            logger.debug(f"Wrote {len(env_vars)} variables to {self.env_file_path}")

        except Exception as e:
            logger.error(f"Error writing .env file {self.env_file_path}: {str(e)}")
            raise EnvFileError(f"Failed to write .env file: {str(e)}")


# Backward compatibility functions
def read_env_file(env_file_path: Path) -> Dict[str, str]:
    """Legacy function for backwards compatibility."""
    return ProjectEnv(env_file_path).read()

def has_env_var(env_file_path: Path, var_name: str) -> bool:
    """Legacy function for backwards compatibility."""
    return ProjectEnv(env_file_path).has_var(var_name)

def get_env_var(env_file_path: Path, var_name: str) -> Optional[str]:
    """Legacy function for backwards compatibility."""
    return ProjectEnv(env_file_path).get_var(var_name)

def set_env_var(env_file_path: Path, var_name: str, var_value: str) -> bool:
    """Legacy function for backwards compatibility."""
    return ProjectEnv(env_file_path).set_var(var_name, var_value)

def remove_env_var(env_file_path: Path, var_name: str) -> bool:
    """Legacy function for backwards compatibility."""
    return ProjectEnv(env_file_path).remove_var(var_name)


def get_project_env(project_name: str) -> ProjectEnv:
    """
    Get a ProjectEnv instance for a specific project.

    Args:
        project_name: Name of the project

    Returns:
        ProjectEnv instance for the project
    """
    from infra.config import Config

    projects_root = Config.get_projects_root_dir()
    project_dir = projects_root / project_name
    env_file = project_dir / ".env"

    return ProjectEnv(env_file)