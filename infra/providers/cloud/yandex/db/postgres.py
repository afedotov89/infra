"""
Functions for managing PostgreSQL databases in Yandex Cloud.
"""

import logging
import subprocess
import os
import random
import string
import json
import tempfile
import atexit
from typing import Dict, Any, Tuple

from infra.config import Config

logger = logging.getLogger(__name__)


class YandexCloudDBError(Exception):
    """Exception raised for errors in Yandex Cloud database operations."""
    pass


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password.

    Args:
        length: Length of the password (default: 16)

    Returns:
        A secure random password string
    """
    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!#$%^&*()-_=+[]{}|;:,.<>?/"

    # Ensure at least one character from each set
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars)
    ]

    # Fill the rest of the password
    remaining_length = length - len(password)
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(random.choice(all_chars) for _ in range(remaining_length))

    # Shuffle the password characters
    random.shuffle(password)

    return ''.join(password)


def get_yc_configuration() -> Dict[str, str]:
    """
    Get Yandex Cloud configuration from environment.
    Authentication is done via service account JSON credentials.

    Returns:
        Dictionary with Yandex Cloud configuration

    Raises:
        YandexCloudDBError: If required configuration is missing
    """
    config = Config.get_all()

    # Check if service account JSON credentials are provided
    if not config.get("YC_SA_JSON_CREDENTIALS"):
        raise YandexCloudDBError("Missing required Yandex Cloud authentication. "
                               "Please provide YC_SA_JSON_CREDENTIALS (JSON text)")

    # Check for other required configuration
    required_keys = [
        "YC_CLOUD_ID",
        "YC_FOLDER_ID",
        "YC_POSTGRES_CLUSTER_ID"
    ]

    missing_keys = [key for key in required_keys if not config.get(key)]

    if missing_keys:
        raise YandexCloudDBError(f"Missing required Yandex Cloud configuration: {', '.join(missing_keys)}")

    result = {key: config.get(key) for key in required_keys}

    # Add authentication
    result["YC_SA_JSON_CREDENTIALS"] = config.get("YC_SA_JSON_CREDENTIALS")

    return result


def _create_database_and_user(db_name: str) -> Tuple[str, str, str]:
    """
    Create a database and user in Yandex Cloud PostgreSQL cluster using yc CLI.
    This operation is idempotent - if database or user already exist,
    they will not be modified (but password will be updated).

    Args:
        db_name: Name of the database and user to create

    Returns:
        Tuple containing (host, database_url, password)

    Raises:
        YandexCloudDBError: If database or user creation fails
    """
    logger.debug(f"Creating database and user {db_name} in Yandex Cloud PostgreSQL")

    # Get Yandex Cloud configuration
    yc_config = get_yc_configuration()

    # Get cluster host and info
    host, cluster_id = _get_cluster_host_and_id(yc_config)

    # Generate a secure password for the user
    password = generate_secure_password()

    # Setup environment for yc commands
    env = os.environ.copy()
    temp_file = None

    try:
        # Create temporary file to store the JSON credentials
        temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
        temp_file.write(yc_config["YC_SA_JSON_CREDENTIALS"])
        temp_file.flush()
        temp_file.close()

        # Register cleanup to ensure the temporary file is removed
        atexit.register(lambda: os.unlink(temp_file.name) if os.path.exists(temp_file.name) else None)

        # Set environment variables for yc command
        env["YC_SERVICE_ACCOUNT_KEY_FILE"] = temp_file.name
        env["YC_CLOUD_ID"] = yc_config["YC_CLOUD_ID"]
        env["YC_FOLDER_ID"] = yc_config["YC_FOLDER_ID"]

        # Check if user exists
        logger.debug(f"Checking if user {db_name} exists")
        list_users_cmd = [
            "yc", "managed-postgresql", "user", "list",
            "--cluster-id", cluster_id,
            "--format", "json"
        ]

        users_output = subprocess.check_output(list_users_cmd, env=env, stderr=subprocess.PIPE)
        users = json.loads(users_output)

        user_exists = any(user["name"] == db_name for user in users)

        # Create or update user
        if user_exists:
            logger.info(f"User {db_name} already exists, updating password")
            update_user_cmd = [
                "yc", "managed-postgresql", "user", "update",
                db_name,
                "--cluster-id", cluster_id,
                "--password", password
            ]
            subprocess.check_call(update_user_cmd, env=env, stderr=subprocess.PIPE)
        else:
            logger.info(f"Creating new user {db_name}")
            create_user_cmd = [
                "yc", "managed-postgresql", "user", "create",
                db_name,
                "--cluster-id", cluster_id,
                "--password", password
            ]
            subprocess.check_call(create_user_cmd, env=env, stderr=subprocess.PIPE)

        # Check if database exists
        logger.debug(f"Checking if database {db_name} exists")
        list_dbs_cmd = [
            "yc", "managed-postgresql", "database", "list",
            "--cluster-id", cluster_id,
            "--format", "json"
        ]

        dbs_output = subprocess.check_output(list_dbs_cmd, env=env, stderr=subprocess.PIPE)
        databases = json.loads(dbs_output)

        db_exists = any(db["name"] == db_name for db in databases)

        # Create database if it doesn't exist
        if not db_exists:
            logger.info(f"Creating new database {db_name}")
            create_db_cmd = [
                "yc", "managed-postgresql", "database", "create",
                db_name,
                "--cluster-id", cluster_id,
                "--owner", db_name
            ]
            subprocess.check_call(create_db_cmd, env=env, stderr=subprocess.PIPE)
        else:
            logger.info(f"Database {db_name} already exists")

        # Generate DATABASE_URL for applications, ensuring SSL is required
        database_url = f"postgresql://{db_name}:{password}@{host}:6432/{db_name}?sslmode=require"

        logger.info(f"Successfully ensured database and user {db_name} in Yandex Cloud PostgreSQL")
        return host, database_url, password

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed during database and user operations: {str(e)}"
        if hasattr(e, 'stderr') and e.stderr:
            error_msg += f"\nError output: {e.stderr.decode('utf-8', errors='replace')}"
        logger.error(error_msg)
        raise YandexCloudDBError(error_msg)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise YandexCloudDBError(f"Unexpected error: {str(e)}")
    finally:
        # Ensure the temporary file is removed
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file.name}: {str(e)}")


def create_database(db_name: str, db_type: str = "postgres") -> Dict[str, Any]:
    """
    Create a database in Yandex Cloud.

    Args:
        db_name: Name of the database to create
        db_type: Type of database to create (only "postgres" is supported currently)

    Returns:
        Dictionary with database connection information

    Raises:
        YandexCloudDBError: If database creation fails or type is not supported
    """
    if db_type.lower() != "postgres":
        raise YandexCloudDBError(f"Unsupported database type: {db_type}. Only 'postgres' is supported.")

    host, database_url, password = _create_database_and_user(db_name)

    return {
        "name": db_name,
        "type": db_type,
        "host": host,
        "port": 6432,
        "username": db_name,
        "password": password,
        "database_url": database_url
    }


def delete_database(db_name: str, db_type: str = "postgres") -> bool:
    """
    Delete a database in Yandex Cloud using yc CLI.

    Args:
        db_name: Name of the database to delete
        db_type: Type of database to delete (only "postgres" is supported currently)

    Returns:
        True if database was deleted successfully, False otherwise

    Raises:
        YandexCloudDBError: If database deletion fails or type is not supported
    """
    if db_type.lower() != "postgres":
        raise YandexCloudDBError(f"Unsupported database type: {db_type}. Only 'postgres' is supported.")

    logger.debug(f"Deleting database {db_name} in Yandex Cloud PostgreSQL")

    # Get Yandex Cloud configuration
    yc_config = get_yc_configuration()

    # Get cluster ID
    _, cluster_id = _get_cluster_host_and_id(yc_config)

    # Setup environment for yc commands
    env = os.environ.copy()
    temp_file = None

    try:
        # Create temporary file to store the JSON credentials
        temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
        temp_file.write(yc_config["YC_SA_JSON_CREDENTIALS"])
        temp_file.flush()
        temp_file.close()

        # Register cleanup to ensure the temporary file is removed
        atexit.register(lambda: os.unlink(temp_file.name) if os.path.exists(temp_file.name) else None)

        # Set environment variables for yc command
        env["YC_SERVICE_ACCOUNT_KEY_FILE"] = temp_file.name
        env["YC_CLOUD_ID"] = yc_config["YC_CLOUD_ID"]
        env["YC_FOLDER_ID"] = yc_config["YC_FOLDER_ID"]

        # Check if database exists
        logger.debug(f"Checking if database {db_name} exists")
        list_dbs_cmd = [
            "yc", "managed-postgresql", "database", "list",
            "--cluster-id", cluster_id,
            "--format", "json"
        ]

        dbs_output = subprocess.check_output(list_dbs_cmd, env=env, stderr=subprocess.PIPE)
        databases = json.loads(dbs_output)

        db_exists = any(db["name"] == db_name for db in databases)

        if not db_exists:
            logger.info(f"Database {db_name} does not exist, nothing to delete")
            return True

        # Delete database
        logger.info(f"Deleting database {db_name}")
        delete_db_cmd = [
            "yc", "managed-postgresql", "database", "delete",
            db_name,
            "--cluster-id", cluster_id
        ]
        subprocess.check_call(delete_db_cmd, env=env, stderr=subprocess.PIPE)

        # Check if user exists
        logger.debug(f"Checking if user {db_name} exists")
        list_users_cmd = [
            "yc", "managed-postgresql", "user", "list",
            "--cluster-id", cluster_id,
            "--format", "json"
        ]

        users_output = subprocess.check_output(list_users_cmd, env=env, stderr=subprocess.PIPE)
        users = json.loads(users_output)

        user_exists = any(user["name"] == db_name for user in users)

        if user_exists:
            # Delete user
            logger.info(f"Deleting user {db_name}")
            delete_user_cmd = [
                "yc", "managed-postgresql", "user", "delete",
                db_name,
                "--cluster-id", cluster_id
            ]
            subprocess.check_call(delete_user_cmd, env=env, stderr=subprocess.PIPE)

        logger.info(f"Successfully deleted database and user {db_name}")
        return True

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed during database deletion: {str(e)}"
        if hasattr(e, 'stderr') and e.stderr:
            error_msg += f"\nError output: {e.stderr.decode('utf-8', errors='replace')}"
        logger.error(error_msg)
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database deletion: {str(e)}")
        return False
    finally:
        # Ensure the temporary file is removed
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file.name}: {str(e)}")


def _get_cluster_host_and_id(yc_config: Dict[str, str]) -> Tuple[str, str]:
    """
    Get the host name and ID for the PostgreSQL cluster.

    Args:
        yc_config: Yandex Cloud configuration

    Returns:
        Tuple containing (host, cluster_id)

    Raises:
        YandexCloudDBError: If getting cluster info fails
    """
    try:
        logger.debug("Getting PostgreSQL cluster information")
        cluster_id = yc_config["YC_POSTGRES_CLUSTER_ID"]

        env = os.environ.copy()
        temp_file = None

        try:
            # Create temporary file to store the JSON credentials
            temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
            temp_file.write(yc_config["YC_SA_JSON_CREDENTIALS"])
            temp_file.flush()
            temp_file.close()

            # Register cleanup to ensure the temporary file is removed
            atexit.register(lambda: os.unlink(temp_file.name) if os.path.exists(temp_file.name) else None)

            # Set the path to our temporary JSON file
            logger.debug(f"Using service account JSON credentials from temporary file: {temp_file.name}")
            env["YC_SERVICE_ACCOUNT_KEY_FILE"] = temp_file.name

            env["YC_CLOUD_ID"] = yc_config["YC_CLOUD_ID"]
            env["YC_FOLDER_ID"] = yc_config["YC_FOLDER_ID"]

            # Get hosts list to retrieve the master host name
            hosts_cmd = [
                "yc", "managed-postgresql", "hosts", "list",
                "--cluster-id", cluster_id,
                "--format", "json"
            ]

            logger.debug(f"Executing command: {' '.join(hosts_cmd)}")
            hosts_output = subprocess.check_output(hosts_cmd, env=env, stderr=subprocess.PIPE)

            hosts_data = json.loads(hosts_output)

            # Extract host name from the hosts list (prefer MASTER)
            host = None
            for host_info in hosts_data:
                if "role" in host_info and host_info["role"] == "MASTER":
                    host = host_info["name"]
                    logger.info(f"Found MASTER host: {host}")
                    break

            # If no master found or no role field, try the first host if available
            if not host and hosts_data:
                host = hosts_data[0]["name"]
                logger.info(f"Using first host from list: {host}")

            # Fallback to internal FQDN if no host could be extracted
            if not host:
                host = f"{cluster_id}.postgresql.yandex.internal"
                logger.warning(f"Could not extract host from hosts list, using fallback internal FQDN: {host}")
            else:
                # Ensure the extracted host is used (redundant log removed for clarity)
                pass

            return host, cluster_id

        finally:
            # Ensure the temporary file is removed
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_file.name}: {str(e)}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get PostgreSQL cluster info: {str(e)}")
        # Log more details when command fails
        if hasattr(e, 'output') and e.output:
            logger.error(f"Command output: {e.output.decode('utf-8', errors='replace')}")
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"Error output: {e.stderr.decode('utf-8', errors='replace')}")
        raise YandexCloudDBError(f"Failed to get PostgreSQL cluster info: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error getting cluster info: {str(e)}")
        raise YandexCloudDBError(f"Unexpected error: {str(e)}")


def check_database_exists(db_name: str) -> bool:
    """
    Check if a database exists in the Yandex Cloud PostgreSQL cluster.

    Args:
        db_name: Name of the database to check.

    Returns:
        True if the database exists, False otherwise.

    Raises:
        YandexCloudDBError: If checking fails due to configuration or command errors.
    """
    logger.debug(f"Checking if database {db_name} exists in Yandex Cloud PostgreSQL")

    # Get Yandex Cloud configuration and cluster ID
    try:
        yc_config = get_yc_configuration()
        _, cluster_id = _get_cluster_host_and_id(yc_config) # Re-use existing helper
    except YandexCloudDBError as e:
        logger.error(f"Failed to get YC configuration or cluster info for existence check: {e}")
        raise # Propagate config errors

    # Setup environment for yc commands using temporary file for credentials
    env = os.environ.copy()
    temp_file = None
    try:
        # Create temporary file for credentials
        temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
        temp_file.write(yc_config["YC_SA_JSON_CREDENTIALS"])
        temp_file.flush()
        temp_file.close()
        atexit.register(lambda: os.unlink(temp_file.name) if os.path.exists(temp_file.name) else None)

        env["YC_SERVICE_ACCOUNT_KEY_FILE"] = temp_file.name
        env["YC_CLOUD_ID"] = yc_config["YC_CLOUD_ID"]
        env["YC_FOLDER_ID"] = yc_config["YC_FOLDER_ID"]

        # Execute yc command to list databases
        list_dbs_cmd = [
            "yc", "managed-postgresql", "database", "list",
            "--cluster-id", cluster_id,
            "--format", "json"
        ]
        logger.debug(f"Executing command: {' '.join(list_dbs_cmd)}")
        dbs_output = subprocess.check_output(list_dbs_cmd, env=env, stderr=subprocess.PIPE)
        databases = json.loads(dbs_output)

        # Check if the database name is in the list
        db_exists = any(db.get("name") == db_name for db in databases)
        logger.debug(f"Database '{db_name}' exists: {db_exists}")
        return db_exists

    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to list databases for cluster {cluster_id}: {e}"
        if hasattr(e, 'stderr') and e.stderr:
            error_msg += f"\nError output: {e.stderr.decode('utf-8', errors='replace')}"
        logger.error(error_msg)
        # Raise for clarity, indicating the check could not be completed.
        raise YandexCloudDBError(error_msg)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse database list JSON for cluster {cluster_id}: {e}"
        logger.error(error_msg)
        raise YandexCloudDBError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error checking database existence: {str(e)}"
        logger.error(error_msg)
        raise YandexCloudDBError(error_msg)
    finally:
        # Ensure the temporary file is removed
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file.name}: {str(e)}")