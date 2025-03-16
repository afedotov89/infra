"""
Yandex Cloud PostgreSQL database management.
"""

import logging
import time
from typing import Dict, List, Optional

import yandexcloud
from yandex.cloud.mdb.postgresql.v1.cluster_pb2 import Cluster
from yandex.cloud.mdb.postgresql.v1.cluster_service_pb2 import (
    CreateClusterRequest, DeleteClusterRequest, ListClustersRequest
)
from yandex.cloud.mdb.postgresql.v1.cluster_service_pb2_grpc import ClusterServiceStub
from yandex.cloud.mdb.postgresql.v1.database_pb2 import Database
from yandex.cloud.mdb.postgresql.v1.database_service_pb2 import (
    CreateDatabaseRequest, DeleteDatabaseRequest, ListDatabasesRequest
)
from yandex.cloud.mdb.postgresql.v1.database_service_pb2_grpc import DatabaseServiceStub
from yandex.cloud.mdb.postgresql.v1.user_pb2 import User, Permission
from yandex.cloud.mdb.postgresql.v1.user_service_pb2 import (
    CreateUserRequest, DeleteUserRequest, ListUsersRequest
)
from yandex.cloud.mdb.postgresql.v1.user_service_pb2_grpc import UserServiceStub

from infra.config import Config

logger = logging.getLogger(__name__)


class YandexCloudDBError(Exception):
    """Exception raised for Yandex Cloud database errors."""
    pass


def get_yc_sdk() -> yandexcloud.SDK:
    """
    Initialize and return a Yandex Cloud SDK.
    
    Returns:
        yandexcloud.SDK: Initialized SDK
        
    Raises:
        YandexCloudDBError: If authentication fails
    """
    credentials = Config.get_yandex_cloud_credentials()
    
    try:
        # Initialize SDK with OAuth token
        return yandexcloud.SDK(token=credentials["oauth_token"])
    except Exception as e:
        logger.error(f"Failed to initialize Yandex Cloud SDK: {str(e)}")
        raise YandexCloudDBError(f"Yandex Cloud authentication failed: {str(e)}")


def create_database(
    name: str, 
    db_type: str = "postgres", 
    version: str = "13", 
    environment: str = "PRODUCTION",
    tier_type: str = "s2.micro",  # Smallest tier
    disk_size: int = 10,  # GB
    disk_type: str = "network-ssd",
    wait_for_ready: bool = True,
    timeout: int = 600,  # seconds
) -> Cluster:
    """
    Create a PostgreSQL database cluster in Yandex Cloud.
    
    Args:
        name: Database cluster name
        db_type: Database type (postgres)
        version: PostgreSQL version
        environment: PRODUCTION or PRESTABLE
        tier_type: Resource tier (s2.micro, etc.)
        disk_size: Disk size in GB
        disk_type: Type of disk (network-ssd, etc.)
        wait_for_ready: Whether to wait for the cluster to be ready
        timeout: Timeout in seconds for waiting
        
    Returns:
        Cluster: The created database cluster
        
    Raises:
        YandexCloudDBError: If cluster creation fails
    """
    if db_type.lower() != "postgres":
        raise YandexCloudDBError(f"Unsupported database type: {db_type}, only 'postgres' is currently supported")
    
    sdk = get_yc_sdk()
    cloud_config = Config.get_yandex_cloud_credentials()
    db_credentials = Config.get_db_credentials()
    folder_id = cloud_config["folder_id"]
    
    # Get the cluster service
    cluster_service = sdk.client(ClusterServiceStub)
    
    try:
        logger.info(f"Creating PostgreSQL cluster: {name}")
        
        # Check if cluster already exists
        existing_clusters = list_databases()
        for cluster in existing_clusters:
            if cluster.name == name:
                logger.info(f"Cluster {name} already exists with ID {cluster.id}")
                return cluster
        
        # Create cluster request
        request = CreateClusterRequest(
            folder_id=folder_id,
            name=name,
            description=f"PostgreSQL cluster for {name}",
            environment=environment,
            config_spec={
                "version": version,
                "postgresql_config": {
                    # PostgreSQL specific configurations can be added here
                    "max_connections": 100,
                },
                "resources": {
                    "resource_preset_id": tier_type,
                    "disk_size": disk_size * 2**30,  # Convert to bytes
                    "disk_type_id": disk_type,
                },
                "access": {
                    "data_lens": False,
                    "web_sql": True,
                },
            },
            database_specs=[
                {
                    "name": name,
                    "owner": "admin",  # Will be created in user_specs
                }
            ],
            user_specs=[
                {
                    "name": "admin",
                    "password": db_credentials["password"],
                    "permissions": [
                        {
                            "database_name": name,
                        }
                    ],
                    "conn_limit": 50,
                }
            ],
            host_specs=[
                {
                    "zone_id": "ru-central1-a",
                    "subnet_id": "",  # Would need to be specified in real implementation
                }
            ],
            network_id="",  # Would need to be specified in real implementation
        )
        
        # Send the request
        operation = cluster_service.Create(request)
        
        # Wait for the operation to complete if requested
        if wait_for_ready:
            logger.info(f"Waiting for cluster creation (up to {timeout} seconds)...")
            
            start_time = time.time()
            while not operation.done:
                if time.time() - start_time > timeout:
                    raise YandexCloudDBError(f"Timeout waiting for cluster creation after {timeout} seconds")
                
                time.sleep(5)
                operation = sdk.wait_operation_and_get_result(
                    operation_id=operation.id,
                    timeout=min(5, timeout - (time.time() - start_time))
                )
            
            # Get the created cluster
            cluster_id = operation.response.id
            cluster = cluster_service.Get(id=cluster_id)
            logger.info(f"PostgreSQL cluster created successfully with ID: {cluster_id}")
            return cluster
        else:
            logger.info(f"PostgreSQL cluster creation initiated, operation ID: {operation.id}")
            # Return a placeholder since we don't have the actual cluster yet
            return Cluster(id=operation.id, name=name, status="CREATING")
            
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL cluster: {str(e)}")
        raise YandexCloudDBError(f"Failed to create PostgreSQL cluster: {str(e)}")


def delete_database(name: str) -> None:
    """
    Delete a PostgreSQL database cluster in Yandex Cloud.
    
    Args:
        name: Cluster name
        
    Raises:
        YandexCloudDBError: If cluster deletion fails
    """
    sdk = get_yc_sdk()
    cluster_service = sdk.client(ClusterServiceStub)
    
    try:
        logger.info(f"Deleting PostgreSQL cluster: {name}")
        
        # Find the cluster by name
        existing_clusters = list_databases()
        target_cluster = None
        
        for cluster in existing_clusters:
            if cluster.name == name:
                target_cluster = cluster
                break
                
        if not target_cluster:
            logger.warning(f"Cluster {name} does not exist, nothing to delete")
            return
            
        # Delete the cluster
        request = DeleteClusterRequest(cluster_id=target_cluster.id)
        operation = cluster_service.Delete(request)
        
        logger.info(f"PostgreSQL cluster deletion initiated, operation ID: {operation.id}")
            
    except Exception as e:
        logger.error(f"Failed to delete PostgreSQL cluster: {str(e)}")
        raise YandexCloudDBError(f"Failed to delete PostgreSQL cluster: {str(e)}")


def list_databases() -> List[Cluster]:
    """
    List PostgreSQL database clusters in Yandex Cloud.
    
    Returns:
        List[Cluster]: List of database clusters
        
    Raises:
        YandexCloudDBError: If listing clusters fails
    """
    sdk = get_yc_sdk()
    cloud_config = Config.get_yandex_cloud_credentials()
    folder_id = cloud_config["folder_id"]
    cluster_service = sdk.client(ClusterServiceStub)
    
    try:
        logger.info("Listing PostgreSQL clusters")
        
        request = ListClustersRequest(folder_id=folder_id)
        response = cluster_service.List(request)
        
        return list(response.clusters)
            
    except Exception as e:
        logger.error(f"Failed to list PostgreSQL clusters: {str(e)}")
        raise YandexCloudDBError(f"Failed to list PostgreSQL clusters: {str(e)}") 