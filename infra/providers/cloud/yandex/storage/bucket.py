import logging
import subprocess
import json
import tempfile
import os
import atexit

from infra.project_setup.types import ProjectSetupContext
from infra.providers.cloud.yandex.db.postgres import get_yc_configuration

logger = logging.getLogger(__name__)

def create_bucket(ctx: 'ProjectSetupContext', bucket_name: str, public_read: bool = False) -> bool:
    """
    Creates a bucket in Yandex Cloud and optionally configures it for website hosting.

    Args:
        ctx: The project setup context.
        bucket_name: The name of the bucket to create.
        public_read: If True, bucket will be public for read (default: False).

    Returns:
        bool: True if bucket creation and optional configuration was successful, False otherwise.
    """
    logger.info(f"Creating Yandex Cloud bucket: {bucket_name} (public_read={public_read})")

    # Get Yandex Cloud configuration with folder ID
    try:
        yc_config = get_yc_configuration()
        folder_id = yc_config.get("YC_FOLDER_ID")

        # Setup environment for yc command
        env = os.environ.copy()
        temp_file = None
        success = False

        try:
            # Create temporary file to store the JSON credentials
            temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
            temp_file.write(yc_config["YC_SA_JSON_CREDENTIALS"])
            temp_file.flush()
            temp_file.close()

            # Set the path to our temporary JSON file
            logger.debug(f"Using service account JSON credentials from temporary file: {temp_file.name}")
            env["YC_SERVICE_ACCOUNT_KEY_FILE"] = temp_file.name

            # Set cloud and folder IDs
            env["YC_CLOUD_ID"] = yc_config["YC_CLOUD_ID"]
            env["YC_FOLDER_ID"] = folder_id

            # --- Step 1: Create bucket command ---
            create_bucket_cmd = [
                "yc", "storage", "bucket", "create",
                bucket_name,
                "--max-size", "1073741824",
                "--folder-id", folder_id
            ]
            if public_read:
                create_bucket_cmd.append("--public-read")

            logger.debug(f"Executing create command: {' '.join(create_bucket_cmd)}")
            result_create = subprocess.run(
                create_bucket_cmd,
                env=env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result_create.returncode != 0:
                stderr_msg = result_create.stderr.strip() if result_create.stderr else "No error output"
                stdout_msg = result_create.stdout.strip() if result_create.stdout else "No standard output"
                logger.error(f"Bucket creation command failed with exit code {result_create.returncode}")
                logger.error(f"stderr: {stderr_msg}")
                logger.error(f"stdout: {stdout_msg}")
                return False # Exit if creation failed
            else:
                logger.info(f"Bucket '{bucket_name}' created successfully in folder: {folder_id}")
                if result_create.stdout:
                    logger.debug(f"Create command stdout:\n{result_create.stdout.strip()}")
                success = True # Mark creation as successful

            # --- Step 2: Configure website hosting if requested ---
            if success and public_read:
                logger.info(f"Configuring bucket '{bucket_name}' for website hosting...")
                # Construct the JSON string for website settings
                website_settings_json = '{"index": "index.html", "error": "error.html"}'

                update_bucket_cmd = [
                    "yc", "storage", "bucket", "update",
                    "--name", bucket_name,
                    "--website-settings", website_settings_json # Use the correct flag and JSON
                ]
                logger.debug(f"Executing update command: {' '.join(update_bucket_cmd)}")
                result_update = subprocess.run(
                    update_bucket_cmd,
                    env=env,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if result_update.returncode != 0:
                    stderr_msg = result_update.stderr.strip() if result_update.stderr else "No error output"
                    stdout_msg = result_update.stdout.strip() if result_update.stdout else "No standard output"
                    logger.error(f"Bucket website configuration command failed with exit code {result_update.returncode}")
                    logger.error(f"stderr: {stderr_msg}")
                    logger.error(f"stdout: {stdout_msg}")
                    logger.warning(f"Website configuration failed for bucket '{bucket_name}', but bucket was created.")
                else:
                    logger.info(f"Bucket '{bucket_name}' configured successfully for website hosting.")
                    if result_update.stdout:
                         logger.debug(f"Update command stdout:\n{result_update.stdout.strip()}")

            return success # Return True if creation was successful (regardless of update status for now)

        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"Failed during bucket creation/configuration: {str(e)}")
        return False

def check_bucket_exists(bucket_name: str) -> bool:
    """
    Checks if a bucket already exists in Yandex Cloud.

    Args:
        bucket_name: The name of the bucket to check.

    Returns:
        bool: True if the bucket exists, False otherwise.
    """
    logger.info(f"Checking if Yandex Cloud bucket exists: {bucket_name}")

    try:
        # Get Yandex Cloud configuration
        yc_config = get_yc_configuration()

        # Setup environment for yc command
        env = os.environ.copy()
        temp_file = None

        try:
            # Create temporary file to store the JSON credentials
            temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
            temp_file.write(yc_config["YC_SA_JSON_CREDENTIALS"])
            temp_file.flush()
            temp_file.close()

            # Set the path to our temporary JSON file
            env["YC_SERVICE_ACCOUNT_KEY_FILE"] = temp_file.name

            # Set cloud and folder IDs
            env["YC_CLOUD_ID"] = yc_config["YC_CLOUD_ID"]
            env["YC_FOLDER_ID"] = yc_config["YC_FOLDER_ID"]

            # Check specific bucket command - this works better than listing all buckets
            check_specific_bucket_cmd = [
                "yc", "storage", "bucket", "get",
                bucket_name,
                "--format", "json"
            ]

            logger.debug(f"Executing direct bucket check command: {' '.join(check_specific_bucket_cmd)}")
            result = subprocess.run(
                check_specific_bucket_cmd,
                env=env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # If the command succeeded, the bucket exists
            if result.returncode == 0:
                logger.info(f"Bucket {bucket_name} exists (confirmed with direct check).")
                return True

            # If we get here, the direct check didn't work, try listing all buckets
            logger.debug(f"Direct bucket check failed, trying bucket list instead.")

            # List buckets command as fallback
            list_buckets_cmd = [
                "yc", "storage", "bucket", "list",
                "--format", "json"
            ]

            logger.debug(f"Executing fallback list buckets command: {' '.join(list_buckets_cmd)}")
            result = subprocess.run(
                list_buckets_cmd,
                env=env,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                stderr_msg = result.stderr.strip() if result.stderr else "No error output"
                stdout_msg = result.stdout.strip() if result.stdout else "No standard output"
                logger.error(f"Bucket list command failed with exit code {result.returncode}")
                logger.error(f"stderr: {stderr_msg}")
                logger.error(f"stdout: {stdout_msg}")
                return False

            # Parse the JSON response and check for bucket
            if not result.stdout.strip():
                logger.warning("Empty response from bucket list command")
                return False

            try:
                buckets = json.loads(result.stdout)
                logger.debug(f"Found {len(buckets)} buckets in the listing")

                # Log all bucket names for debugging
                bucket_names = [b.get('name') for b in buckets if 'name' in b]
                logger.debug(f"Bucket names in listing: {bucket_names}")

                for bucket in buckets:
                    if bucket.get('name') == bucket_name:
                        logger.info(f"Bucket {bucket_name} exists (found in bucket list).")
                        return True

                logger.info(f"Bucket {bucket_name} not found in bucket list.")
                return False
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse bucket list response as JSON: {e}")
                logger.error(f"Response content: {result.stdout}")
                return False

        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"Error checking bucket existence: {str(e)}")
        return False