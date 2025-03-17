"""
Tests for database creation and DATABASE_URL generation.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock, call

from infra.providers.cloud.yandex.db.postgres import (
    generate_secure_password,
    create_database_and_user,
    create_database,
    get_yc_configuration,
    YandexCloudDBError
)
from infra.config import Config


class TestPasswordGeneration(unittest.TestCase):
    """Test the password generation functionality."""
    
    def test_generate_secure_password(self):
        """Test that the password generation function creates secure passwords."""
        password = generate_secure_password()
        
        # Check length
        self.assertEqual(len(password), 16, "Password should be 16 characters by default")
        
        # Check custom length
        custom_length = 24
        password = generate_secure_password(custom_length)
        self.assertEqual(len(password), custom_length, f"Password should be {custom_length} characters")
        
        # Check character types
        password = generate_secure_password()
        has_lowercase = any(c.islower() for c in password)
        has_uppercase = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        self.assertTrue(has_lowercase, "Password should contain lowercase letters")
        self.assertTrue(has_uppercase, "Password should contain uppercase letters")
        self.assertTrue(has_digit, "Password should contain digits")
        self.assertTrue(has_special, "Password should contain special characters")


class TestYCDatabaseCreation(unittest.TestCase):
    """Test the database creation functionality using Yandex Cloud CLI."""
    
    @patch('subprocess.check_output')
    @patch('subprocess.check_call')
    @patch('infra.providers.cloud.yandex.db.postgres._get_cluster_host_and_id')
    @patch('infra.providers.cloud.yandex.db.postgres.get_yc_configuration')
    def test_create_database_and_user_both_new(self, mock_get_config, mock_get_host, mock_check_call, mock_check_output):
        """Test creating a database and user when both don't exist."""
        # Setup mocks
        mock_get_config.return_value = {
            "YC_SA_JSON_CREDENTIALS": '{"id":"test-id","service_account_id":"test-sa-id","private_key":"test-key"}',
            "YC_CLOUD_ID": "test_cloud_id",
            "YC_FOLDER_ID": "test_folder_id",
            "YC_POSTGRES_CLUSTER_ID": "test_cluster_id"
        }
        
        mock_get_host.return_value = ("test-host.postgresql.yandex.internal", "test_cluster_id")
        
        # Mock empty lists to indicate no users and databases exist
        mock_check_output.side_effect = [
            json.dumps([]).encode(),  # No users exist
            json.dumps([]).encode()   # No databases exist
        ]
        
        # Call the function
        host, database_url, password = create_database_and_user("testdb")
        
        # Assertions
        self.assertEqual(host, "test-host.postgresql.yandex.internal")
        self.assertTrue(database_url.startswith("postgresql://testdb:"))
        self.assertTrue(database_url.endswith("@test-host.postgresql.yandex.internal:6432/testdb"))
        self.assertTrue(len(password) >= 16)
        
        # Check that subprocess.check_call was called with the right commands for user and database creation
        self.assertEqual(mock_check_call.call_count, 2)
        
        # Get the calls to check_call
        calls = mock_check_call.call_args_list
        
        # First call should be to create user with --cluster-id parameter
        user_cmd = calls[0][0][0]
        self.assertEqual(user_cmd[0], "yc")
        self.assertEqual(user_cmd[1], "managed-postgresql")
        self.assertEqual(user_cmd[2], "user")
        self.assertEqual(user_cmd[3], "create")
        self.assertEqual(user_cmd[4], "testdb")
        self.assertEqual(user_cmd[5], "--cluster-id")
        
        # Second call should be to create database with --cluster-id parameter
        db_cmd = calls[1][0][0]
        self.assertEqual(db_cmd[0], "yc")
        self.assertEqual(db_cmd[1], "managed-postgresql")
        self.assertEqual(db_cmd[2], "database")
        self.assertEqual(db_cmd[3], "create")
        self.assertEqual(db_cmd[4], "testdb")
        self.assertEqual(db_cmd[5], "--cluster-id")
    
    @patch('subprocess.check_output')
    @patch('subprocess.check_call')
    @patch('infra.providers.cloud.yandex.db.postgres._get_cluster_host_and_id')
    @patch('infra.providers.cloud.yandex.db.postgres.get_yc_configuration')
    def test_create_database_and_user_both_exist(self, mock_get_config, mock_get_host, mock_check_call, mock_check_output):
        """Test creating a database and user when both already exist."""
        # Setup mocks
        mock_get_config.return_value = {
            "YC_SA_JSON_CREDENTIALS": '{"id":"test-id","service_account_id":"test-sa-id","private_key":"test-key"}',
            "YC_CLOUD_ID": "test_cloud_id",
            "YC_FOLDER_ID": "test_folder_id",
            "YC_POSTGRES_CLUSTER_ID": "test_cluster_id"
        }
        
        mock_get_host.return_value = ("test-host.postgresql.yandex.internal", "test_cluster_id")
        
        # Mock lists that indicate users and databases exist
        mock_check_output.side_effect = [
            json.dumps([{"name": "testdb"}]).encode(),  # User exists
            json.dumps([{"name": "testdb"}]).encode()   # Database exists
        ]
        
        # Call the function
        host, database_url, password = create_database_and_user("testdb")
        
        # Assertions
        self.assertEqual(host, "test-host.postgresql.yandex.internal")
        self.assertTrue(database_url.startswith("postgresql://testdb:"))
        self.assertTrue(database_url.endswith("@test-host.postgresql.yandex.internal:6432/testdb"))
        self.assertTrue(len(password) >= 16)
        
        # Check that subprocess.check_call was called only for user update
        self.assertEqual(mock_check_call.call_count, 1)
        
        # Get the call to check_call
        call_args = mock_check_call.call_args[0][0]
        
        # Call should be to update user password with --cluster-id parameter
        self.assertEqual(call_args[0], "yc")
        self.assertEqual(call_args[1], "managed-postgresql")
        self.assertEqual(call_args[2], "user")
        self.assertEqual(call_args[3], "update")
        self.assertEqual(call_args[4], "testdb")
        self.assertEqual(call_args[5], "--cluster-id")
    
    @patch('infra.providers.cloud.yandex.db.postgres.create_database_and_user')
    def test_create_database(self, mock_create_db_and_user):
        """Test the high-level database creation function."""
        # Setup mock
        mock_create_db_and_user.return_value = (
            "test-host.postgresql.yandex.internal",
            "postgresql://testdb:password@test-host.postgresql.yandex.internal:6432/testdb",
            "password"
        )
        
        # Call the function
        result = create_database("testdb")
        
        # Assertions
        self.assertEqual(result["name"], "testdb")
        self.assertEqual(result["type"], "postgres")
        self.assertEqual(result["host"], "test-host.postgresql.yandex.internal")
        self.assertEqual(result["port"], 6432)
        self.assertEqual(result["username"], "testdb")
        self.assertEqual(result["password"], "password")
        self.assertEqual(
            result["database_url"], 
            "postgresql://testdb:password@test-host.postgresql.yandex.internal:6432/testdb"
        )

    @patch('infra.config.Config.get_all')
    def test_get_yc_configuration_success(self, mock_get_all):
        """Test getting Yandex Cloud configuration with service account JSON."""
        # Setup mock to return service account JSON
        mock_get_all.return_value = {
            "YC_SA_JSON_CREDENTIALS": '{"id":"test-id","service_account_id":"test-sa-id","private_key":"test-key"}',
            "YC_CLOUD_ID": "test_cloud_id",
            "YC_FOLDER_ID": "test_folder_id",
            "YC_POSTGRES_CLUSTER_ID": "test_cluster_id"
        }
        
        # Call the function
        config = get_yc_configuration()
        
        # Assertions
        self.assertEqual(config["YC_SA_JSON_CREDENTIALS"], '{"id":"test-id","service_account_id":"test-sa-id","private_key":"test-key"}')
        self.assertEqual(config["YC_CLOUD_ID"], "test_cloud_id")
        self.assertEqual(config["YC_FOLDER_ID"], "test_folder_id")
        self.assertEqual(config["YC_POSTGRES_CLUSTER_ID"], "test_cluster_id")

    @patch('infra.config.Config.get_all')
    def test_get_yc_configuration_missing_sa_json(self, mock_get_all):
        """Test getting Yandex Cloud configuration with missing service account JSON."""
        # Setup mock to return config without service account JSON
        mock_get_all.return_value = {
            "YC_CLOUD_ID": "test_cloud_id",
            "YC_FOLDER_ID": "test_folder_id",
            "YC_POSTGRES_CLUSTER_ID": "test_cluster_id"
        }
        
        # Call the function and check for exception
        with self.assertRaises(YandexCloudDBError) as context:
            get_yc_configuration()
        
        # Check exception message
        self.assertTrue("Missing required Yandex Cloud authentication" in str(context.exception))


class TestDatabaseConfig(unittest.TestCase):
    """Test the database configuration functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Clean up any existing test data
        self.test_project_name = "test_project"
        Config._database_info = {}
        
        # Create a test configuration directory
        self.config_dir = os.path.expanduser("~/.infra_test")
        os.makedirs(self.config_dir, exist_ok=True)
        self.db_info_file = os.path.join(self.config_dir, "db_info.json")
        
        # Save original path
        self.original_expand_user = os.path.expanduser
        
        # Mock expanduser to return our test directory
        def mock_expanduser(path):
            if path == "~/.infra":
                return self.config_dir
            return self.original_expand_user(path)
        
        self.expanduser_patcher = patch('os.path.expanduser', side_effect=mock_expanduser)
        self.expanduser_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test file if it exists
        if os.path.exists(self.db_info_file):
            os.remove(self.db_info_file)
        
        # Remove test directory if it exists
        if os.path.exists(self.config_dir):
            os.rmdir(self.config_dir)
        
        # Stop patcher
        self.expanduser_patcher.stop()
    
    def test_save_and_get_database_info(self):
        """Test saving and retrieving database information."""
        # Test data
        db_info = {
            "name": "test_db",
            "type": "postgres",
            "host": "test-host.postgresql.yandex.internal",
            "port": 6432,
            "username": "test_user",
            "password": "test_password",
            "database_url": "postgresql://test_user:test_password@test-host.postgresql.yandex.internal:6432/test_db"
        }
        
        # Save the information
        Config.save_database_info(self.test_project_name, db_info)
        
        # Verify it was saved in memory
        self.assertEqual(Config._database_info[self.test_project_name], db_info)
        
        # Verify it was saved to file
        self.assertTrue(os.path.exists(self.db_info_file))
        with open(self.db_info_file, 'r') as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data[self.test_project_name], db_info)
        
        # Clear the in-memory cache
        Config._database_info = {}
        
        # Retrieve the information
        retrieved_info = Config.get_database_info(self.test_project_name)
        
        # Verify it matches what we saved
        self.assertEqual(retrieved_info, db_info)


if __name__ == '__main__':
    unittest.main() 