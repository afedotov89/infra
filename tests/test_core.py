"""
Tests for project setup core functionality.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import os
from pathlib import Path

from infra.project_setup.core import (
    _create_database,
    _setup_github_secrets,
    SetupError
)


class TestDatabaseCreation(unittest.TestCase):
    """Test database creation functionality."""

    @patch('infra.providers.git.github.get_repository_secrets')
    @patch('infra.project_setup.core.create_database')
    @patch('infra.config.Config.save_database_info')
    def test_create_database(self, mock_save_info, mock_create_db, mock_get_secrets):
        """Test creating a database when DATABASE_URL secret doesn't exist."""
        # Setup
        mock_get_secrets.return_value = ["OTHER_SECRET"]
        mock_create_db.return_value = {
            "name": "testdb",
            "type": "postgres",
            "host": "test-host.postgresql.yandex.internal",
            "port": 6432,
            "username": "testdb",
            "password": "password",
            "database_url": "postgresql://testdb:password@test-host.postgresql.yandex.internal:6432/testdb"
        }
        mock_log = MagicMock()

        # Call function
        result = _create_database("testproject", "postgres", "testdb", mock_log)

        # Assertions
        self.assertEqual(result, "testdb")
        mock_get_secrets.assert_called_once_with("testproject")
        mock_create_db.assert_called_once_with("testdb", "postgres")
        mock_save_info.assert_called_once()
        mock_log.assert_any_call("🔄 Checking if database needs to be created...")
        mock_log.assert_any_call("🔄 Creating database...")
        mock_log.assert_any_call("✅ Database 'testdb' created")

    @patch('infra.providers.git.github.get_repository_secrets')
    @patch('infra.project_setup.core.create_database')
    @patch('infra.config.Config.save_database_info')
    def test_skip_database_creation_if_secret_exists(self, mock_save_info, mock_create_db, mock_get_secrets):
        """Test skipping database creation when DATABASE_URL secret already exists."""
        # Setup
        mock_get_secrets.return_value = ["DATABASE_URL", "OTHER_SECRET"]
        mock_log = MagicMock()

        # Call function
        result = _create_database("testproject", "postgres", "testdb", mock_log)

        # Assertions
        self.assertEqual(result, "testdb")
        mock_get_secrets.assert_called_once_with("testproject")
        mock_create_db.assert_not_called()
        mock_save_info.assert_not_called()
        mock_log.assert_any_call("🔄 Checking if database needs to be created...")
        mock_log.assert_any_call("ℹ️ DATABASE_URL secret already exists for project testproject")
        mock_log.assert_any_call("   Skipping database creation step to preserve existing configuration")

    @patch('infra.providers.git.github.get_repository_secrets')
    @patch('infra.project_setup.core.create_database')
    def test_handle_database_creation_error(self, mock_create_db, mock_get_secrets):
        """Test error handling during database creation."""
        # Setup
        mock_get_secrets.return_value = ["OTHER_SECRET"]
        mock_create_db.side_effect = Exception("Test database error")
        mock_log = MagicMock()

        # Call function
        result = _create_database("testproject", "postgres", "testdb", mock_log)

        # Assertions
        self.assertEqual(result, "testdb")
        mock_log.assert_any_call("⚠️  Database creation failed: Test database error")
        mock_log.assert_any_call("   Continuing with project setup...")


if __name__ == '__main__':
    unittest.main()