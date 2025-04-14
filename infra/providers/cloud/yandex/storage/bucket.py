import logging
import subprocess

from infra.project_setup.types import ProjectSetupContext

logger = logging.getLogger(__name__)

def create_bucket(ctx: 'ProjectSetupContext', bucket_name: str) -> bool:
    """
    Creates a bucket in Yandex Cloud for static files.

    Args:
        ctx: The project setup context.
        bucket_name: The name of the bucket to create.

    Returns:
        bool: True if bucket creation was successful, False otherwise.
    """
    logger.info(f"Creating Yandex Cloud bucket: {bucket_name}")
    create_bucket_cmd = f"yc storage bucket create {bucket_name} --max-size 1073741824"
    try:
        result = subprocess.run(create_bucket_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"Successfully created bucket: {bucket_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create bucket: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while creating bucket: {str(e)}")
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
    check_bucket_cmd = f"yc storage bucket list --format json"
    try:
        result = subprocess.run(check_bucket_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        import json
        buckets = json.loads(result.stdout)
        for bucket in buckets:
            if bucket.get('name') == bucket_name:
                logger.info(f"Bucket {bucket_name} exists.")
                return True
        logger.info(f"Bucket {bucket_name} does not exist.")
        return False
    except Exception as e:
        logger.error(f"Error checking bucket existence: {str(e)}")
        return False